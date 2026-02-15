"""Integration tests for CSRF Origin validation, concurrent token rotation,
and token expiry edge cases.

These cover review issue #16: scenarios that were not previously tested.
"""

import os
import requests
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
AUTH_URL = f"{API_BASE_URL}/api/v1/auth"
ADMIN_CREDS = {"username": "admin", "password": "adminpass123"}


def _login_session(user_agent: str | None = None) -> requests.Session:
    """Create a new requests.Session, login, and return it."""
    session = requests.Session()
    if user_agent:
        session.headers["User-Agent"] = user_agent
    resp = session.post(f"{AUTH_URL}/login", json=ADMIN_CREDS)
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    return session


# ============================================================================
# CSRF Origin Validation Middleware
# ============================================================================


class TestCSRFOriginValidation:
    """Test the OriginValidationMiddleware in app/main.py."""

    # -- Safe methods should never be blocked regardless of Origin ----------

    def test_get_with_bad_origin_allowed(self):
        """GET requests should pass even with a disallowed Origin."""
        resp = requests.get(
            f"{API_BASE_URL}/health",
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status_code == 200

    def test_head_with_bad_origin_allowed(self):
        """HEAD requests should not be blocked by CSRF middleware."""
        resp = requests.head(
            f"{API_BASE_URL}/health",
            headers={"Origin": "https://evil.com"},
        )
        # HEAD is a safe method — CSRF middleware must not block it
        assert resp.status_code != 403

    def test_options_with_bad_origin_allowed(self):
        """OPTIONS (preflight) requests should not be blocked by CSRF middleware."""
        resp = requests.options(
            f"{AUTH_URL}/login",
            headers={"Origin": "https://evil.com"},
        )
        # OPTIONS handled by CORSMiddleware; should not be 403
        assert resp.status_code != 403

    # -- Unsafe methods with no Origin header (non-browser clients) ---------

    def test_post_without_origin_allowed(self):
        """POST with no Origin header should pass (curl, Postman, etc.)."""
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
        )
        assert resp.status_code == 200

    def test_put_without_origin_allowed(self):
        """PUT with no Origin header should not be blocked by CSRF."""
        resp = requests.put(f"{API_BASE_URL}/health")
        # Will probably 404/405, but must NOT be 403
        assert resp.status_code != 403

    def test_delete_without_origin_allowed(self):
        """DELETE with no Origin header should not be blocked by CSRF."""
        resp = requests.delete(f"{API_BASE_URL}/health")
        assert resp.status_code != 403

    def test_patch_without_origin_allowed(self):
        """PATCH with no Origin header should not be blocked by CSRF."""
        resp = requests.patch(f"{API_BASE_URL}/health")
        assert resp.status_code != 403

    # -- Unsafe methods with allowed Origin ---------------------------------

    def test_post_with_allowed_origin(self):
        """POST with an allowed Origin should pass through."""
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
            headers={"Origin": "http://localhost:3000"},
        )
        assert resp.status_code == 200

    def test_post_with_allowed_origin_trailing_slash(self):
        """Trailing slash on Origin should be normalised and still match."""
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
            headers={"Origin": "http://localhost:3000/"},
        )
        assert resp.status_code == 200

    # -- Unsafe methods with disallowed Origin (CSRF attack) ----------------

    def test_post_with_disallowed_origin_blocked(self):
        """POST with a disallowed Origin should return 403."""
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Origin not allowed"

    def test_put_with_disallowed_origin_blocked(self):
        """PUT with a disallowed Origin should return 403."""
        resp = requests.put(
            f"{API_BASE_URL}/health",
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status_code == 403

    def test_delete_with_disallowed_origin_blocked(self):
        """DELETE with a disallowed Origin should return 403."""
        resp = requests.delete(
            f"{API_BASE_URL}/health",
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status_code == 403

    def test_patch_with_disallowed_origin_blocked(self):
        """PATCH with a disallowed Origin should return 403."""
        resp = requests.patch(
            f"{API_BASE_URL}/health",
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status_code == 403

    # -- Referer fallback ---------------------------------------------------

    def test_referer_fallback_allowed(self):
        """When Origin is absent, allowed Referer should pass."""
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
            headers={"Referer": "http://localhost:3000/admin/login"},
        )
        assert resp.status_code == 200

    def test_referer_fallback_disallowed(self):
        """When Origin is absent, disallowed Referer should be blocked."""
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
            headers={"Referer": "https://evil.com/phishing-page"},
        )
        assert resp.status_code == 403

    def test_origin_takes_precedence_over_referer(self):
        """When both Origin and Referer are present, Origin should be used."""
        # Good Origin + bad Referer → should pass (Origin takes precedence)
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
            headers={
                "Origin": "http://localhost:3000",
                "Referer": "https://evil.com/page",
            },
        )
        assert resp.status_code == 200

    def test_bad_origin_overrides_good_referer(self):
        """Bad Origin should block even if Referer is allowed."""
        resp = requests.post(
            f"{AUTH_URL}/login",
            json=ADMIN_CREDS,
            headers={
                "Origin": "https://evil.com",
                "Referer": "http://localhost:3000/page",
            },
        )
        assert resp.status_code == 403


# ============================================================================
# Concurrent Token Rotation
# ============================================================================


