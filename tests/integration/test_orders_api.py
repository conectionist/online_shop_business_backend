from datetime import datetime
import os
import requests
from integration.test_auth_utils import auth_utils
import pytest


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{API_BASE_URL}/api/v1"


def _get_any_list_id_or_skip():
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
        "order_notes": "Leave at door",
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    # Order creation is now public - no auth required
    assert resp.status_code == 201, resp.text
    order = resp.json()
    assert order["nume_client"] == "John Doe"
    assert order["liste_id"] == list_id


def test_orders_create_public_and_read_with_auth():
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "John Doe",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
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
        payload = {"nume_client": name, "data_plasarii": iso, "liste_id": list_id}
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
