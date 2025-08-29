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


def test_orders_create_requires_auth():
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "John Doe",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "order_notes": "Leave at door",
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    # No Authorization header → HTTPBearer returns 403
    assert resp.status_code == 403


def test_orders_create_and_read_success_with_auth():
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "John Doe",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
        "order_notes": "Leave at door",
    }
    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, resp.text
    order = resp.json()
    order_id = order["id"]

    # List
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/")
    assert resp.status_code == 200
    assert any(o["id"] == order_id for o in resp.json())

    # Get details
    resp = auth_utils.make_authenticated_request("GET", f"{API_V1}/orders/{order_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


def test_orders_list_and_get_require_auth():
    # Create an order with auth to have an ID
    list_id = _get_any_list_id_or_skip()
    payload = {
        "nume_client": "Jane Doe",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": list_id,
    }
    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/", json=payload)
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

    create_resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/", json=payload)
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

    if not auth_utils.access_token:
        auth_utils.login()

    payload = {
        "nume_client": "Patch/Delete Target",
        "data_plasarii": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": liste_id,
    }
    resp = auth_utils.make_authenticated_request("POST", f"{API_V1}/orders/", json=payload)
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