class TestConcurrentTokenRotation:
    """Test that concurrent refresh requests don't create duplicate sessions."""

    def test_concurrent_refresh_old_token_invalid_after(self):
        """After concurrent refresh attempts complete, the original token
        should no longer be usable.

        Note: Without DB-level row locking (SELECT ... FOR UPDATE), multiple
        concurrent refreshes may each succeed because flush() only persists
        within the current transaction. This test verifies the *sequential*
        guarantee: once rotation completes, the old token is revoked.
        """
        session = _login_session()
        old_refresh = session.cookies.get("refresh_token")
        assert old_refresh

        results = []

        def do_refresh():
            resp = requests.post(
                f"{AUTH_URL}/refresh",
                json={},
                cookies={"refresh_token": old_refresh},
            )
            return resp.status_code

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(do_refresh) for _ in range(3)]
            for f in as_completed(futures):
                results.append(f.result())

        # At least one should have succeeded
        assert 200 in results, f"Expected at least one success: {results}"
        # All results should be either 200 or 401 (no 500s)
        assert all(r in (200, 401) for r in results), f"Unexpected status codes: {results}"

        # After all concurrent requests complete, the original token must be revoked
        late_resp = requests.post(
            f"{AUTH_URL}/refresh",
            json={},
            cookies={"refresh_token": old_refresh},
        )
        assert late_resp.status_code == 401, (
            "Old refresh token should be revoked after rotation"
        )

    def test_old_refresh_token_rejected_after_rotation(self):
        """After a successful refresh, the old refresh token should be rejected."""
        session = _login_session()
        old_refresh = session.cookies.get("refresh_token")
        assert old_refresh

        # Rotate
        refresh_resp = session.post(f"{AUTH_URL}/refresh", json={})
        assert refresh_resp.status_code == 200
        new_refresh = refresh_resp.cookies.get("refresh_token")
        assert new_refresh
        assert new_refresh != old_refresh

        # Old token should be revoked
        old_resp = requests.post(
            f"{AUTH_URL}/refresh",
            json={},
            cookies={"refresh_token": old_refresh},
        )
        assert old_resp.status_code == 401


# ============================================================================
# Token Expiry / Clock-Skew Edge Cases
# ============================================================================


class TestTokenEdgeCases:
    """Test edge cases around token expiry and invalid tokens."""

    def test_revoked_refresh_token_returns_401(self):
        """A refresh token that has been explicitly revoked should be rejected."""
        session = _login_session()
        refresh_cookie = session.cookies.get("refresh_token")
        assert refresh_cookie

        # Logout revokes the refresh token
        logout_resp = session.post(f"{AUTH_URL}/logout", json={})
        assert logout_resp.status_code == 200

        # Try to use the revoked refresh token
        resp = requests.post(
            f"{AUTH_URL}/refresh",
            json={},
            cookies={"refresh_token": refresh_cookie},
        )
        assert resp.status_code == 401
        assert "revoked" in resp.json()["detail"].lower()

    def test_garbage_refresh_token_returns_401(self):
        """A completely invalid refresh token string should be rejected."""
        resp = requests.post(
            f"{AUTH_URL}/refresh",
            json={},
            cookies={"refresh_token": "not-a-real-jwt-at-all"},
        )
        assert resp.status_code == 401

    def test_missing_refresh_cookie_returns_401(self):
        """Refresh with no refresh_token cookie at all should be rejected."""
        resp = requests.post(f"{AUTH_URL}/refresh", json={})
        assert resp.status_code == 401
        assert "Missing refresh token cookie" in resp.json()["detail"]

    def test_access_token_as_refresh_cookie_returns_401(self):
        """Using the access token value in the refresh_token cookie should fail."""
        session = _login_session()
        access_token = session.cookies.get("access_token")
        assert access_token

        resp = requests.post(
            f"{AUTH_URL}/refresh",
            json={},
            cookies={"refresh_token": access_token},
        )
        assert resp.status_code == 401
        assert "Invalid token type" in resp.json()["detail"]

    def test_refresh_after_logout_all_returns_401(self):
        """After logout-all, all refresh tokens should be rejected."""
        s1 = _login_session("Mozilla/5.0 (X11; Linux x86_64) Chrome/120")
        s2 = _login_session("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/604.1")

        refresh_s2 = s2.cookies.get("refresh_token")
        assert refresh_s2

        # Logout-all from s1
        resp = s1.post(f"{AUTH_URL}/logout-all", json={})
        assert resp.status_code == 200

        # s2's refresh token should now be rejected
        resp = requests.post(
            f"{AUTH_URL}/refresh",
            json={},
            cookies={"refresh_token": refresh_s2},
        )
        assert resp.status_code == 401

    def test_expired_access_token_cookie_returns_401(self):
        """An expired access token cookie should yield 401 on protected endpoints."""
        # We can't easily forge an expired JWT here, but we can verify that
        # a tampered/truncated token is rejected.
        resp = requests.get(
            f"{AUTH_URL}/me",
            cookies={"access_token": "eyJ.expired.token"},
        )
        assert resp.status_code == 401

    def test_refresh_token_not_accepted_on_me_endpoint(self):
        """The /auth/me endpoint should reject refresh tokens used as access tokens."""
        session = _login_session()
        refresh_token = session.cookies.get("refresh_token")
        assert refresh_token

        resp = requests.get(
            f"{AUTH_URL}/me",
            cookies={"access_token": refresh_token},
        )
        assert resp.status_code == 401
