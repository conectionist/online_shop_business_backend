from datetime import datetime, date, timezone
import os
import requests
from integration.test_auth_utils import auth_utils
from integration.test_lists_api import ListTestUtils
import pytest


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{API_BASE_URL}/api/v1"

list_utils = ListTestUtils()


def _open_list_for_orders(list_id):
    """Make *list_id* the list customers can order from (publishing unpublishes the others)."""
    resp = requests.get(f"{API_V1}/liste/published")
    assert resp.status_code == 200, resp.text
    published = resp.json()
    if published is None or published["id"] != list_id:
        list_utils.update_entity(list_id, is_published=True)


def _get_orderable_list_id_or_skip():
    """Return the first list's ID, opening it for orders.

    Orders are only accepted for the published, unexpired list, and other tests
    publish lists of their own. The first list is seed list 1 (delivery types 1-3).
    """
    resp = requests.get(f"{API_V1}/liste")
    assert resp.status_code == 200, f"Failed to list lists: {resp.text}"
    lists = resp.json()
    if not lists:
        pytest.skip("No lists available in test environment")
    _open_list_for_orders(lists[0]["id"])
    return lists[0]["id"]


def test_orders_create_public_success():
    list_id = _get_orderable_list_id_or_skip()
    payload = {
        "nume_client": f"John Doe {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
        "order_notes": "Leave at door",
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    # Order creation is now public - no auth required
    assert resp.status_code == 201, resp.text
    order = resp.json()
    assert order["nume_client"].startswith("John Doe ")
    assert order["liste_id"] == list_id
    assert order["delivery_type_id"] == 1
    assert order["payment_method_id"] == 5


def test_orders_create_public_and_read_with_auth():
    list_id = _get_orderable_list_id_or_skip()
    payload = {
        "nume_client": f"John Doe Auth {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    payload = {
        "nume_client": f"Jane Doe {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu (pickup)
        "payment_method_id": 7,  # Transfer Bancar
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201
    order_id = resp.json()["id"]

    # List without auth
    resp = requests.get(f"{API_V1}/orders/")
    # No Authorization header → HTTPBearer returns 401
    assert resp.status_code == 401

    # Get without auth
    resp = requests.get(f"{API_V1}/orders/{order_id}")
    # No Authorization header → HTTPBearer returns 401
    assert resp.status_code == 401


def test_orders_endpoints_invalid_token_returns_401():
    # Invalid/garbled token should result in 401 from get_current_admin
    headers = {"Authorization": "Bearer invalid_token"}
    # List with invalid token
    resp = requests.get(f"{API_V1}/orders/", headers=headers)
    assert resp.status_code == 401


def test_orders_create_with_items_success():
    liste_id = _get_orderable_list_id_or_skip()

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
        "nume_client": f"Order With Items {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    assert created["nume_client"].startswith("Order With Items ")
    assert isinstance(created.get("items", []), list)
    assert len(created["items"]) == 1


@pytest.mark.parametrize("sent_price", [0, "catalogue + 1000", None])
def test_orders_create_stores_current_price_whatever_price_is_sent(sent_price):
    liste_id = _get_orderable_list_id_or_skip()

    products = requests.get(f"{API_V1}/products").json()
    if not products:
        pytest.skip("No products available in test environment")
    product = products[0]

    item = {
        "produse_id": product["id"],
        "cantitate_produs": 2,
        "unitati_id": product["unitati_id"],
    }
    if sent_price == "catalogue + 1000":
        item["pret_produs"] = product["pret"] + 1000
    elif sent_price is not None:
        item["pret_produs"] = sent_price

    payload = {
        "nume_client": f"Price Check {sent_price} {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": liste_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
        "items": [item],
    }

    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, resp.text
    stored = resp.json()["items"]
    assert len(stored) == 1
    assert stored[0]["pret_produs"] == product["pret"]
    assert stored[0]["cantitate_produs"] == 2


def _create_minimal_order_and_return_id():
    liste_id = _get_orderable_list_id_or_skip()

    payload = {
        "nume_client": f"Patch/Delete Target {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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


def test_orders_delete_soft_deletes_order():
    """Test that delete performs soft delete - order is marked as deleted but still exists"""
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    # Delete (soft delete)
    resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}")
    assert resp.status_code == 204, resp.text
    # Verify not found in normal listing (soft-deleted orders excluded by default)
    get_after = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}")
    assert get_after.status_code == 404, "Soft-deleted order should not be found without include_deleted"
    # Verify can be retrieved with include_deleted=True
    get_with_deleted = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}?include_deleted=true")
    assert get_with_deleted.status_code == 200, "Soft-deleted order should be found with include_deleted=true"
    deleted_order = get_with_deleted.json()
    assert deleted_order["is_deleted"] == True, "Order should be marked as deleted"
    # Verify not in list without include_deleted
    list_resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/")
    assert list_resp.status_code == 200
    order_ids = [o["id"] for o in list_resp.json()]
    assert order_id not in order_ids, "Soft-deleted order should not appear in normal listing"
    # Verify appears in list with include_deleted=True
    list_with_deleted = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?include_deleted=true")
    assert list_with_deleted.status_code == 200
    order_ids_with_deleted = [o["id"] for o in list_with_deleted.json()]
    assert order_id in order_ids_with_deleted, "Soft-deleted order should appear in listing with include_deleted=true"


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
    list_id = _get_orderable_list_id_or_skip()
    produse_id, unitati_id, pret = _discover_product_and_unit_or_skip()
    if not auth_utils.access_token:
        auth_utils.login()
    order_payload = {
        "nume_client": "Items Lifecycle",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    now = datetime.now(timezone.utc)
    iso = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # Create two orders
    for name in [f"Filter Alice {int(datetime.now(timezone.utc).timestamp()*1000)}", f"Filter Bob {int(datetime.now(timezone.utc).timestamp()*1000)}"]:
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
    list_id = _get_orderable_list_id_or_skip()
    payload = {
        "nume_client": f"Invalid Token Write {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    # Create order
    order_payload = {
        "nume_client": f"Validation Target {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    # Create
    payload = {
        "nume_client": f"Immutable List {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    
    # Test missing delivery_type_id
    payload_missing_delivery = {
        "nume_client": "Missing Delivery",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_missing_delivery)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    
    # Test missing payment_method_id
    payload_missing_payment = {
        "nume_client": "Missing Payment",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload_missing_payment)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_orders_create_with_home_delivery_requires_address():
    """Test that home delivery requires delivery address"""
    list_id = _get_orderable_list_id_or_skip()
    
    # Test home delivery without address (should fail)
    payload_home_no_address = {
        "nume_client": "Home Delivery No Address",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    
    list_id = _get_orderable_list_id_or_skip()
    
    # Create orders with different delivery and payment methods
    orders_data = [
        (1, 5),  # Sediu + Cash
        (2, 6),  # Punct fix + Card
        (3, 7),  # Domiciliu + Transfer
    ]
    
    for i, (dt_id, pm_id) in enumerate(orders_data):
        payload = {
        "nume_client": f"Filter Test {i+1} {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    
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
            "nume_client": f"Test Customer {phone} {int(datetime.now(timezone.utc).timestamp()*1000)}",
            "phone_number": phone,
            "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    
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
            "nume_client": f"Test Customer {phone} {int(datetime.now(timezone.utc).timestamp()*1000)}",
            "phone_number": phone,
            "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    
    # Test without phone_number field
    payload_no_phone = {
        "nume_client": "Customer Without Phone",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    
    list_id = _get_orderable_list_id_or_skip()
    
    # Create order with valid phone number
    payload = {
        "nume_client": "Update Test Customer",
        "phone_number": "+40712345678",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    
    # Test exactly 20 characters (should work)
    phone_20_chars = "12345678901234567890"  # 20 digits
    payload = {
        "nume_client": f"Max Length Test {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "phone_number": phone_20_chars,
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    list_id = _get_orderable_list_id_or_skip()
    
    # Test phone number with leading/trailing whitespace (should be trimmed)
    payload = {
        "nume_client": f"Whitespace Test {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "phone_number": "  40712345678  ",  # With spaces
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    liste_id = _get_orderable_list_id_or_skip()

    produse_id, unitati_id, pret = _discover_product_and_unit_or_skip()
    # Create oldest order
    older_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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
    newer_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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
    # Arrange two distinct lists; only one list is open for orders at a time
    list_resp = requests.get(f"{API_V1}/liste")
    assert list_resp.status_code == 200, list_resp.text
    lists = list_resp.json()
    if len(lists) < 2:
        pytest.skip("Need at least two lists to validate cross-list non-merge")
    list_a = lists[0]["id"]
    list_b = lists[1]["id"]

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    base_payload = {
        "nume_client": "Ștefan Same",
        "data_plasarii": now_iso,
        "delivery_type_id": 1,
        "payment_method_id": 5,
    }
    _open_list_for_orders(list_a)
    r_a = requests.post(f"{API_V1}/orders/", json={**base_payload, "liste_id": list_a})
    assert r_a.status_code == 201, r_a.text
    try:
        _open_list_for_orders(list_b)
        r_b = requests.post(f"{API_V1}/orders/", json={**base_payload, "liste_id": list_b})
        assert r_b.status_code == 201, r_b.text
    finally:
        # The other tests order from the first list
        _open_list_for_orders(list_a)

    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?merge_similar=true&nume_client=Stefan&limit=1000")
    assert resp.status_code == 200
    body = resp.json()
    names = [(o["nume_client"], o["liste_id"]) for o in body if o["nume_client"].lower().startswith("ștefan") or o["nume_client"].lower().startswith("ştefan")]
    # Expect two separate entries for the two lists
    lists_seen = {lid for _, lid in names}
    assert list_a in lists_seen and list_b in lists_seen

# ---------- Duplicate detection tests ----------

def test_orders_create_duplicate_without_items_returns_409():
    list_id = _get_orderable_list_id_or_skip()
    name = f"Dup No Items {int(datetime.now(timezone.utc).timestamp()*1000)}"
    payload = {
        "nume_client": name,
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,
        "payment_method_id": 5,
    }
    r1 = requests.post(f"{API_V1}/orders/", json=payload)
    assert r1.status_code == 201, r1.text
    r2 = requests.post(f"{API_V1}/orders/", json=payload)
    assert r2.status_code == 409, f"Expected 409 duplicate, got {r2.status_code}: {r2.text}"
    error_data = r2.json()
    assert "detail" in error_data, f"Expected detail in error response, got: {error_data}"
    detail = error_data["detail"]
    assert "error_code" in detail, f"Expected structured error, got: {detail}"
    assert detail["error_code"] == "DUPLICATE_ORDER", f"Expected DUPLICATE_ORDER, got: {detail.get('error_code')}"
    assert "order_id" in detail, f"Expected order_id in error, got: {detail}"
    assert "message" in detail, f"Expected message in error, got: {detail}"


def test_orders_create_duplicate_with_items_returns_409():
    list_id = _get_orderable_list_id_or_skip()
    # Discover a product
    prod_resp = requests.get(f"{API_V1}/products")
    assert prod_resp.status_code == 200, prod_resp.text
    products = prod_resp.json()
    if not products:
        pytest.skip("No products available in test environment")
    p = products[0]
    produse_id = p["id"]
    unitati_id = p["unitati_id"]
    pret = p["pret"]

    base = {
        "nume_client": f"Dup With Items {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,
        "payment_method_id": 5,
        "items": [
            {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 2, "unitati_id": unitati_id}
        ],
    }
    r1 = requests.post(f"{API_V1}/orders/", json=base)
    assert r1.status_code == 201, r1.text
    r2 = requests.post(f"{API_V1}/orders/", json=base)
    assert r2.status_code == 409, f"Expected 409 duplicate, got {r2.status_code}: {r2.text}"
    error_data = r2.json()
    assert "detail" in error_data, f"Expected detail in error response, got: {error_data}"
    detail = error_data["detail"]
    assert "error_code" in detail, f"Expected structured error, got: {detail}"
    assert detail["error_code"] == "DUPLICATE_ORDER", f"Expected DUPLICATE_ORDER, got: {detail.get('error_code')}"
    assert "order_id" in detail, f"Expected order_id in error, got: {detail}"


def test_orders_create_same_products_split_items_still_409():
    list_id = _get_orderable_list_id_or_skip()
    # Discover a product
    prod_resp = requests.get(f"{API_V1}/products")
    assert prod_resp.status_code == 200, prod_resp.text
    products = prod_resp.json()
    if not products:
        pytest.skip("No products available in test environment")
    p = products[0]
    produse_id = p["id"]
    unitati_id = p["unitati_id"]
    pret = p["pret"]

    name = f"Dup Split {int(datetime.now(timezone.utc).timestamp()*1000)}"
    base_one_line = {
        "nume_client": name,
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,
        "payment_method_id": 5,
        "items": [
            {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 2, "unitati_id": unitati_id}
        ],
    }
    r1 = requests.post(f"{API_V1}/orders/", json=base_one_line)
    assert r1.status_code == 201, r1.text

    split_lines = {
        **base_one_line,
        "items": [
            {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 1, "unitati_id": unitati_id},
            {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 1, "unitati_id": unitati_id},
        ],
    }
    r2 = requests.post(f"{API_V1}/orders/", json=split_lines)
    assert r2.status_code == 409, f"Expected 409 for split duplicate, got {r2.status_code}: {r2.text}"
    error_data = r2.json()
    assert "detail" in error_data, f"Expected detail in error response, got: {error_data}"
    detail = error_data["detail"]
    assert "error_code" in detail, f"Expected structured error, got: {detail}"
    assert detail["error_code"] == "DUPLICATE_ORDER", f"Expected DUPLICATE_ORDER, got: {detail.get('error_code')}"


def test_orders_create_different_quantities_returns_201():
    list_id = _get_orderable_list_id_or_skip()
    # Discover a product
    prod_resp = requests.get(f"{API_V1}/products")
    assert prod_resp.status_code == 200, prod_resp.text
    products = prod_resp.json()
    if not products:
        pytest.skip("No products available in test environment")
    p = products[0]
    produse_id = p["id"]
    unitati_id = p["unitati_id"]
    pret = p["pret"]

    name = f"Dup Different Qty {int(datetime.now(timezone.utc).timestamp()*1000)}"
    base_qty2 = {
        "nume_client": name,
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,
        "payment_method_id": 5,
        "items": [
            {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 2, "unitati_id": unitati_id}
        ],
    }
    r1 = requests.post(f"{API_V1}/orders/", json=base_qty2)
    assert r1.status_code == 201, r1.text

    base_qty3 = {
        **base_qty2,
        "items": [
            {"produse_id": produse_id, "pret_produs": pret, "cantitate_produs": 3, "unitati_id": unitati_id}
        ],
    }
    r2 = requests.post(f"{API_V1}/orders/", json=base_qty3)
    assert r2.status_code == 201, f"Expected 201 for different quantities, got {r2.status_code}: {r2.text}"


# ---------- Soft delete and restore tests ----------

def test_orders_soft_delete_and_restore():
    """Test soft delete and restore functionality"""
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    
    # 1. Verify order exists and is not deleted
    get_resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}")
    assert get_resp.status_code == 200
    order = get_resp.json()
    assert order["is_deleted"] == False, "New order should not be deleted"
    
    # 2. Soft delete the order
    delete_resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}")
    assert delete_resp.status_code == 204, "Delete should return 204"
    
    # 3. Verify order is soft-deleted
    get_deleted = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}?include_deleted=true")
    assert get_deleted.status_code == 200
    deleted_order = get_deleted.json()
    assert deleted_order["is_deleted"] == True, "Order should be marked as deleted"
    
    # 4. Verify order is excluded from normal listing
    list_resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/")
    assert list_resp.status_code == 200
    order_ids = [o["id"] for o in list_resp.json()]
    assert order_id not in order_ids, "Soft-deleted order should not appear in normal listing"
    
    # 5. Restore the order
    restore_resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order_id}/restore")
    assert restore_resp.status_code == 200, f"Restore should return 200, got {restore_resp.status_code}: {restore_resp.text}"
    restored_order = restore_resp.json()
    assert restored_order["is_deleted"] == False, "Restored order should not be marked as deleted"
    
    # 6. Verify order appears in normal listing again
    list_after_restore = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/")
    assert list_after_restore.status_code == 200
    order_ids_after = [o["id"] for o in list_after_restore.json()]
    assert order_id in order_ids_after, "Restored order should appear in normal listing"


def test_orders_restore_non_existent_order_returns_404():
    """Test that restoring a non-existent order returns 404"""
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Try to restore non-existent order
    restore_resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/999999/restore")
    assert restore_resp.status_code == 404, "Restoring non-existent order should return 404"


def test_orders_restore_not_deleted_order_returns_404():
    """Test that restoring an order that is not soft-deleted returns 404"""
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Try to restore order that is not deleted
    restore_resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order_id}/restore")
    assert restore_resp.status_code == 404, "Restoring non-deleted order should return 404"


def test_orders_update_soft_deleted_order_fails():
    """Test that updating a soft-deleted order fails"""
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Soft delete the order
    delete_resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}")
    assert delete_resp.status_code == 204
    
    # Try to update soft-deleted order
    update_resp = auth_utils.make_authenticated_request(
        "PATCH", 
        f"{API_V1}/orders/{order_id}",
        json={"nume_client": "Updated Name"}
    )
    assert update_resp.status_code == 400, "Updating soft-deleted order should return 400"
    assert "soft-deleted" in update_resp.text.lower(), "Error message should mention soft-deleted"


def test_orders_duplicate_detection_excludes_soft_deleted():
    """Test that duplicate detection excludes soft-deleted orders"""
    list_id = _get_orderable_list_id_or_skip()
    name = f"Dup Exclude Deleted {int(datetime.now(timezone.utc).timestamp()*1000)}"
    
    # Create first order
    payload = {
        "nume_client": name,
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,
        "payment_method_id": 5,
    }
    r1 = requests.post(f"{API_V1}/orders/", json=payload)
    assert r1.status_code == 201, r1.text
    order_id = r1.json()["id"]
    
    # Soft delete the order
    if not auth_utils.access_token:
        auth_utils.login()
    delete_resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}")
    assert delete_resp.status_code == 204
    
    # Try to create duplicate - should succeed because original is soft-deleted
    r2 = requests.post(f"{API_V1}/orders/", json=payload)
    assert r2.status_code == 201, f"Creating duplicate of soft-deleted order should succeed, got {r2.status_code}: {r2.text}"


def test_orders_include_deleted_parameter():
    """Test include_deleted parameter in list and get endpoints"""
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Soft delete the order
    delete_resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}")
    assert delete_resp.status_code == 204
    
    # Test list endpoint without include_deleted (default False)
    list_default = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/")
    assert list_default.status_code == 200
    order_ids_default = [o["id"] for o in list_default.json()]
    assert order_id not in order_ids_default, "Soft-deleted order should not appear without include_deleted"
    
    # Test list endpoint with include_deleted=True
    list_with_deleted = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?include_deleted=true")
    assert list_with_deleted.status_code == 200
    order_ids_with_deleted = [o["id"] for o in list_with_deleted.json()]
    assert order_id in order_ids_with_deleted, "Soft-deleted order should appear with include_deleted=true"
    
    # Test get endpoint without include_deleted (default False)
    get_default = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}")
    assert get_default.status_code == 404, "Soft-deleted order should not be found without include_deleted"
    
    # Test get endpoint with include_deleted=True
    get_with_deleted = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}?include_deleted=true")
    assert get_with_deleted.status_code == 200, "Soft-deleted order should be found with include_deleted=true"
    order = get_with_deleted.json()
    assert order["is_deleted"] == True, "Order should be marked as deleted"


