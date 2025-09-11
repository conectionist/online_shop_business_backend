from datetime import datetime, date
import os
import requests
from integration.test_auth_utils import auth_utils
import pytest


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{API_BASE_URL}/api/v1"


def _get_any_list_id_or_skip():
    """Get any available list ID for testing"""
    resp = requests.get(f"{API_V1}/liste")
    assert resp.status_code == 200, f"Failed to list lists: {resp.text}"
    lists = resp.json()
    if not lists:
        pytest.skip("No lists available in test environment")
        return None
    return lists[0]["id"]


def test_orders_create_public_success():
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "John Doe",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
        "order_notes": "Leave at door",
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    # Order creation is now public - no auth required
    assert resp.status_code == 201, resp.text
    order = resp.json()
    assert order["nume_client"] == "John Doe"
    assert order["liste_id"] == list_id
    assert order["delivery_type_id"] == 1
    assert order["payment_method_id"] == 5


def test_orders_create_public_and_read_with_auth():
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "John Doe",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 2,  # Ridicare de la punct fix
        "payment_method_id": 6,  # Card
        "order_notes": "Leave at door",
    }
    # Create order without auth (public)
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, resp.text
    order = resp.json()
    order_id = order["id"]

    # List requires auth
    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/")
    assert resp.status_code == 200
    assert any(o["id"] == order_id for o in resp.json())

    # Get details requires auth
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


def test_orders_list_and_get_require_auth():
    # Create an order without auth (public) to have an ID
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "Jane Doe",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu (pickup)
        "payment_method_id": 7,  # Transfer Bancar
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201
    order_id = resp.json()["id"]

    # List without auth
    resp = requests.get(f"{API_V1}/orders/")
    # No Authorization header → HTTPBearer returns 403
    assert resp.status_code == 403

    # Get without auth
    resp = requests.get(f"{API_V1}/orders/{order_id}")
    # No Authorization header → HTTPBearer returns 403
    assert resp.status_code == 403


def test_orders_endpoints_invalid_token_returns_401():
    # Invalid/garbled token should result in 401 from get_current_admin
    headers = {"Authorization": "Bearer invalid_token"}
    # List with invalid token
    resp = requests.get(f"{API_V1}/orders/", headers=headers)
    assert resp.status_code == 401


def test_orders_create_with_items_success():
    # Discover a list
    list_resp = requests.get(f"{API_V1}/liste")
    assert list_resp.status_code == 200, list_resp.text
    lists = list_resp.json()
    if not lists:
        pytest.skip("No lists available in test environment")
    liste_id = lists[0]["id"]

    # Discover a product (and unit)
    prod_resp = requests.get(f"{API_V1}/products")
    assert prod_resp.status_code == 200, prod_resp.text
    products = prod_resp.json()
    if not products:
        pytest.skip("No products available in test environment")
    product = products[0]
    produse_id = product["id"]
    unitati_id = product["unitati_id"]
    pret_produs = product["pret"]

    # Auth
    if not auth_utils.access_token:
        auth_utils.login()

    payload = {
        "nume_client": "Order With Items",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": liste_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
        "items": [
            {
                "produse_id": produse_id,
                "pret_produs": pret_produs,
                "cantitate_produs": 1,
                "unitati_id": unitati_id,
            }
        ],
    }

    create_resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    assert created["liste_id"] == liste_id
    assert created["nume_client"] == "Order With Items"
    assert isinstance(created.get("items", []), list)
    assert len(created["items"]) == 1


def _create_minimal_order_and_return_id():
    list_resp = requests.get(f"{API_V1}/liste")
    assert list_resp.status_code == 200, list_resp.text
    lists = list_resp.json()
    if not lists:
        pytest.skip("No lists available in test environment")
    liste_id = lists[0]["id"]

    payload = {
        "nume_client": "Patch/Delete Target",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": liste_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_orders_patch_updates_fields():
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    patch_payload = {"nume_client": "Updated Name", "order_notes": "Updated notes"}
    resp = auth_utils.make_authenticated_request("PATCH", f"{API_V1}/orders/{order_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["nume_client"] == "Updated Name"
    assert body.get("order_notes") == "Updated notes"


def test_orders_delete_removes_order():
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    # Delete
    resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}")
    assert resp.status_code == 204, resp.text
    # Verify not found
    get_after = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}")
    assert get_after.status_code == 404


