"""Integration tests for session management endpoints."""

import os
import requests
import pytest
import time
from typing import Dict, Any


class SessionTestUtils:
    """Test utilities for the Session Management API."""
    
    def __init__(self):
        """Initialize with the Session Management endpoint."""
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_v1_str = "/api/v1"
        self.auth_base_url = f"{self.api_base_url}{self.api_v1_str}/auth"
        # Use a session to track cookies across requests
        self.session = requests.Session()
    
    def login(self, username: str, password: str) -> requests.Response:
        """Login with username and password."""
        return self.session.post(
            f"{self.auth_base_url}/login",
            json={"username": username, "password": password}
        )
    
    def logout(self) -> requests.Response:
        """Logout from current session."""
        return self.session.post(f"{self.auth_base_url}/logout")
    
    def logout_all(self) -> requests.Response:
        """Logout from all sessions."""
        return self.session.post(f"{self.auth_base_url}/logout-all")
    
    def list_sessions(self) -> requests.Response:
        """List all active sessions."""
        return self.session.get(f"{self.auth_base_url}/sessions")
    
    def get_current_session(self) -> requests.Response:
        """Get current session details."""
        return self.session.get(f"{self.auth_base_url}/sessions/current")
    
    def get_session_by_id(self, session_id: int) -> requests.Response:
        """Get specific session by ID."""
        return self.session.get(f"{self.auth_base_url}/sessions/{session_id}")
    
    def revoke_session(self, session_id: int) -> requests.Response:
        """Revoke a specific session by ID."""
        return self.session.delete(f"{self.auth_base_url}/sessions/{session_id}")

    def logout_others(self) -> requests.Response:
        """Logout from all other sessions except the current one."""
        return self.session.post(f"{self.auth_base_url}/logout-others")


@pytest.fixture
def session_utils():
    """Fixture to provide session test utilities."""
    return SessionTestUtils()


@pytest.fixture
def second_session():
    """Fixture to provide a second session for multi-session tests."""
    utils = SessionTestUtils()
    utils.session.headers["User-Agent"] = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
    return utils


@pytest.fixture(autouse=True)
def reset_admin_sessions():
    """Ensure a clean session slate for admin before each test."""
    utils = SessionTestUtils()
    login_response = utils.login("admin", "adminpass123")
    if login_response.status_code == 200:
        utils.logout_all()
    yield


