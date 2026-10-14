from datetime import datetime, timezone
import os

import pytest
import requests

from integration.test_auth_utils import auth_utils


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{API_BASE_URL}/api/v1"

STATS_ENDPOINTS = [
    "statistics/overview",
    "statistics/products",
    "statistics/customers",
    "statistics/current-list",
]


def _login():
    if not auth_utils.access_token:
        auth_utils.login()


def _get(path: str, **params):
    return auth_utils.make_authenticated_request("GET", f"{API_V1}/{path}", params=params)


def _discover_list_or_skip():
    resp = requests.get(f"{API_V1}/liste")
    assert resp.status_code == 200, resp.text
    lists = resp.json()
    if not lists:
        pytest.skip("No lists available in test environment")
    return lists[0]


def _discover_product_or_skip():
    resp = requests.get(f"{API_V1}/products")
    assert resp.status_code == 200, resp.text
    products = resp.json()
    if not products:
        pytest.skip("No products available in test environment")
    return products[0]


def _create_order(liste_id: int, product: dict, quantity: int) -> int:
    payload = {
        "nume_client": f"Stats Client {int(datetime.now(timezone.utc).timestamp()*1000)}",
        "data_plasarii": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "liste_id": liste_id,
        "delivery_type_id": 1,  # Ridicare de la sediu
        "payment_method_id": 5,  # Cash
        "items": [
            {
                "produse_id": product["id"],
                "pret_produs": product["pret"],
                "cantitate_produs": quantity,
                "unitati_id": product["unitati_id"],
            }
        ],
    }
    resp = requests.post(f"{API_V1}/orders/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.parametrize("path", STATS_ENDPOINTS)
def test_statistics_require_auth(path):
    resp = requests.get(f"{API_V1}/{path}")
    assert resp.status_code == 401, resp.text


def test_statistics_overview_structure():
    _login()
    resp = _get("statistics/overview")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    for key in ("period", "summary", "previous_summary", "lists", "delivery_types", "payment_methods", "heatmap"):
        assert key in body
    assert len(body["heatmap"]) == 7 * 24
    summary = body["summary"]
    assert summary["orders"] >= 0
    assert 0 <= summary["repeat_customer_rate"] <= 1
    # "All time" has no comparison period
    assert body["previous_summary"] is None
    # Lists come back in chronological order
    dates = [p["data"] for p in body["lists"]]
    assert dates == sorted(dates)


def test_statistics_date_range_has_comparison_period():
    _login()
    resp = _get("statistics/overview", start_date="2025-01-01", end_date="2025-01-31")
    assert resp.status_code == 200, resp.text
    period = resp.json()["period"]
    # The comparison period is the 31 days right before the range
    assert period["previous_start_date"] == "2024-12-01"
    assert period["previous_end_date"] == "2024-12-31"


def test_statistics_rejects_inverted_date_range():
    _login()
    resp = _get("statistics/products", start_date="2025-02-01", end_date="2025-01-01")
    assert resp.status_code == 400, resp.text


def test_statistics_order_lifecycle_updates_figures():
    lst = _discover_list_or_skip()
    product = _discover_product_or_skip()
    _login()
    period = {"start_date": lst["data"], "end_date": lst["data"]}

    before = _get("statistics/overview", **period)
    assert before.status_code == 200, before.text
    before_summary = before.json()["summary"]

    order_id = _create_order(lst["id"], product, quantity=2)
    expected_revenue = product["pret"] * 2

    after = _get("statistics/overview", **period)
    assert after.status_code == 200, after.text
    after_summary = after.json()["summary"]
    assert after_summary["orders"] == before_summary["orders"] + 1
    assert after_summary["revenue"] == before_summary["revenue"] + expected_revenue
    assert after_summary["items_sold"] == before_summary["items_sold"] + 2
    assert any(p["list_id"] == lst["id"] for p in after.json()["lists"])

    products = _get("statistics/products", limit=100, **period)
    assert products.status_code == 200, products.text
    assert any(p["product_id"] == product["id"] for p in products.json()["top_by_quantity"])

    # Soft-deleting the order removes it from revenue and counts it as cancelled
    resp = auth_utils.make_authenticated_request("DELETE", f"{API_V1}/orders/{order_id}")
    assert resp.status_code == 204, resp.text
    final = _get("statistics/overview", **period)
    assert final.status_code == 200, final.text
    final_summary = final.json()["summary"]
    assert final_summary["orders"] == before_summary["orders"]
    assert final_summary["revenue"] == before_summary["revenue"]
    assert final_summary["cancelled_orders"] == before_summary["cancelled_orders"] + 1


def test_statistics_customers_structure():
    _login()
    resp = _get("statistics/customers", start_date="2025-01-01")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body["top_customers"], list)
    revenues = [c["revenue"] for c in body["top_customers"]]
    assert revenues == sorted(revenues, reverse=True)
    orders = [c["orders"] for c in body["top_customers_by_orders"]]
    assert orders == sorted(orders, reverse=True)
    # Both rankings cover the same customers, so they are equally long
    assert len(body["top_customers_by_orders"]) == len(body["top_customers"])


def test_statistics_current_list_structure():
    _login()
    resp = _get("statistics/current-list")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    for key in ("list", "orders", "revenue", "previous", "stock", "sold_out_count", "low_stock_count"):
        assert key in body
    for item in body["stock"]:
        assert item["stock"] > 0
        assert item["remaining"] >= 0
