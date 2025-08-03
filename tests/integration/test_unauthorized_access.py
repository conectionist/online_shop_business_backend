"""Test unauthorized access to protected endpoints"""

import requests
import pytest
from typing import Dict, Any

import os

# Base URLs for different endpoints
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
BASE_URL = f"{API_BASE_URL}/api/v1"

# Protected endpoints to test
PROTECTED_ENDPOINTS = [
    # Business Details
    ("detalii-business", "POST", {}),
    ("detalii-business/1", "PUT", {}),
    ("detalii-business/1", "PATCH", {}),
    ("detalii-business/1", "DELETE", {}),
    
    # Categories
    ("categories", "POST", {"name": "Test Category"}),
    ("categories/1", "PUT", {"name": "Updated Category"}),
    ("categories/1", "DELETE", {}),
    
    # Products
    ("products", "POST", {
        "nume": "Test Product",
        "cantitate": "10",
        "pret": "100",
        "description": "Test description",
        "category_id": "1",
        "unitati_id": "1"
    }),
    ("products/1", "PATCH", {"nume": "Updated Product"}),
    ("products/1", "DELETE", {}),
    
    # Delivery Types
    ("tipuri-livrare", "POST", {"denumire": "Test Delivery"}),
    ("tipuri-livrare/1", "PUT", {"denumire": "Updated Delivery"}),
    ("tipuri-livrare/1", "PATCH", {"denumire": "Patched Delivery"}),
    ("tipuri-livrare/1", "DELETE", {}),
    
    # Delivery Schedules
    ("orare-livrari", "POST", {"denumire": "Test Schedule"}),
    ("orare-livrari/1", "PUT", {"denumire": "Updated Schedule"}),
    ("orare-livrari/1", "PATCH", {"denumire": "Patched Schedule"}),
    ("orare-livrari/1", "DELETE", {}),
    
    # Payment Methods
    ("modalitati-plata", "POST", {"denumire": "Test Payment"}),
    ("modalitati-plata/1", "PUT", {"denumire": "Updated Payment"}),
    ("modalitati-plata/1", "PATCH", {"denumire": "Patched Payment"}),
    ("modalitati-plata/1", "DELETE", {}),
    
    # Units
    ("unitati", "POST", {"denumire": "Test Unit"}),
    ("unitati/1", "PUT", {"denumire": "Updated Unit"}),
    ("unitati/1", "PATCH", {"denumire": "Patched Unit"}),
    ("unitati/1", "DELETE", {}),
    
    # Lists
    ("liste", "POST", {"denumire": "Test List"}),
    ("liste/1", "PUT", {"denumire": "Updated List"}),
    ("liste/1", "PATCH", {"denumire": "Patched List"}),
    ("liste/1", "DELETE", {}),
    
    # Product Overrides
    ("product-overrides", "POST", {
        "product_id": "1",
        "list_id": "1",
        "pret_override": "150"
    }),
    ("product-overrides/1", "PUT", {
        "product_id": "1",
        "list_id": "1",
        "pret_override": "200"
    }),
    ("product-overrides/1", "DELETE", {}),
    
    # Product Images
    ("products/1/images", "POST", {}),  # File upload endpoint
    ("products/1/images/1/position", "PUT", {"position": 1}),
    ("products/1/images/1/primary", "PUT", {}),
    ("products/1/images/1", "DELETE", {}),
    ("products/1/images/reorder", "PUT", {"image_ids": [1, 2, 3]}),
    
    # List Relationships
    ("liste/1/products/1", "POST", {"stoc_produs": 10}),
    ("liste/1/products/1", "DELETE", {}),
    ("liste/1/products", "PUT", {"product_ids": [1, 2, 3]}),
    ("liste/1/delivery-types/1", "POST", {}),
    ("liste/1/delivery-types/1", "DELETE", {}),
    ("liste/1/delivery-types", "PUT", {"delivery_type_ids": [1, 2, 3]}),
]