def test_orders_hard_delete_permanently_removes_order():
    """Test that hard delete permanently removes the order"""
    order_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Hard delete the order
    delete_resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}?permanent=true")
    assert delete_resp.status_code == 204, "Hard delete should return 204"
    
    # Verify order is permanently gone (not found even with include_deleted)
    get_resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}?include_deleted=true")
    assert get_resp.status_code == 404, "Hard-deleted order should not be found even with include_deleted=true"
    
    # Verify not in list even with include_deleted
    list_with_deleted = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/?include_deleted=true")
    assert list_with_deleted.status_code == 200
    order_ids = [o["id"] for o in list_with_deleted.json()]
    assert order_id not in order_ids, "Hard-deleted order should not appear in any listing"


def test_orders_soft_delete_vs_hard_delete():
    """Test the difference between soft delete and hard delete"""
    # Create two orders
    order1_id = _create_minimal_order_and_return_id()
    order2_id = _create_minimal_order_and_return_id()
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Soft delete first order
    soft_delete_resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order1_id}")
    assert soft_delete_resp.status_code == 204
    
    # Hard delete second order
    hard_delete_resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order2_id}?permanent=true")
    assert hard_delete_resp.status_code == 204
    
    # Verify soft-deleted order can be restored
    restore_resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order1_id}/restore")
    assert restore_resp.status_code == 200, "Soft-deleted order should be restorable"
    
    # Verify hard-deleted order cannot be restored (doesn't exist)
    restore_hard_resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/{order2_id}/restore")
    assert restore_hard_resp.status_code == 404, "Hard-deleted order should not be restorable"


