import os
import uuid
import xml.etree.ElementTree as ET

import pytest
import requests

from integration.test_utils import EntityTestUtils
from integration.test_lists_api import ListTestUtils
from integration.test_categories_api import CategoryTestUtils
from integration.test_products_api import ProductTestUtils, get_test_image_content
from integration.test_auth_utils import auth_utils

G = "{http://base.google.com/ns/1.0}"

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
FEED_URL = f"{API_BASE_URL}/api/v1/feeds/google.xml"
LISTE_URL = f"{API_BASE_URL}/api/v1/liste"
PRODUCTS_URL = f"{API_BASE_URL}/api/v1/products"

unit_utils = EntityTestUtils(entity_name="Unit", endpoint_path="unitati")
list_utils = ListTestUtils()
category_utils = CategoryTestUtils()
product_utils = ProductTestUtils()


def get_or_create_unit(name):
    """Return the ID of the unit called *name*, creating it if needed (names are unique)."""
    skip = 0
    while True:
        response = requests.get(f"{unit_utils.base_url}/?skip={skip}&limit=100")
        assert response.status_code == 200, response.text
        units = response.json()
        for unit in units:
            if unit["denumire"].lower() == name.lower():
                return unit["id"]
        if len(units) < 100:
            break
        skip += 100
    _, unit_id = unit_utils.create_entity(name)
    return unit_id


def create_product(category_id, unitati_id, cantitate, pret, with_image=True):
    _, product_id = product_utils.create_entity(
        category_id=category_id, unitati_id=unitati_id, cantitate=cantitate, pret=pret
    )
    if with_image:
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{product_utils.base_url}/{product_id}/images",
            files={"file": ("test_image.jpg", get_test_image_content(), "image/jpeg")},
        )
        assert response.status_code in (200, 201), f"Image upload failed: {response.text}"
    return product_id


def add_to_list(list_id, category_id, product_id, stoc_produs=None):
    payload = {} if stoc_produs is None else {"stoc_produs": stoc_produs}
    response = auth_utils.make_authenticated_request(
        "POST",
        f"{LISTE_URL}/{list_id}/categories/{category_id}/products/{product_id}",
        json=payload,
    )
    assert response.status_code == 201, response.text


def fetch_feed_items():
    response = requests.get(FEED_URL)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/xml")
    root = ET.fromstring(response.content)
    assert root.tag == "rss"
    return {item.findtext(f"{G}id"): item for item in root.iter("item")}


def fetch_offer(product_id):
    response = requests.get(f"{PRODUCTS_URL}/{product_id}/offer")
    assert response.status_code == 200, response.text
    return response.json()


def assert_offer_matches_feed_item(offer, item):
    """The storefront JSON-LD is built from the offer, so it must say what the feed says."""
    assert offer["availability"] == item.findtext(f"{G}availability")
    assert f"{offer['price']:.2f} {offer['currency']}" == item.findtext(f"{G}price")
    if offer["unit_pricing"] is None:
        assert item.find(f"{G}unit_pricing_measure") is None
    else:
        measure, base = offer["unit_pricing"]["measure"], offer["unit_pricing"]["base"]
        assert f"{measure['value']:g}{measure['unit']}" == item.findtext(f"{G}unit_pricing_measure")
        assert f"{base['value']:g}{base['unit']}" == item.findtext(f"{G}unit_pricing_base_measure")