class TestUnauthorizedAccess:
    """Test that protected endpoints reject unauthenticated requests."""
    
    @pytest.mark.parametrize("endpoint,method,data", PROTECTED_ENDPOINTS)
    def test_unauthorized_access(self, endpoint: str, method: str, data: Dict[str, Any]):
        """
        Test that protected endpoints return 401 Unauthorized when accessed without authentication.
        
        Args:
            endpoint: The endpoint path (relative to /api/v1/)
            method: HTTP method (POST, PUT, PATCH, DELETE)
            data: Request data for POST/PUT/PATCH requests
        """
        url = f"{BASE_URL}/{endpoint}"
        
        # Make request without authentication
        if method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            pytest.fail(f"Unsupported HTTP method: {method}")
        
        # Verify response (FastAPI can return 401 or 403 for unauthenticated access)
        assert response.status_code in [401, 403], (
            f"Expected 401 Unauthorized or 403 Forbidden for {method} {endpoint}, "
            f"got {response.status_code}: {response.text}"
        )
        
        # Verify error message
        try:
            error_data = response.json()
            assert "detail" in error_data, f"Response should contain 'detail' field: {error_data}"
            # Check for various authentication error messages
            error_detail = error_data["detail"]
            assert any(msg in error_detail for msg in ["Not authenticated", "Not authorized", "Forbidden", "Unauthorized"]), (
                f"Error message should indicate authentication required: {error_detail}"
            )
        except ValueError:
            # Some endpoints might return plain text
            response_text = response.text
            assert any(msg in response_text for msg in ["Not authenticated", "Not authorized", "Forbidden", "Unauthorized"]), (
                f"Response should indicate authentication required: {response_text}"
            )


class TestPublicEndpoints:
    """Test that public endpoints work without authentication."""
    
    PUBLIC_ENDPOINTS = [
        # System Config (read-only)
        ("system/config", "GET"),
        
        # GET endpoints for entities (read-only)
        ("business-details", "GET"),
        ("business-details/1", "GET"),
        ("categories", "GET"),
        ("categories/1", "GET"),
        ("products", "GET"),
        ("products/1", "GET"),
        ("delivery-types", "GET"),
        ("delivery-types/1", "GET"),
        ("delivery-schedules", "GET"),
        ("delivery-schedules/1", "GET"),
        ("modalitati-plata", "GET"),
        ("modalitati-plata/1", "GET"),
        ("unitati", "GET"),
        ("unitati/1", "GET"),
        ("lists", "GET"),
        ("lists/1", "GET"),
        ("product-overrides", "GET"),
        ("product-overrides/1", "GET"),
    ]
    
    @pytest.mark.parametrize("endpoint,method", PUBLIC_ENDPOINTS)
    def test_public_endpoints(self, endpoint: str, method: str):
        """
        Test that public endpoints work without authentication.
        
        Args:
            endpoint: The endpoint path (relative to /api/v1/)
            method: HTTP method (GET)
        """
        url = f"{BASE_URL}/{endpoint}"
        
        # Make request without authentication
        response = requests.get(url)
        
        # Verify response (should not be 401)
        assert response.status_code != 401, (
            f"Public endpoint {method} {endpoint} should not require authentication, "
            f"but got 401: {response.text}"
        )
        
        # Accept various status codes for GET requests:
        # - 200: Success with data
        # - 404: Resource not found (acceptable for GET)
        # - 422: Validation error (acceptable for invalid IDs)
        assert response.status_code in [200, 404, 422], (
            f"Unexpected status code {response.status_code} for {method} {endpoint}: {response.text}"
        )


def test_auth_endpoints_work_without_auth():
    """Test that auth endpoints work without authentication."""
    
    # Login endpoint should work without auth (that's the point!)
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "adminpass123"}
    )
    
    # Should either succeed (if credentials are correct) or return 401 for invalid credentials
    # But should NOT return 401 for "Not authenticated" (that would be wrong)
    assert response.status_code in [200, 401], (
        f"Login endpoint should work without auth, got {response.status_code}: {response.text}"
    )
    
    if response.status_code == 401:
        # Check that it's not "Not authenticated" error
        try:
            error_data = response.json()
            assert "Invalid username or password" in error_data.get("detail", ""), (
                f"Login should fail with invalid credentials message, not auth required: {error_data}"
            )
        except ValueError:
            pass  # Plain text response is fine


def test_refresh_endpoint_requires_token():
    """Test that refresh endpoint requires a valid refresh token."""
    
    # Try to refresh without token
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    
    assert response.status_code == 401, (
        f"Refresh endpoint should require valid token, got {response.status_code}: {response.text}"
    )
    
    # Verify error message
    try:
        error_data = response.json()
        assert "detail" in error_data, f"Response should contain 'detail' field: {error_data}"
        assert "Invalid" in error_data["detail"] or "expired" in error_data["detail"], (
            f"Error message should indicate invalid/expired token: {error_data['detail']}"
        )
    except ValueError:
        # Some endpoints might return plain text
        assert "Invalid" in response.text or "expired" in response.text, (
            f"Response should indicate invalid/expired token: {response.text}"
        ) 