# ---------- Only the open list accepts orders ----------

def _post_minimal_order(list_id):
    payload = {
        "nume_client": f"Closed List {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    return requests.post(f"{API_V1}/orders/", json=payload)


def _assert_list_not_open(resp, list_id):
    # 400, not 409: the storefront treats an unknown 409 as a duplicate, i.e. as success
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    detail = resp.json()["detail"]
    assert detail["error_code"] == "LIST_NOT_OPEN", detail
    assert detail["list_id"] == list_id, detail


def test_orders_create_for_unpublished_list_returns_400():
    _, list_id = list_utils.create_entity(is_published=False)
    try:
        _assert_list_not_open(_post_minimal_order(list_id), list_id)
    finally:
        list_utils.delete_entity(list_id)


def test_orders_create_for_expired_list_returns_400():
    _, list_id = list_utils.create_entity_with_expiration("2020-01-02T00:00:00", date="2020-01-01")
    try:
        _assert_list_not_open(_post_minimal_order(list_id), list_id)
    finally:
        list_utils.delete_entity(list_id)


def test_orders_create_for_deleted_list_returns_400():
    _, list_id = list_utils.create_entity(is_published=True)
    list_utils.delete_entity(list_id)

    _assert_list_not_open(_post_minimal_order(list_id), list_id)


def test_orders_duplicate_of_an_order_placed_before_the_list_closed_returns_409():
    # The storefront retries a submission after a network error or 5xx and treats 409
    # DUPLICATE_ORDER as success, so a retry that lands after closing time must still be
    # recognised as the order it already placed, not refused as LIST_NOT_OPEN
    list_id = _get_orderable_list_id_or_skip()
    stamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    payload = {
        "nume_client": f"Retry After Close {stamp}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, resp.text

    list_utils.update_entity(list_id, is_published=False)
    try:
        resp = requests.post(f"{API_V1}/orders/", json=payload)
        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
        assert resp.json()["detail"]["error_code"] == "DUPLICATE_ORDER", resp.text

        # A new order for the closed list is still refused
        _assert_list_not_open(
            requests.post(f"{API_V1}/orders/", json={**payload, "nume_client": f"New After Close {stamp}"}),
            list_id,
        )
    finally:
        # The other tests order from this list
        _open_list_for_orders(list_id)
