import os
import requests
import pytest
import time
import uuid
from typing import Dict, Any


class AuthTestUtils:
    """Test utilities for the Authentication API."""
    
    def __init__(self):
        """Initialize with the Authentication endpoint."""
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_v1_str = "/api/v1"
        self.auth_base_url = f"{self.api_base_url}{self.api_v1_str}/auth"
        # Use a session to track cookies across requests
        self.session = requests.Session()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with username and password.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Login response data
        """
        response = self.session.post(
            f"{self.auth_base_url}/login",
            json={"username": username, "password": password}
        )
        return response
    
    def refresh_token(self) -> requests.Response:
        """Refresh the access token using the refresh_token httpOnly cookie."""
        return self.session.post(
            f"{self.auth_base_url}/refresh",
            json={},
        )
    
    def create_admin(self, access_token: str, username: str, password: str) -> requests.Response:
        """
        Create a new admin user (requires authentication).
        
        Args:
            access_token: JWT access token
            username: New admin username
            password: New admin password
            
        Returns:
            Create admin response
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{self.auth_base_url}/create-admin",
            json={"username": username, "password": password},
            headers=headers
        )
        return response
    
    def generate_unique_username(self, prefix: str = "testadmin") -> str:
        """Generate a unique username for testing."""
        short_uuid = str(uuid.uuid4())[:8]
        return f"{prefix}_{short_uuid}"
    
    def change_password(self, current_password: str, new_password: str) -> requests.Response:
        """
        Change the current admin's password.
        
        Args:
            current_password: Current password
            new_password: New password
            
        Returns:
            Password change response
        """
        response = self.session.post(
            f"{self.auth_base_url}/change-password",
            json={"current_password": current_password, "new_password": new_password}
        )
        return response


# Test utility instance
auth_utils = AuthTestUtils()


class TestAuthLogin:
    """Test login functionality."""
    
    def test_login_success(self):
        """Test successful login with default admin credentials."""
        response = auth_utils.login("admin", "adminpass123")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Response JSON should no longer contain raw tokens
        data = response.json()
        assert "access_token" not in data
        assert "refresh_token" not in data
        assert "token_type" not in data
        assert "expires_in" in data
        assert "admin" in data
        assert data["admin"]["username"] == "admin"
        assert "id" in data["admin"]

        # Tokens should be delivered via cookies instead
        set_cookie_headers = response.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie_headers, "Expected access_token cookie to be set on login"
        assert "refresh_token=" in set_cookie_headers, "Expected refresh_token cookie to be set on login"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = auth_utils.login("admin", "wrongpassword")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid username or password" in data["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        response = auth_utils.login("nonexistent", "password")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid username or password" in data["detail"]
    
    def test_login_empty_credentials(self):
        """Test login with empty credentials."""
        response = auth_utils.login("", "")
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    
    def test_login_missing_fields(self):
        """Test login with missing fields."""
        response = requests.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin"}  # Missing password
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"