def test_google_feed_lists_products_with_price_availability_and_unit_pricing():
    if not auth_utils.access_token:
        auth_utils.login()

    gr_unit = get_or_create_unit("gr")
    buc_unit = get_or_create_unit("buc")
    ml_unit = get_or_create_unit("ml")
    _, tray_unit = unit_utils.create_entity(f"Caserola de 250gr {str(uuid.uuid4())[:8]}")
    _, category_id = category_utils.create_entity(f"Feed Category {str(uuid.uuid4())[:8]}")

    by_weight = create_product(category_id, gr_unit, cantitate=600, pret=16)
    sold_out = create_product(category_id, buc_unit, cantitate=1, pret=11)
    not_listed_tray = create_product(category_id, tray_unit, cantitate=2, pret=18)
    bad_quantity = create_product(category_id, ml_unit, cantitate=1, pret=28)
    without_image = create_product(category_id, gr_unit, cantitate=500, pret=12, with_image=False)
    deleted = create_product(category_id, gr_unit, cantitate=500, pret=12)
    product_ids = [by_weight, sold_out, not_listed_tray, bad_quantity, without_image, deleted]

    _, list_id = list_utils.create_entity(is_published=True)
    try:
        add_to_list(list_id, category_id, by_weight)
        add_to_list(list_id, category_id, sold_out, stoc_produs=0)
        product_utils.delete_entity(deleted)

        items = fetch_feed_items()

        item = items[str(by_weight)]
        assert item.findtext(f"{G}price") == "16.00 RON"
        assert item.findtext(f"{G}availability") == "in_stock"
        assert item.findtext("link").endswith(f"/product/{by_weight}")
        assert item.findtext(f"{G}image_link").startswith(("http://", "https://"))
        assert item.findtext(f"{G}brand")
        assert item.findtext(f"{G}condition") == "new"
        assert item.findtext(f"{G}unit_pricing_measure") == "600g"
        assert item.findtext(f"{G}unit_pricing_base_measure") == "1kg"

        item = items[str(sold_out)]
        assert item.findtext(f"{G}availability") == "out_of_stock"
        assert item.find(f"{G}unit_pricing_measure") is None

        item = items[str(not_listed_tray)]
        assert item.findtext(f"{G}availability") == "out_of_stock"
        assert item.findtext(f"{G}unit_pricing_measure") == "500g"
        assert item.findtext(f"{G}unit_pricing_base_measure") == "1kg"

        # 1 ml for 28 lei is a data-entry mistake; no unit price is published for it
        assert items[str(bad_quantity)].find(f"{G}unit_pricing_measure") is None

        assert str(without_image) not in items
        assert str(deleted) not in items

        for product_id in (by_weight, sold_out, not_listed_tray, bad_quantity):
            assert_offer_matches_feed_item(fetch_offer(product_id), items[str(product_id)])
        assert fetch_offer(by_weight)["unit_pricing"] == {
            "measure": {"value": 600, "unit": "g"},
            "base": {"value": 1, "unit": "kg"},
        }
        # Deleted products are left out of the feed, so they have no offer either
        assert requests.get(f"{PRODUCTS_URL}/{deleted}/offer").status_code == 404
    finally:
        list_utils.delete_entity(list_id)
        for product_id in product_ids:
            if product_id != deleted:
                product_utils.delete_entity(product_id)


def test_google_feed_treats_expired_list_as_unavailable():
    if not auth_utils.access_token:
        auth_utils.login()

    gr_unit = get_or_create_unit("gr")
    _, category_id = category_utils.create_entity(f"Feed Category {str(uuid.uuid4())[:8]}")
    product_id = create_product(category_id, gr_unit, cantitate=500, pret=12)

    _, list_id = list_utils.create_entity_with_expiration("2020-01-02T00:00:00", date="2020-01-01")
    try:
        add_to_list(list_id, category_id, product_id)

        items = fetch_feed_items()

        assert items[str(product_id)].findtext(f"{G}availability") == "out_of_stock"
        assert fetch_offer(product_id)["availability"] == "out_of_stock"
    finally:
        list_utils.delete_entity(list_id)
        product_utils.delete_entity(product_id)


@pytest.mark.parametrize("unit_name, shared, cantitate, expected", [
    # A diacritic after the number's g or l is part of a word, not a unit
    ("Tava de 12 găluște", False, 1, None),
    ("Set 20 lămâi", False, 1, None),
    ("Pachet 2x400g", False, 1, (800, "g", "kg")),
    ("Borcan 1/2 kg", False, 1, (0.5, "kg", "kg")),
    # Two sizes in one name are ambiguous, so no unit price is published
    ("Cutie 2x250g + 1kg", False, 1, None),
    ("Sticla de 0,75l", False, 1, (0.75, "l", "l")),
    ("gr.", True, 600, (600, "g", "kg")),
    ("kg.", True, 1, (1, "kg", "kg")),
    ("kilograme", True, 2, (2, "kg", "kg")),
    ("mililitri", True, 500, (500, "ml", "l")),
    ("buc", True, 1, None),
])
def test_product_offer_unit_pricing(unit_name, shared, cantitate, expected):
    if not auth_utils.access_token:
        auth_utils.login()

    # Unit names are unique; container names get a suffix (hex has no unit letters)
    if shared:
        unit_id = get_or_create_unit(unit_name)
    else:
        _, unit_id = unit_utils.create_entity(f"{unit_name} {uuid.uuid4().hex[:8]}")
    _, category_id = category_utils.create_entity(f"Offer Category {str(uuid.uuid4())[:8]}")
    product_id = create_product(category_id, unit_id, cantitate=cantitate, pret=10, with_image=False)
    try:
        offer = fetch_offer(product_id)

        if expected is None:
            assert offer["unit_pricing"] is None
        else:
            value, unit, base_unit = expected
            assert offer["unit_pricing"] == {
                "measure": {"value": value, "unit": unit},
                "base": {"value": 1, "unit": base_unit},
            }
    finally:
        product_utils.delete_entity(product_id)


def test_product_offer_for_missing_product_is_not_found():
    assert requests.get(f"{PRODUCTS_URL}/999999999/offer").status_code == 404
