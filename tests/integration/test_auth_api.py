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
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with username and password.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Login response data
        """
        response = requests.post(
            f"{self.auth_base_url}/login",
            json={"username": username, "password": password}
        )
        return response
    
    def refresh_token(self, refresh_token: str) -> requests.Response:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Refresh response
        """
        response = requests.post(
            f"{self.auth_base_url}/refresh",
            json={"refresh_token": refresh_token}
        )
        return response
    
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
    
    def change_password(self, access_token: str, current_password: str, new_password: str) -> requests.Response:
        """
        Change the current admin's password.
        
        Args:
            access_token: JWT access token
            current_password: Current password
            new_password: New password
            
        Returns:
            Password change response
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{self.auth_base_url}/change-password",
            json={"current_password": current_password, "new_password": new_password},
            headers=headers
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
        # First login to get tokens (from JSON) and to establish cookies
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        # For now refresh endpoint still expects the refresh token in the body
        refresh_token = login_data.get("refresh_token")
        
        # Refresh the token
        refresh_response = auth_utils.refresh_token(refresh_token)
        
        assert refresh_response.status_code == 200, f"Expected 200, got {refresh_response.status_code}: {refresh_response.text}"
        
        data = refresh_response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        # Should not include refresh_token in response
        assert "refresh_token" not in data
    
    def test_refresh_invalid_token(self):
        """Test refresh with invalid token."""
        response = auth_utils.refresh_token("invalid_token")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid refresh token" in data["detail"]
    
    def test_refresh_access_token_as_refresh(self):
        """Test using access token as refresh token (should fail)."""
        # First login to get tokens
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        # This test still relies on access_token in the JSON response.
        # It will be fully migrated to cookie-based auth in later steps.
        access_token = login_data.get("access_token")
        
        # Try to use access token as refresh token
        response = auth_utils.refresh_token(access_token)
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid token type" in data["detail"]

    def test_refresh_token_rejected_on_admin_endpoint(self):
        """Refresh token must not be accepted as admin auth; only access tokens work on admin endpoints."""
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        login_data = login_response.json()
        # This test still relies on refresh_token in the JSON response.
        # It will be fully migrated to cookie-based auth in later steps.
        refresh_token = login_data.get("refresh_token")
        # Use an admin-only endpoint (list orders requires get_current_admin)
        orders_url = f"{auth_utils.api_base_url}{auth_utils.api_v1_str}/orders/"
        response = requests.get(
            orders_url,
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response.status_code == 401, f"Expected 401 when using refresh token on admin endpoint, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "Access token required" in data["detail"]


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
        
        login_data = login_response.json()
        # For now, change-password tests still rely on access_token from JSON.
        # These will be migrated to cookie-based auth when protected endpoints
        # switch to reading tokens from cookies in a later step.
        access_token = login_data.get("access_token")
        
        # Change password
        response = auth_utils.change_password(access_token, "adminpass123", "newpass123")
        
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
        new_login_data = new_login_response.json()
        new_access_token = new_login_data.get("access_token")
        revert_response = auth_utils.change_password(new_access_token, "newpass123", "adminpass123")
        assert revert_response.status_code == 200
    
    def test_change_password_unauthorized(self):
        """Test password change without authentication."""
        response = auth_utils.change_password("invalid_token", "oldpass", "newpass")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid authentication token" in data["detail"]
    
    def test_change_password_wrong_current_password(self):
        """Test password change with wrong current password."""
        # First login to get access token
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        access_token = login_data.get("access_token")
        
        # Try to change password with wrong current password
        response = auth_utils.change_password(access_token, "wrongpass", "newpass123")
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "Invalid current password" in data["detail"]
    
    def test_change_password_invalid_data(self):
        """Test password change with invalid data."""
        # First login to get access token
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        access_token = login_data.get("access_token")
        
        # Try to change password with short new password
        response = requests.post(
            f"{auth_utils.auth_base_url}/change-password",
            json={"current_password": "adminpass123", "new_password": "123"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    
    def test_change_password_missing_fields(self):
        """Test password change with missing fields."""
        # First login to get access token
        login_response = auth_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        
        # Try to change password with missing new_password
        response = requests.post(
            f"{auth_utils.auth_base_url}/change-password",
            json={"current_password": "adminpass123"},
            headers={"Authorization": f"Bearer {access_token}"}
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