class TestAuthRefresh:
    """Test token refresh functionality."""
    
    def test_refresh_success(self):
        """Test successful token refresh."""
        # Use a session to simulate browser behavior: login sets cookies, then
        # refresh uses the refresh_token cookie only.
        session = requests.Session()

        login_response = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"}
        )
        assert login_response.status_code == 200, f"Expected 200 on login, got {login_response.status_code}: {login_response.text}"
        # Ensure refresh_token cookie is present after login
        assert "refresh_token" in login_response.cookies, "Expected refresh_token cookie after login"

        # Refresh the token using the cookie-based flow
        refresh_response = session.post(
            f"{auth_utils.auth_base_url}/refresh",
            json={}
        )
        
        assert refresh_response.status_code == 200, f"Expected 200, got {refresh_response.status_code}: {refresh_response.text}"
        
        data = refresh_response.json()
        # Response body should no longer expose raw tokens
        assert "access_token" not in data
        assert "token_type" not in data
        assert "refresh_token" not in data
        assert "expires_in" in data

        # New access token must be set via cookies
        set_cookie_headers = refresh_response.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie_headers, "Expected access_token cookie to be set on refresh"

    def test_refresh_rotates_refresh_token(self):
        """Refresh should rotate refresh_token (old refresh token becomes revoked)."""
        session = requests.Session()

        login_response = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"}
        )
        assert login_response.status_code == 200
        old_refresh = login_response.cookies.get("refresh_token")
        assert old_refresh

        refresh_response = session.post(
            f"{auth_utils.auth_base_url}/refresh",
            json={}
        )
        assert refresh_response.status_code == 200
        new_refresh = refresh_response.cookies.get("refresh_token")
        assert new_refresh
        assert new_refresh != old_refresh
    
    def test_refresh_invalid_token(self):
        """Test refresh with invalid token."""
        # Simulate an invalid refresh token cookie
        response = requests.post(
            f"{auth_utils.auth_base_url}/refresh",
            json={},
            cookies={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid refresh token" in data["detail"]
    
    def test_refresh_access_token_as_refresh(self):
        """Test using access token as refresh token (should fail)."""
        # First login to get a valid access token cookie
        session = requests.Session()
        login_response = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"}
        )
        assert login_response.status_code == 200

        access_token_cookie = login_response.cookies.get("access_token")
        assert access_token_cookie, "Expected access_token cookie after login"

        # Try to use access token value as the refresh token cookie
        response = requests.post(
            f"{auth_utils.auth_base_url}/refresh",
            json={},
            cookies={"refresh_token": access_token_cookie}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid token type" in data["detail"]

    def test_refresh_token_rejected_on_admin_endpoint(self):
        """Refresh token must not be accepted as admin auth; only access tokens work on admin endpoints."""
        # Login to obtain a refresh token cookie, then misuse it as an
        # Authorization header on an admin-only endpoint.
        session = requests.Session()
        login_response = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"}
        )
        assert login_response.status_code == 200
        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token, "Expected refresh_token cookie after login"
        # Use an admin-only endpoint (list orders requires get_current_admin)
        orders_url = f"{auth_utils.api_base_url}{auth_utils.api_v1_str}/orders/"
        response = requests.get(
            orders_url,
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response.status_code == 401, f"Expected 401 when using refresh token on admin endpoint, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]


class TestAuthMe:
    """Test /auth/me session check endpoint."""

    def test_me_returns_current_admin_with_valid_cookie(self):
        session = requests.Session()

        login_resp = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert login_resp.status_code == 200, f"Expected 200 on login, got {login_resp.status_code}: {login_resp.text}"
        assert "access_token" in login_resp.cookies, "Expected access_token cookie after login"

        me_resp = session.get(f"{auth_utils.auth_base_url}/me")
        assert me_resp.status_code == 200, f"Expected 200, got {me_resp.status_code}: {me_resp.text}"
        data = me_resp.json()
        assert data["id"] > 0
        assert data["username"] == "admin"

    def test_me_without_cookie_returns_401(self):
        resp = requests.get(f"{auth_utils.auth_base_url}/me")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_me_with_invalid_token_returns_401(self):
        resp = requests.get(
            f"{auth_utils.auth_base_url}/me",
            cookies={"access_token": "invalid"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detail" in data


class TestAuthLogout:
    """Test logout functionality."""

    def test_logout_success(self):
        session = requests.Session()

        login_resp = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert login_resp.status_code == 200

        logout_resp = session.post(f"{auth_utils.auth_base_url}/logout", json={})
        assert logout_resp.status_code == 200, f"Expected 200, got {logout_resp.status_code}: {logout_resp.text}"

        set_cookie_headers = logout_resp.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie_headers
        assert "refresh_token=" in set_cookie_headers
        assert "Max-Age=0" in set_cookie_headers or "max-age=0" in set_cookie_headers

    def test_logout_revokes_refresh_token(self):
        """After logout, the previous refresh token should be rejected as revoked."""
        session = requests.Session()

        login_resp = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert login_resp.status_code == 200
        old_refresh = login_resp.cookies.get("refresh_token")
        assert old_refresh

        logout_resp = session.post(f"{auth_utils.auth_base_url}/logout", json={})
        assert logout_resp.status_code == 200

        refresh_resp = requests.post(
            f"{auth_utils.auth_base_url}/refresh",
            json={},
            cookies={"refresh_token": old_refresh},
        )
        assert refresh_resp.status_code == 401

        detail = refresh_resp.json().get("detail", "")
        assert "revoked" in detail.lower() or "invalid" in detail.lower()


class TestAuthLogoutAll:
    """Test logout-all (global logout) functionality."""

    def test_logout_all_revokes_other_sessions(self):
        """Logout-all should revoke refresh tokens from other sessions/devices."""
        session1 = requests.Session()
        session2 = requests.Session()

        r1 = session1.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert r1.status_code == 200

        r2 = session2.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert r2.status_code == 200
        refresh2 = r2.cookies.get("refresh_token")
        assert refresh2

        logout_all_resp = session1.post(f"{auth_utils.auth_base_url}/logout-all", json={})
        assert logout_all_resp.status_code == 200

        refresh_resp = requests.post(
            f"{auth_utils.auth_base_url}/refresh",
            json={},
            cookies={"refresh_token": refresh2},
        )
        assert refresh_resp.status_code == 401

        detail = refresh_resp.json().get("detail", "")
        assert "revoked" in detail.lower() or "invalid" in detail.lower()


class TestAuthLogoutOthers:
    """Test logout-others (log out all devices except current) functionality."""

    def test_logout_others_revokes_other_sessions(self):
        """Logout-others should revoke other sessions but keep the current one alive."""
        session1 = requests.Session()
        session2 = requests.Session()

        r1 = session1.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert r1.status_code == 200

        r2 = session2.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert r2.status_code == 200
        refresh2 = r2.cookies.get("refresh_token")
        assert refresh2

        # Logout others from session 1
        resp = session1.post(f"{auth_utils.auth_base_url}/logout-others", json={})
        assert resp.status_code == 200

        # Session 2 should be revoked
        refresh_resp = requests.post(
            f"{auth_utils.auth_base_url}/refresh",
            json={},
            cookies={"refresh_token": refresh2},
        )
        assert refresh_resp.status_code == 401

        # Session 1 should still work
        me_resp = session1.get(f"{auth_utils.auth_base_url}/me")
        assert me_resp.status_code == 200

    def test_logout_others_keeps_current_session(self):
        """After logout-others, the current session's cookies should remain valid."""
        session = requests.Session()

        login_resp = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert login_resp.status_code == 200

        resp = session.post(f"{auth_utils.auth_base_url}/logout-others", json={})
        assert resp.status_code == 200

        # Current session should still be able to access protected endpoints
        me_resp = session.get(f"{auth_utils.auth_base_url}/me")
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "admin"

    def test_logout_others_no_other_sessions(self):
        """Logout-others with only one active session should succeed with 0 revoked."""
        session = requests.Session()

        # Login and immediately clear all sessions to start clean
        login_resp = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert login_resp.status_code == 200
        session.post(f"{auth_utils.auth_base_url}/logout-all", json={})

        # Login again — now this is the only session
        login_resp = session.post(
            f"{auth_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
        )
        assert login_resp.status_code == 200

        resp = session.post(f"{auth_utils.auth_base_url}/logout-others", json={})
        assert resp.status_code == 200
        assert "0 other device" in resp.json()["message"]


# class TestAuthCreateAdmin:
#     """Test admin creation functionality."""
#     
#     def test_create_admin_success(self):
#         """Test successful admin creation by authenticated admin."""
#         # First login to get access token
#         login_response = auth_utils.login("admin", "adminpass123")
#         assert login_response.status_code == 200
#         
#         login_data = login_response.json()
#         access_token = login_data["access_token"]
#         
#         # Create new admin with unique username
#         unique_username = auth_utils.generate_unique_username("testadmin")
#         response = auth_utils.create_admin(access_token, unique_username, "testpass123456")
#         
#         assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
#         
#         data = response.json()
#         assert "id" in data
#         assert "username" in data
#         assert data["username"] == unique_username
#         assert data["id"] > 0
#     
#     def test_create_admin_unauthorized(self):
#         """Test admin creation without authentication."""
#         response = auth_utils.create_admin("invalid_token", "testadmin", "testpass123")
#         
#         assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
#         
#         data = response.json()
#         assert "detail" in data
#         assert "Invalid authentication token" in data["detail"]
#     
#     def test_create_admin_duplicate_username(self):
#         """Test creating admin with duplicate username."""
#         # First login to get access token
#         login_response = auth_utils.login("admin", "adminpass123")
#         assert login_response.status_code == 200
#         
#         login_data = login_response.json()
#         access_token = login_data["access_token"]
#         
#         # Create first admin with unique username
#         unique_username = auth_utils.generate_unique_username("duplicateadmin")
#         response1 = auth_utils.create_admin(access_token, unique_username, "pass123456")
#         assert response1.status_code == 201
#         
#         # Try to create second admin with same username
#         response2 = auth_utils.create_admin(access_token, unique_username, "pass456789")
#         
#         assert response2.status_code == 409, f"Expected 409, got {response2.status_code}: {response2.text}"
#         
#         data = response2.json()
#         assert "detail" in data
#         assert "already exists" in data["detail"]
#     
#     def test_create_admin_invalid_data(self):
#         """Test admin creation with invalid data."""
#         # First login to get access token
#         login_response = auth_utils.login("admin", "adminpass123")
#         assert login_response.status_code == 200
#         
#         login_data = login_response.json()
#         access_token = login_data["access_token"]
#         
#         # Try to create admin with empty username
#         response = requests.post(
#             f"{auth_utils.auth_base_url}/create-admin",
#             json={"username": "", "password": "pass123456"},
#             headers={"Authorization": f"Bearer {access_token}"}
#         )
#         
#         assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
#     
#     def test_create_admin_missing_fields(self):
#         """Test admin creation with missing fields."""
#         # First login to get access token
#         login_response = auth_utils.login("admin", "adminpass123")
#         assert login_response.status_code == 200
#         
#         login_data = login_response.json()
#         access_token = login_data["access_token"]
#         
#         # Try to create admin with missing password
#         response = requests.post(
#             f"{auth_utils.auth_base_url}/create-admin",
#             json={"username": "testadmin"},
#             headers={"Authorization": f"Bearer {access_token}"}
#         )
#         
#         assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"


class TestAuthChangePassword:
    """Test password change functionality."""
    
    def test_change_password_success(self):
        """Test successful password change."""
        # First login to get access token
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200

        # Protected endpoints are still header-based until Step 6, so extract
        # the access token from the cookie and send it as a Bearer token.
        access_token = login_response.cookies.get("access_token")
        assert access_token, "Expected access_token cookie after login"
        
        # Change password
        response = auth_utils.change_password("adminpass123", "newpass123")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "Password changed successfully" in data["message"]
        
        # Verify old password no longer works
        old_login_response = auth_utils.login("admin", "adminpass123")
        assert old_login_response.status_code == 401
        
        # Verify new password works
        new_login_response = auth_utils.login("admin", "newpass123")
        assert new_login_response.status_code == 200
        
        # Change password back for other tests
        new_access_token = new_login_response.cookies.get("access_token")
        assert new_access_token, "Expected access_token cookie after login"
        revert_response = auth_utils.change_password("newpass123", "adminpass123")
        assert revert_response.status_code == 200
    
    def test_change_password_unauthorized(self):
        """Test password change without authentication."""
        # Clear session cookies to ensure no authentication
        auth_utils.session.cookies.clear()
        
        response = auth_utils.change_password("oldpass", "newpass")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]
    
    def test_change_password_wrong_current_password(self):
        """Test password change with wrong current password."""
        # First login to get access token
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200

        access_token = login_response.cookies.get("access_token")
        assert access_token, "Expected access_token cookie after login"
        
        # Try to change password with wrong current password
        response = auth_utils.change_password("wrongpass", "newpass123")
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid current password" in data["detail"]
    
    def test_change_password_invalid_data(self):
        """Test password change with invalid data."""
        # First login to get access token
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200

        access_token = login_response.cookies.get("access_token")
        assert access_token, "Expected access_token cookie after login"
        
        session = requests.Session()
        session.cookies.set("access_token", access_token)
        
        # Try to change password with short new password
        response = session.post(
            f"{auth_utils.auth_base_url}/change-password",
            json={"current_password": "adminpass123", "new_password": "123"},
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    
    def test_change_password_missing_fields(self):
        """Test password change with missing fields."""
        # First login to get access token
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200

        access_token = login_response.cookies.get("access_token")
        assert access_token, "Expected access_token cookie after login"
        
        # Try to change password with missing new_password
        response = auth_utils.session.post(
            f"{auth_utils.auth_base_url}/change-password",
            json={"current_password": "adminpass123"}
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"


class TestAuthEndToEnd:
    """Test end-to-end authentication workflows."""
    
    # def test_complete_admin_workflow(self):
    #     """Test complete workflow: login, create admin, login as new admin, change password."""
    #     # 1. Login as default admin
    #     login_response = auth_utils.login("admin", "adminpass123")
    #     assert login_response.status_code == 200
    #     
    #     login_data = login_response.json()
    #     access_token = login_data["access_token"]
    #     
    #     # 2. Create new admin with unique username
    #     unique_username = auth_utils.generate_unique_username("workflowadmin")
    #     create_response = auth_utils.create_admin(access_token, unique_username, "workflowpass123456")
    #     assert create_response.status_code == 201
    #     
    #     create_data = create_response.json()
    #     new_admin_id = create_data["id"]
    #     assert create_data["username"] == unique_username
    #     
    #     # 3. Login as new admin
    #     new_login_response = auth_utils.login(unique_username, "workflowpass123456")
    #     assert new_login_response.status_code == 200
    #     
    #     new_login_data = new_login_response.json()
    #     new_access_token = new_login_data["access_token"]
    #     new_refresh_token = new_login_data["refresh_token"]
    #     
    #     # 4. Change password as new admin
    #     change_response = auth_utils.change_password(new_access_token, "workflowpass123456", "newworkflowpass123456")
    #     assert change_response.status_code == 200
    #     
    #     # 5. Verify old password no longer works
    #     old_login_response = auth_utils.login(unique_username, "workflowpass123456")
    #     assert old_login_response.status_code == 401
    #     
    #     # 6. Verify new password works
    #     new_login_response2 = auth_utils.login(unique_username, "newworkflowpass123456")
    #     assert new_login_response2.status_code == 200
    #     
    #     # 7. Test refresh token with new admin
    #     refresh_response = auth_utils.refresh_token(new_refresh_token)
    #     assert refresh_response.status_code == 200
    #     
    #     refresh_data = refresh_response.json()
    #     assert "access_token" in refresh_data
    
    # def test_token_expiration_handling(self):
    #     """Test that expired tokens are properly handled."""
    #     # This test would require manipulating token expiration times
    #     # For now, we'll test that valid tokens work and invalid tokens don't
    #     
    #     # Test with valid token
    #     login_response = auth_utils.login("admin", "adminpass123")
    #     assert login_response.status_code == 200
    #     
    #     login_data = login_response.json()
    #     access_token = login_data["access_token"]
    #     
    #     # Test that valid token works for protected endpoint
    #     unique_username = auth_utils.generate_unique_username("expirationtest")
    #     response = auth_utils.create_admin(access_token, unique_username, "pass123456")
    #     assert response.status_code == 201
    #     
    #     # Test with invalid token
    #     unique_username2 = auth_utils.generate_unique_username("expirationtest2")
    #     invalid_response = auth_utils.create_admin("invalid_token", unique_username2, "pass123456")
    #     assert invalid_response.status_code == 401
    
    # def test_multiple_admin_creation(self):
    #     """Test creating multiple admin users."""
    #     # Login as default admin
    #     login_response = auth_utils.login("admin", "adminpass123")
    #     assert login_response.status_code == 200
    #     
    #     login_data = login_response.json()
    #     access_token = login_data["access_token"]
    #     
    #     # Create multiple admins with unique usernames
    #     admin_names = []
    #     for i in range(3):
    #         unique_username = auth_utils.generate_unique_username(f"admin{i}")
    #         admin_names.append(unique_username)
    #     
    #     for i, username in enumerate(admin_names):
    #         response = auth_utils.create_admin(access_token, username, f"pass{i}123456")
    #         assert response.status_code == 201
    #         
    #         data = response.json()
    #         assert data["username"] == username
    #         assert data["id"] > 0
    #     
    #     # Verify all admins can login
    #     for i, username in enumerate(admin_names):
    #         login_response = auth_utils.login(username, f"pass{i}123456")
    #         assert login_response.status_code == 200
    #         
    #         login_data = login_response.json()
    #         assert login_data["admin"]["username"] == username


# Standalone test functions for pytest discovery
def test_auth_login_success():
    """Test successful login."""
    test = TestAuthLogin()
    test.test_login_success()


def test_auth_login_invalid_credentials():
    """Test login with invalid credentials."""
    test = TestAuthLogin()
    test.test_login_invalid_credentials()


def test_auth_refresh_success():
    """Test successful token refresh."""
    test = TestAuthRefresh()
    test.test_refresh_success()


def test_refresh_token_rejected_on_admin_endpoint():
    """Refresh token must not be accepted on admin endpoints."""
    test = TestAuthRefresh()
    test.test_refresh_token_rejected_on_admin_endpoint()


# def test_auth_create_admin_success():
#     """Test successful admin creation."""
#     test = TestAuthCreateAdmin()
#     test.test_create_admin_success()


def test_auth_change_password_success():
    """Test successful password change."""
    test = TestAuthChangePassword()
    test.test_change_password_success()


# def test_auth_complete_workflow():
#     """Test complete authentication workflow."""
#     test = TestAuthEndToEnd()
#     test.test_complete_admin_workflow()