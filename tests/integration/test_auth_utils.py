"""
Authentication utilities for integration tests.

This module provides utilities for handling authentication in tests,
including login, token management, and authenticated requests.
"""

import os
import requests
from typing import Optional


class AuthTestUtils:
    """Authentication utilities for integration tests."""
    
    def __init__(self):
        """Initialize the authentication utilities."""
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_v1_str = "/api/v1"
        self.auth_url = f"{self.api_base_url}{self.api_v1_str}/auth"
        # Use a session to track cookies across requests
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
    def login(self, username: str = "admin", password: str = "adminpass123") -> bool:
        """
        Login and get authentication tokens.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            True if login successful, False otherwise
        """
        login_data = {
            "username": username,
            "password": password
        }
        
        response = self.session.post(
            f"{self.auth_url}/login",
            json=login_data
        )
        
        if response.status_code == 200:
            # Tokens are now issued via httpOnly cookies; extract them so that
            # existing tests, which still rely on Authorization headers, can
            # continue to function while the API migrates to cookie-based auth.
            self.access_token = response.cookies.get("access_token")
            self.refresh_token = response.cookies.get("refresh_token")
            return True
        else:
            self.access_token = None
            self.refresh_token = None
            return False
    
    def get_auth_headers(self) -> dict:
        """
        Get authentication headers for requests.
        
        Returns:
            Dictionary with Authorization header if token is available
        """
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    def make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request with the current access token.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object
        """
        headers = kwargs.get("headers", {})
        auth_headers = self.get_auth_headers()
        headers.update(auth_headers)
        kwargs["headers"] = headers
        
        return requests.request(method, url, **kwargs)
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            return False
            
        refresh_data = {
            "refresh_token": self.refresh_token
        }
        
        response = requests.post(
            f"{self.auth_url}/refresh",
            json=refresh_data
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            return True
        else:
            return False
    
    def logout(self):
        """Clear authentication tokens."""
        self.access_token = None
        self.refresh_token = None


# Global authentication utility instance
auth_utils = AuthTestUtils() 