# ---------- Additional coverage ----------

def _discover_product_and_unit_or_skip():
    prod_resp = requests.get(f"{API_V1}/products")
    assert prod_resp.status_code == 200, prod_resp.text
    products = prod_resp.json()
    if not products:
        pytest.skip("No products available in test environment")
    p = products[0]
    return p["id"], p["unitati_id"], p["pret"]


def test_orders_items_crud_lifecycle():
    # Arrange
    list_id = _get_any_list_id_or_skip()
    produse_id, unitati_id, pret = _discover_product_and_unit_or_skip()
    if not auth_utils.access_token:
        auth_utils.login()
    order_payload = {
        "nume_client": "Items Lifecycle",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    create = requests.post(f"{API_V1}/orders/", json=order_payload)
    assert create.status_code == 201, create.text
    order_id = create.json()["id"]

    # Add item
    add_item = {
        "produse_id": produse_id,
        "pret_produs": pret,
        "cantitate_produs": 1,
        "unitati_id": unitati_id,
    }
    resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order_id}/products", json=add_item)
    assert resp.status_code == 201, resp.text

    # Update item
    update_item = {
        "produse_id": produse_id,
        "pret_produs": pret + 10,
        "cantitate_produs": 2,
        "unitati_id": unitati_id,
    }
    resp = auth_utils.make_authenticated_request(
        "PATCH", f"{API_V1}/orders/{order_id}/products/{produse_id}", json=update_item
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cantitate_produs"] == 2
    assert body["pret_produs"] == pret + 10

    # Remove item
    resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}/products/{produse_id}")
    assert resp.status_code == 204, resp.text


def test_orders_filters_nume_client_list_id_date_range():
    if not auth_utils.access_token:
        auth_utils.login()
    list_id = _get_any_list_id_or_skip()
    now = datetime.utcnow()
    iso = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # Create two orders
    for name in ["Filter Alice", "Filter Bob"]:
        payload = {"nume_client": name, "data_plasarii": iso, "liste_id": list_id, "delivery_type_id": 1, "payment_method_id": 5}
        r = requests.post(f"{API_V1}/orders/", json=payload)
        assert r.status_code == 201, r.text

    # Filter by substring
    r = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?nume_client=Alice")
    assert r.status_code == 200
    names = [o["nume_client"] for o in r.json()]
    assert any("Alice" in n for n in names)

    # Filter by list id
    r = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?liste_id={list_id}")
    assert r.status_code == 200
    assert all(o["liste_id"] == list_id for o in r.json())

    # Filter by date range (same instant)
    r = auth_utils.make_authenticated_request(
        "GET", f"{API_V1}/orders/?data_plasarii_start={iso}&data_plasarii_end={iso}"
    )
    assert r.status_code == 200


def test_orders_write_with_invalid_token_returns_401():
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "Invalid Token Write",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    headers = {"Authorization": "Bearer invalid_token"}
    r = requests.post(f"{API_V1}/orders/", json=payload, headers=headers)
    # Order creation is public, so invalid token should still work
    assert r.status_code == 201


def test_orders_validation_errors():
    if not auth_utils.access_token:
        auth_utils.login()
    list_id = _get_any_list_id_or_skip()
    # Create order
    order_payload = {
        "nume_client": "Validation Target",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    order_resp = requests.post(f"{API_V1}/orders/", json=order_payload)
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    # Add item with non-existent product
    bad_item = {"produse_id": 999999, "pret_produs": 100, "cantitate_produs": 1, "unitati_id": 1}
    r = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order_id}/products", json=bad_item)
    assert r.status_code == 400

    # Add item with invalid unit
    # Discover a real product id
    produse_id, _, pret = _discover_product_and_unit_or_skip()
    bad_unit_item = {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 1, "unitati_id": 999999}
    r = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order_id}/products", json=bad_unit_item)
    assert r.status_code == 400

    # Add item with invalid quantity (schema validation 422)
    _, unitati_id, pret = _discover_product_and_unit_or_skip()
    zero_qty = {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 0, "unitati_id": unitati_id}
    r = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order_id}/products", json=zero_qty)
    assert r.status_code == 422


