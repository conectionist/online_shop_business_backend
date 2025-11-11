"""Integration tests for Payment Types API endpoints"""

import os
import requests
import pytest
from integration.test_auth_utils import auth_utils

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{API_BASE_URL}/api/v1"
PAYMENT_TYPES_URL = f"{API_V1}/payment-types"


def test_get_all_payment_types_public():
    """Test that GET /payment-types/ is public and returns all payment types"""
    response = requests.get(PAYMENT_TYPES_URL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    payment_types = response.json()
    assert isinstance(payment_types, list)
    assert len(payment_types) >= 6, "Should have at least 6 payment types (0-5)"
    
    # Verify expected payment types exist
    type_ids = {pt["id"] for pt in payment_types}
    assert 0 in type_ids, "Should have custom (0)"
    assert 1 in type_ids, "Should have cash (1)"
    assert 2 in type_ids, "Should have physical_card (2)"
    assert 3 in type_ids, "Should have online_card (3)"
    assert 4 in type_ids, "Should have revolut (4)"
    assert 5 in type_ids, "Should have bank_transfer (5)"
    
    # Verify structure
    for pt in payment_types:
        assert "id" in pt
        assert "name" in pt
        assert "friendly_name" in pt
        assert isinstance(pt["id"], int)
        assert isinstance(pt["name"], str)
        assert isinstance(pt["friendly_name"], str)


def test_get_payment_type_by_id_public():
    """Test that GET /payment-types/{id} is public and returns correct payment type"""
    # Test getting cash (id=1)
    response = requests.get(f"{PAYMENT_TYPES_URL}/1")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    payment_type = response.json()
    assert payment_type["id"] == 1
    assert payment_type["name"] == "cash"
    assert payment_type["friendly_name"] == "Numerar"
    
    # Test getting revolut (id=4)
    response = requests.get(f"{PAYMENT_TYPES_URL}/4")
    assert response.status_code == 200
    payment_type = response.json()
    assert payment_type["id"] == 4
    assert payment_type["name"] == "revolut"
    assert payment_type["friendly_name"] == "Transfer Revolut"


def test_get_payment_type_invalid_id():
    """Test that GET /payment-types/{id} returns 404 for invalid ID"""
    # Test negative ID
    response = requests.get(f"{PAYMENT_TYPES_URL}/-1")
    assert response.status_code == 422, "Negative ID should return 422 validation error"
    
    # Test non-existent ID
    response = requests.get(f"{PAYMENT_TYPES_URL}/999")
    assert response.status_code == 404, "Non-existent ID should return 404"


def test_payment_types_romanian_friendly_names():
    """Test that payment types have Romanian friendly names"""
    response = requests.get(PAYMENT_TYPES_URL)
    assert response.status_code == 200
    
    payment_types = {pt["id"]: pt for pt in response.json()}
    
    # Verify Romanian friendly names
    assert payment_types[0]["friendly_name"] == "Nespecificat"
    assert payment_types[1]["friendly_name"] == "Numerar"
    assert payment_types[2]["friendly_name"] == "Plata cu cardul"
    assert payment_types[3]["friendly_name"] == "Plata cu card online"
    assert payment_types[4]["friendly_name"] == "Transfer Revolut"
    assert payment_types[5]["friendly_name"] == "Transfer bancar"


def test_payment_types_ordered_by_id():
    """Test that payment types are returned ordered by ID"""
    response = requests.get(PAYMENT_TYPES_URL)
    assert response.status_code == 200
    
    payment_types = response.json()
    ids = [pt["id"] for pt in payment_types]
    
    # Should be ordered by ID (0, 1, 2, 3, 4, 5)
    assert ids == sorted(ids), "Payment types should be ordered by ID"

