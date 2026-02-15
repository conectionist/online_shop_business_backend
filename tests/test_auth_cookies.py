"""Unit tests for auth cookie helper utilities."""

from fastapi import Response

from app.core import auth_cookies
from app.core.config import settings


def test_access_cookie_params_default_env():
    params = auth_cookies.get_access_cookie_params()

    assert params["httponly"] is True
    assert params["secure"] == settings.COOKIE_SECURE
    assert params["samesite"] == settings.COOKIE_SAMESITE
    assert params["path"] == settings.COOKIE_PATH
    assert params["max_age"] == settings.ACCESS_TOKEN_COOKIE_MAX_AGE

    if settings.COOKIE_DOMAIN:
        assert params["domain"] == settings.COOKIE_DOMAIN
    else:
        assert "domain" not in params


def test_refresh_cookie_params_default_env():
    params = auth_cookies.get_refresh_cookie_params()

    assert params["httponly"] is True
    assert params["secure"] == settings.COOKIE_SECURE
    assert params["samesite"] == settings.COOKIE_SAMESITE
    assert params["path"] == settings.COOKIE_PATH
    assert params["max_age"] == settings.REFRESH_TOKEN_COOKIE_MAX_AGE

    if settings.COOKIE_DOMAIN:
        assert params["domain"] == settings.COOKIE_DOMAIN
    else:
        assert "domain" not in params


def test_set_auth_cookies_sets_both_cookies():
    response = Response()

    access_value = "access-token-value"
    refresh_value = "refresh-token-value"

    auth_cookies.set_auth_cookies(response, access_value, refresh_value)

    # Response headers should contain two Set-Cookie entries
    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2

    # Ensure both cookie names are present
    combined = " ".join(set_cookie_headers)
    assert f"{auth_cookies.ACCESS_TOKEN_COOKIE_NAME}=" in combined
    assert f"{auth_cookies.REFRESH_TOKEN_COOKIE_NAME}=" in combined


def test_clear_auth_cookies_clears_both_cookies():
    response = Response()

    auth_cookies.clear_auth_cookies(response)

    # Response headers should contain two Set-Cookie entries with max-age=0
    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2

    for header in set_cookie_headers:
        assert "Max-Age=0" in header or "max-age=0" in header
        assert (
            auth_cookies.ACCESS_TOKEN_COOKIE_NAME in header
            or auth_cookies.REFRESH_TOKEN_COOKIE_NAME in header
        )