class TestSessionManagement:
    """Test suite for session management endpoints."""
    
    def test_list_sessions_unauthenticated(self, session_utils):
        """Test that listing sessions requires authentication."""
        response = session_utils.list_sessions()
        assert response.status_code == 401
    
    def test_list_sessions_single_session(self, session_utils):
        """Test listing sessions with a single active session."""
        # Login
        login_response = session_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        # List sessions
        response = session_utils.list_sessions()
        assert response.status_code == 200
        
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["sessions"]) == 1
        
        # Verify session structure
        session = data["sessions"][0]
        assert "id" in session
        assert "session_name" in session
        assert "device_type" in session
        assert "browser_name" in session
        assert "os_name" in session
        assert "ip_address" in session
        assert "created_at" in session
        assert "expires_at" in session
        assert "is_current" in session
        assert session["is_current"] is True
    
    def test_list_sessions_multiple_sessions(self, session_utils, second_session):
        """Test listing sessions with multiple active sessions."""
        # Login from first session
        login1 = session_utils.login("admin", "adminpass123")
        assert login1.status_code == 200
        
        # Login from second session
        login2 = second_session.login("admin", "adminpass123")
        assert login2.status_code == 200
        
        # List sessions from first session
        response = session_utils.list_sessions()
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert len(data["sessions"]) == 2
        
        # Verify one session is marked as current
        current_sessions = [s for s in data["sessions"] if s["is_current"]]
        assert len(current_sessions) == 1
    
    def test_get_current_session(self, session_utils):
        """Test getting current session details."""
        # Login
        login_response = session_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        # Get current session
        response = session_utils.get_current_session()
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "session_name" in data
        assert "device_type" in data
        assert "browser_name" in data
        assert "os_name" in data
        assert data["is_current"] is True
    
    def test_get_current_session_unauthenticated(self, session_utils):
        """Test that getting current session requires authentication."""
        response = session_utils.get_current_session()
        assert response.status_code == 401
    
    def test_get_session_by_id(self, session_utils):
        """Test getting a specific session by ID."""
        # Login
        login_response = session_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        # List sessions to get session ID
        list_response = session_utils.list_sessions()
        assert list_response.status_code == 200
        sessions = list_response.json()["sessions"]
        session_id = sessions[0]["id"]
        
        # Get session by ID
        response = session_utils.get_session_by_id(session_id)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == session_id
        assert data["is_current"] is True
    
    def test_get_session_by_id_not_found(self, session_utils):
        """Test getting a non-existent session returns 404."""
        # Login
        login_response = session_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        # Try to get non-existent session
        response = session_utils.get_session_by_id(999999)
        assert response.status_code == 404
    
    def test_revoke_session_other_device(self, session_utils, second_session):
        """Test revoking a session from another device."""
        # Login from first session
        login1 = session_utils.login("admin", "adminpass123")
        assert login1.status_code == 200
        
        # Login from second session
        login2 = second_session.login("admin", "adminpass123")
        assert login2.status_code == 200
        
        # List sessions from first session
        list_response = session_utils.list_sessions()
        assert list_response.status_code == 200
        sessions = list_response.json()["sessions"]
        assert len(sessions) == 2
        
        # Find the other session (not current)
        other_session = [s for s in sessions if not s["is_current"]][0]
        other_session_id = other_session["id"]
        
        # Revoke the other session
        revoke_response = session_utils.revoke_session(other_session_id)
        assert revoke_response.status_code == 200
        
        data = revoke_response.json()
        assert data["message"] == "Session revoked successfully"
        assert data["session_id"] == other_session_id
        
        # Verify the revoked session is no longer active
        list_response2 = session_utils.list_sessions()
        assert list_response2.status_code == 200
        sessions2 = list_response2.json()["sessions"]
        assert len(sessions2) == 1
        
        # Verify the second session can no longer make requests
        second_list_response = second_session.list_sessions()
        assert second_list_response.status_code == 401
    
    def test_revoke_current_session_fails(self, session_utils):
        """Test that revoking the current session returns an error."""
        # Login
        login_response = session_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        # List sessions to get current session ID
        list_response = session_utils.list_sessions()
        assert list_response.status_code == 200
        sessions = list_response.json()["sessions"]
        current_session = [s for s in sessions if s["is_current"]][0]
        current_session_id = current_session["id"]
        
        # Try to revoke current session
        response = session_utils.revoke_session(current_session_id)
        assert response.status_code == 400
        assert "Cannot revoke current session" in response.json()["detail"]
    
    def test_revoke_session_not_found(self, session_utils):
        """Test revoking a non-existent session returns 404."""
        # Login
        login_response = session_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        # Try to revoke non-existent session
        response = session_utils.revoke_session(999999)
        assert response.status_code == 404
    
    def test_session_lifecycle(self, session_utils):
        """Test complete session lifecycle: login -> list -> logout."""
        # Login
        login_response = session_utils.login("admin", "adminpass123")
        assert login_response.status_code == 200
        
        # List sessions - should have 1 active session
        list_response1 = session_utils.list_sessions()
        assert list_response1.status_code == 200
        assert list_response1.json()["total"] == 1
        
        # Logout
        logout_response = session_utils.logout()
        assert logout_response.status_code == 200
        
        # Try to list sessions after logout - should fail
        list_response2 = session_utils.list_sessions()
        assert list_response2.status_code == 401
    
    def test_logout_all_revokes_all_sessions(self, session_utils, second_session):
        """Test that logout-all revokes all sessions."""
        # Login from first session
        login1 = session_utils.login("admin", "adminpass123")
        assert login1.status_code == 200
        
        # Login from second session
        login2 = second_session.login("admin", "adminpass123")
        assert login2.status_code == 200
        
        # Verify both sessions are active
        list_response1 = session_utils.list_sessions()
        assert list_response1.status_code == 200
        assert list_response1.json()["total"] == 2
        
        # Logout from all devices
        logout_all_response = session_utils.logout_all()
        assert logout_all_response.status_code == 200
        
        # Verify both sessions are now invalid
        list_response2 = session_utils.list_sessions()
        assert list_response2.status_code == 401
        
        list_response3 = second_session.list_sessions()
        assert list_response3.status_code == 401
    
    def test_session_metadata_captured(self, session_utils):
        """Test that session metadata is properly captured."""
        # Login with custom user agent
        custom_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        login_response = session_utils.session.post(
            f"{session_utils.auth_base_url}/login",
            json={"username": "admin", "password": "adminpass123"},
            headers=custom_headers
        )
        assert login_response.status_code == 200
        
        # Get current session
        response = session_utils.get_current_session()
        assert response.status_code == 200
        
        data = response.json()
        # Verify metadata is captured (exact values depend on parser)
        assert data["device_type"] in ["desktop", "mobile", "tablet", "unknown"]
        assert data["browser_name"] is not None
        assert data["os_name"] is not None
        assert data["session_name"] is not None
        assert data["ip_address"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
