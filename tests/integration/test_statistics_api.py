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


def test_statistics_compares_with_the_same_number_of_earlier_lists():
    _login()
    all_time = _get("statistics/overview")
    assert all_time.status_code == 200, all_time.text
    lists = all_time.json()["lists"]
    if len(lists) < 2:
        pytest.skip("Needs at least two lists with orders")

    start, end = lists[len(lists) // 2]["data"], lists[-1]["data"]
    current = [p for p in lists if start <= p["data"] <= end]
    first = lists.index(current[0])
    resp = _get("statistics/overview", start_date=start, end_date=end)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    period = body["period"]
    assert period["list_count"] == len(current)
    if first >= len(current):
        # The lists right before the range, however many days they span
        previous = lists[first - len(current):first]
        assert period["previous_list_count"] == len(current)
        assert period["previous_start_date"] == previous[0]["data"]
        assert period["previous_end_date"] == previous[-1]["data"]
        assert body["previous_summary"] is not None
    else:
        # Too few earlier lists for a like-for-like comparison
        assert period["previous_list_count"] == 0
        assert body["previous_summary"] is None


def test_statistics_range_without_lists_has_no_comparison():
    _login()
    resp = _get("statistics/overview", start_date="1990-01-01", end_date="1990-12-31")
    assert resp.status_code == 200, resp.text
    period = resp.json()["period"]
    assert period["list_count"] == 0
    assert period["previous_list_count"] == 0
    assert period["previous_start_date"] is None
    assert resp.json()["previous_summary"] is None
    # Dates far outside the calendar used to overflow the comparison window
    resp = _get("statistics/overview", start_date="0001-01-01", end_date="9999-12-31")
    assert resp.status_code == 200, resp.text


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
    try:
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
    finally:
        # Remove the order for good, even after a failed assertion, so it never skews
        # later tests or runs
        auth_utils.make_authenticated_request(
            "DELETE", f"{API_V1}/orders/{order_id}", params={"permanent": "true"}
        )


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
    for key in ("list", "orders", "revenue", "previous", "sold_out"):
        assert key in body
    # Only products that had orders count as sold out, most ordered first
    ordered = [item["ordered"] for item in body["sold_out"]]
    assert all(q > 0 for q in ordered)
    assert ordered == sorted(ordered, reverse=True)


def test_statistics_products_structure():
    _login()
    resp = _get("statistics/products")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    for key in ("top_by_quantity", "top_by_revenue", "categories", "unsold_products", "sell_outs"):
        assert key in body
    for item in body["sell_outs"]:
        assert 1 <= item["sold_out"] <= item["offered"]
    counts = [item["sold_out"] for item in body["sell_outs"]]
    assert counts == sorted(counts, reverse=True)
    # A product that sold out was ordered, so it is never listed as unsold
    sold_out_ids = {item["product_id"] for item in body["sell_outs"]}
    assert not sold_out_ids & {item["product_id"] for item in body["unsold_products"]}


def test_statistics_marking_an_ordered_product_unavailable_counts_as_sold_out():
    lst = _discover_list_or_skip()
    _login()
    resp = requests.get(f"{API_V1}/liste/{lst['id']}/products")
    assert resp.status_code == 200, resp.text
    available = [p for p in resp.json() if p.get("stoc_produs") != 0]
    if not available:
        pytest.skip("The list has no available products")
    product = available[0]
    availability_url = f"{API_V1}/liste/{lst['id']}/products/{product['id']}"
    period = {"start_date": lst["data"], "end_date": lst["data"]}

    order_id = _create_order(lst["id"], product, quantity=3)
    try:
        # The admin's toggle marks a sold-out product unavailable with stock 0
        resp = auth_utils.make_authenticated_request("PATCH", availability_url, json={"stoc_produs": 0})
        assert resp.status_code == 200, resp.text

        products = _get("statistics/products", **period)
        assert products.status_code == 200, products.text
        sell_out = next(p for p in products.json()["sell_outs"] if p["product_id"] == product["id"])
        assert sell_out["sold_out"] == 1
        assert sell_out["offered"] == 1

        current = _get("statistics/current-list")
        assert current.status_code == 200, current.text
        body = current.json()
        if body["list"] and body["list"]["id"] == lst["id"]:
            item = next(p for p in body["sold_out"] if p["product_id"] == product["id"])
            assert item["ordered"] >= 3
    finally:
        auth_utils.make_authenticated_request("PATCH", availability_url, json={"stoc_produs": product.get("stoc_produs")})
        auth_utils.make_authenticated_request(
            "DELETE", f"{API_V1}/orders/{order_id}", params={"permanent": "true"}
        )