def test_orders_attempt_change_liste_id_ignored():
    if not auth_utils.access_token:
        auth_utils.login()
    list_id = _get_any_list_id_or_skip()
    # Create
    payload = {
        "nume_client": "Immutable List",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    r = requests.post(f"{API_V1}/orders/", json=payload)
    assert r.status_code == 201
    order = r.json()
    order_id = order["id"]
    # Attempt to change liste_id via patch (should be ignored or rejected). Our schema ignores extra fields.
    patch_payload = {"liste_id": list_id + 1, "nume_client": "Still Immutable"}
    r = auth_utils.make_authenticated_request("PATCH", f"{API_V1}/orders/{order_id}", json=patch_payload)
    assert r.status_code == 200
    # Verify liste_id unchanged
    r = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}")
    assert r.status_code == 200
    assert r.json()["liste_id"] == list_id


# ---------- New tests for delivery and payment validation ----------

def test_orders_create_without_required_fields_fails():
    """Test that order creation fails without delivery_type_id and payment_method_id"""
    list_id = _get_any_list_id_or_skip()
    
    # Test missing delivery_type_id
    payload_missing_delivery = {
        "nume_client": "Missing Delivery",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_missing_delivery)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    
    # Test missing payment_method_id
    payload_missing_payment = {
        "nume_client": "Missing Payment",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_missing_payment)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_orders_create_with_home_delivery_requires_address():
    """Test that home delivery requires delivery address"""
    list_id = _get_any_list_id_or_skip()
    
    # Test home delivery without address (should fail)
    payload_home_no_address = {
        "nume_client": "Home Delivery No Address",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 3,  # Livrare la domiciliu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_home_no_address)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    assert "delivery address is required" in resp.text.lower()
    
    # Test home delivery with address (should succeed)
    payload_home_with_address = {
        "nume_client": "Home Delivery With Address",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 3,  # Livrare la domiciliu
        "payment_method_id": 5,  # Cash
        "delivery_address": "123 Test Street, Test City",
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_home_with_address)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    order = resp.json()
    assert order["delivery_address"] == "123 Test Street, Test City"


def test_orders_update_with_new_delivery_method():
    """Test updating order with new delivery method"""
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Update delivery method
    patch_payload = {
        "delivery_type_id": 2,  # Ridicare de la punct fix
        "delivery_address": None,  # Clear address for pickup
    }
    resp = auth_utils.make_authenticated_request("PATCH", f"{API_V1}/orders/{order_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    
    # Verify update
    order = resp.json()
    assert order["delivery_type_id"] == 2
    assert order["delivery_address"] is None


def test_orders_filter_by_delivery_and_payment_methods():
    """Test filtering orders by delivery and payment methods"""
    if not auth_utils.access_token:
        auth_utils.login()
    
    list_id = _get_any_list_id_or_skip()
    
    # Create orders with different delivery and payment methods
    orders_data = [
        (1, 5),  # Sediu + Cash
        (2, 6),  # Punct fix + Card
        (3, 7),  # Domiciliu + Transfer
    ]
    
    for i, (dt_id, pm_id) in enumerate(orders_data):
        payload = {
            "nume_client": f"Filter Test {i+1}",
            "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "liste_id": list_id,
            "delivery_type_id": dt_id,
            "payment_method_id": pm_id,
        }
        if dt_id == 3:  # Home delivery needs address
            payload["delivery_address"] = f"Address {i+1}"
        
        resp = requests.post(f"{API_V1}/orders/", json=payload)
        assert resp.status_code == 201, f"Failed to create order {i+1}: {resp.text}"
    
    # Test filtering by delivery type
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?delivery_type_id=1")
    assert resp.status_code == 200
    orders = resp.json()
    assert all(o["delivery_type_id"] == 1 for o in orders)
    
    # Test filtering by payment method
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?payment_method_id=5")
    assert resp.status_code == 200
    orders = resp.json()
    assert all(o["payment_method_id"] == 5 for o in orders)
    
    # Test sorting by delivery type
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?sort_by=delivery_type_id&sort_order=asc")
    assert resp.status_code == 200
    orders = resp.json()
    delivery_ids = [o["delivery_type_id"] for o in orders]
    assert delivery_ids == sorted(delivery_ids)


# ---------- Phone Number Validation Tests ----------

def test_orders_phone_number_validation_valid_formats():
    """Test that valid phone number formats are accepted"""
    list_id = _get_any_list_id_or_skip()
    
    # Test valid phone number formats
    valid_phones = [
        "+40712345678",      # International format with +
        "40712345678",       # International format without +
        "0741234567",        # Romanian mobile starting with 0
        "7123456789",        # 10 digits starting with 7
        "1234567890",        # 10 digits starting with 1
        "+1234567890",       # US format with +
        "123456789012345",   # 15 digits (max length)
    ]
    
    for phone in valid_phones:
        payload = {
            "nume_client": f"Test Customer {phone}",
            "phone_number": phone,
            "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "liste_id": list_id,
            "delivery_type_id": 1,  # Ridicare de la sediu
            "payment_method_id": 5,  # Cash
        }
        resp = requests.post(f"{API_V1}/orders/", json=payload)
        assert resp.status_code == 201, f"Valid phone {phone} should be accepted, got {resp.status_code}: {resp.text}"
        
        # Verify phone number is stored correctly
        order = resp.json()
        assert order["phone_number"] == phone, f"Phone number {phone} not stored correctly"


def test_orders_phone_number_validation_invalid_formats():
    """Test that invalid phone number formats are rejected with 422"""
    list_id = _get_any_list_id_or_skip()
    
    # Test invalid phone number formats
    invalid_phones = [
        "12345",             # Too short (5 digits)
        "123456789012345678901",  # Too long (21 digits)
        "abc123456789",      # Contains letters
        "123-456-7890",      # Contains hyphens
        "123 456 7890",      # Contains spaces
        "(123) 456-7890",    # Contains parentheses and spaces
        "00-123456789",      # Contains hyphens
    ]
    
    for phone in invalid_phones:
        payload = {
            "nume_client": f"Test Customer {phone}",
            "phone_number": phone,
            "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "liste_id": list_id,
            "delivery_type_id": 1,  # Ridicare de la sediu
            "payment_method_id": 5,  # Cash
        }
        resp = requests.post(f"{API_V1}/orders/", json=payload)
        assert resp.status_code == 422, f"Invalid phone {phone} should be rejected with 422, got {resp.status_code}: {resp.text}"
        
        # Verify error message mentions phone number validation
        error_detail = resp.json().get("detail", [])
        assert any("phone_number" in str(error) for error in error_detail), f"Error should mention phone_number for {phone}"


def test_orders_phone_number_optional_field():
    """Test that phone_number is truly optional"""
    list_id = _get_any_list_id_or_skip()
    
    # Test without phone_number field
    payload_no_phone = {
        "nume_client": "Customer Without Phone",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_no_phone)
    assert resp.status_code == 201, f"Order without phone should be accepted, got {resp.status_code}: {resp.text}"
    
    order = resp.json()
    assert order["phone_number"] is None, "Phone number should be None when not provided"
    
    # Test with phone_number as null
    payload_null_phone = {
        "nume_client": "Customer With Null Phone",
        "phone_number": None,
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_null_phone)
    assert resp.status_code == 201, f"Order with null phone should be accepted, got {resp.status_code}: {resp.text}"
    
    order = resp.json()
    assert order["phone_number"] is None, "Phone number should be None when explicitly set to null"


def test_orders_phone_number_update_validation():
    """Test phone number validation in order updates"""
    if not auth_utils.access_token:
        auth_utils.login()
    
    list_id = _get_any_list_id_or_skip()
    
    # Create order with valid phone number
    payload = {
        "nume_client": "Update Test Customer",
        "phone_number": "+40712345678",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201
    order_id = resp.json()["id"]
    
    # Test updating with valid phone number
    update_payload = {"phone_number": "40798765432"}
    resp = auth_utils.make_authenticated_request("PATCH", f"{API_V1}/orders/{order_id}", json=update_payload)
    assert resp.status_code == 200, f"Valid phone update should succeed, got {resp.status_code}: {resp.text}"
    
    order = resp.json()
    assert order["phone_number"] == "40798765432", "Phone number should be updated correctly"
    
    # Test updating with invalid phone number
    invalid_update_payload = {"phone_number": "12345"}  # Too short
    resp = auth_utils.make_authenticated_request("PATCH", f"{API_V1}/orders/{order_id}", json=invalid_update_payload)
    assert resp.status_code == 422, f"Invalid phone update should fail with 422, got {resp.status_code}: {resp.text}"
    
    # Test updating to null (should work)
    null_update_payload = {"phone_number": None}
    resp = auth_utils.make_authenticated_request("PATCH", f"{API_V1}/orders/{order_id}", json=null_update_payload)
    assert resp.status_code == 200, f"Null phone update should succeed, got {resp.status_code}: {resp.text}"
    
    order = resp.json()
    assert order["phone_number"] is None, "Phone number should be set to None"


def test_orders_phone_number_max_length_validation():
    """Test phone number maximum length validation"""
    list_id = _get_any_list_id_or_skip()
    
    # Test exactly 20 characters (should work)
    phone_20_chars = "12345678901234567890"  # 20 digits
    payload = {
        "nume_client": "Max Length Test",
        "phone_number": phone_20_chars,
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, f"20-character phone should be accepted, got {resp.status_code}: {resp.text}"
    
    # Test 21 characters (should fail)
    phone_21_chars = "123456789012345678901"  # 21 digits
    payload["phone_number"] = phone_21_chars
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 422, f"21-character phone should be rejected with 422, got {resp.status_code}: {resp.text}"


def test_orders_phone_number_whitespace_handling():
    """Test that whitespace in phone numbers is handled correctly"""
    list_id = _get_any_list_id_or_skip()
    
    # Test phone number with leading/trailing whitespace (should be trimmed)
    payload = {
        "nume_client": "Whitespace Test",
        "phone_number": "  40712345678  ",  # With spaces
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, f"Phone with whitespace should be accepted, got {resp.status_code}: {resp.text}"
    
    order = resp.json()
    assert order["phone_number"] == "40712345678", "Whitespace should be trimmed from phone number"
    
    # Test empty string (should fail validation)
    payload["phone_number"] = ""
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 422, f"Empty string phone should be rejected with 422, got {resp.status_code}: {resp.text}"
    
    # Test whitespace-only string (should fail validation)
    payload["phone_number"] = "   "
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 422, f"Whitespace-only phone should be rejected with 422, got {resp.status_code}: {resp.text}"


# ---------- Merge similar orders tests ----------

def test_orders_merge_similar_basic_merge():
    """Merging two orders for same customer (case/diacritics-insensitive) within the same list."""
    # Arrange
    list_resp = requests.get(f"{API_V1}/liste")
    assert list_resp.status_code == 200, list_resp.text
    lists = list_resp.json()
    if not lists:
        pytest.skip("No lists available in test environment")
    liste_id = lists[0]["id"]

    produse_id, unitati_id, pret = _discover_product_and_unit_or_skip()
    # Create oldest order
    older_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    payload_old = {
        "nume_client": "Ştefan Pop",
        "phone_number": None,
        "data_plasarii": older_iso,
        "liste_id": liste_id,
        "delivery_type_id": 1,
        "payment_method_id": 5,
        "order_notes": None,
        "items": [
            {
                "produse_id": produse_id,
                "pret_produs": pret,
                "cantitate_produs": 1,
                "unitati_id": unitati_id,
            }
        ],
    }
    r1 = requests.post(f"{API_V1}/orders/", json=payload_old)
    assert r1.status_code == 201, r1.text
    old_order = r1.json()

    # Create newest order (different delivery/payment, has phone and note)
    newer_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    payload_new = {
        "nume_client": "stefan pop",
        "phone_number": "+40123456789",
        "data_plasarii": newer_iso,
        "liste_id": liste_id,
        "delivery_type_id": 2,
        "payment_method_id": 6,
        "order_notes": "new note",
    }
    r2 = requests.post(f"{API_V1}/orders/", json=payload_new)
    assert r2.status_code == 201, r2.text
    new_order = r2.json()

    # Add a distinct item to the new order via items endpoint to cover items merge
    if not auth_utils.access_token:
        auth_utils.login()
    add_item = {
        "produse_id": produse_id,
        "pret_produs": pret + 5,
        "cantitate_produs": 2,
        "unitati_id": unitati_id,
    }
    r_add = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{new_order['id']}/products", json=add_item)
    assert r_add.status_code == 201, r_add.text

    # Act: fetch merged
    resp = auth_utils.make_authenticated_request(
        "GET",
        f"{API_V1}/orders/?liste_id={liste_id}&merge_similar=true&limit=1000",
    )
    assert resp.status_code == 200, resp.text
    orders = resp.json()
    # Identify merged entry via newest phone/notes on same list (robust to collation/id ordering)
    candidates = [
        o for o in orders
        if o["liste_id"] == liste_id and o.get("phone_number") == "+40123456789" and o.get("order_notes") == "new note"
    ]
    assert len(candidates) >= 1, "Merged entry not found by expected merged fields"
    m = candidates[0]

    # Assert merge rules
    assert m["phone_number"] == "+40123456789"  # newest non-empty
    assert m["data_plasarii"] >= old_order["data_plasarii"]
    assert m["delivery_type_id"] == 2
    assert m["payment_method_id"] == 6
    assert m.get("order_notes") == "new note"
    assert m["created_at"] == old_order["created_at"]
    assert m["updated_at"] >= old_order["updated_at"]

    # Items from both orders are present
    assert isinstance(m.get("items", []), list)
    assert len(m["items"]) >= 2


def test_orders_merge_similar_different_lists_not_merged():
    """Orders with same normalized name across different lists should not merge."""
    # Arrange two distinct lists
    list_resp = requests.get(f"{API_V1}/liste")
    assert list_resp.status_code == 200, list_resp.text
    lists = list_resp.json()
    if len(lists) < 2:
        pytest.skip("Need at least two lists to validate cross-list non-merge")
    list_a = lists[0]["id"]
    list_b = lists[1]["id"]

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    base_payload = {
        "nume_client": "Ștefan Same",
        "data_plasarii": now_iso,
        "delivery_type_id": 1,
        "payment_method_id": 5,
    }
    r_a = requests.post(f"{API_V1}/orders/", json={**base_payload, "liste_id": list_a})
    assert r_a.status_code == 201, r_a.text
    r_b = requests.post(f"{API_V1}/orders/", json={**base_payload, "liste_id": list_b})
    assert r_b.status_code == 201, r_b.text

    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?merge_similar=true&nume_client=Stefan&limit=1000")
    assert resp.status_code == 200
    body = resp.json()
    names = [(o["nume_client"], o["liste_id"]) for o in body if o["nume_client"].lower().startswith("ștefan") or o["nume_client"].lower().startswith("ştefan")]
    # Expect two separate entries for the two lists
    lists_seen = {lid for _, lid in names}
    assert list_a in lists_seen and list_b in lists_seen
