"""Google Merchant Center product feed.

Builds an RSS 2.0 feed in Google's product data format, so Merchant Center can read
prices, availability and unit pricing without rendering the client-side storefront.
"""
import logging
import re
from typing import Iterable, Optional
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.constants import PLACEHOLDER_URL_BASE, UPLOADS_URL_BASE
from app.core.image_versions import resolve_image_versions
from app.models.list_product_ordered import ListProductOrdered
from app.models.product import Product
from app.services.list import get_current_published_list
from app.utils.unit_pricing import UnitPricing, get_unit_pricing

logger = logging.getLogger(__name__)

GOOGLE_NS = "http://base.google.com/ns/1.0"
ET.register_namespace("g", GOOGLE_NS)

# Matches the brand in the storefront's product JSON-LD (frontend src/utils/schema.ts)
BRAND_NAME = "Paine cu Maia de la Andreea"
CURRENCY = "RON"
MAX_ADDITIONAL_IMAGES = 10
PRODUCT_PLACEHOLDER_URL = f"{PLACEHOLDER_URL_BASE}/product_placeholder.jpg"

# Characters XML 1.0 forbids; ElementTree writes them out raw, and one of them in any
# product field would make Merchant Center reject the whole document
_XML_INVALID_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def get_current_stock(db: Session, product_ids: Optional[Iterable[int]] = None) -> dict[int, Optional[int]]:
    """Map product ID -> stock in the current published list (None means no limit).

    Products missing from the result are not in the current list. Empty when no
    list is published or the published list has expired.
    """
    current_list = get_current_published_list(db)
    if current_list is None:
        return {}
    query = db.query(ListProductOrdered).filter(ListProductOrdered.liste_id == current_list.id)
    if product_ids is not None:
        query = query.filter(ListProductOrdered.produse_id.in_(list(product_ids)))
    return {entry.produse_id: entry.stoc_produs for entry in query}


def get_availability(product_id: int, stock_by_product: dict[int, Optional[int]]) -> str:
    """Products in the current list are in stock unless their list stock is 0.

    Every other product is out of stock, so it stays approved between lists.
    """
    in_stock = product_id in stock_by_product and stock_by_product[product_id] != 0
    return "in_stock" if in_stock else "out_of_stock"


def _unit_pricing(product: Product) -> Optional[UnitPricing]:
    return get_unit_pricing(product.cantitate, product.unit.denumire if product.unit else None)


def build_product_offer(db: Session, product_id: int) -> Optional[dict]:
    """Price, availability and unit pricing of one product, computed as the feed computes them.

    The storefront builds its product JSON-LD from this, so Merchant Center finds the
    same values on the landing page as in the feed. Returns None for missing or
    deleted products, which the feed leaves out.
    """
    product = (
        db.query(Product)
        .options(joinedload(Product.unit))
        .filter(Product.id == product_id, Product.is_deleted == False)  # noqa: E712
        .first()
    )
    if product is None:
        return None

    unit_pricing = _unit_pricing(product)
    return {
        "product_id": product.id,
        "price": product.pret,
        "currency": CURRENCY,
        "availability": get_availability(product.id, get_current_stock(db, product_ids=[product.id])),
        "unit_pricing": None if unit_pricing is None else unit_pricing.offer_values(),
    }


def _image_url(api_base_url: str, image_path: str) -> str:
    original = resolve_image_versions(image_path, placeholder_url=PRODUCT_PLACEHOLDER_URL)["original"]
    return f"{api_base_url}{UPLOADS_URL_BASE}/{original}"


def build_feed_items(db: Session, frontend_url: str, api_base_url: str) -> list[dict]:
    """Collect feed entries for every non-deleted product that has at least one image."""
    stock_by_product = get_current_stock(db)

    products = (
        db.query(Product)
        .options(selectinload(Product.images), joinedload(Product.unit), joinedload(Product.category))
        .filter(Product.is_deleted == False)  # noqa: E712
        .order_by(Product.id)
        .all()
    )

    frontend_url = frontend_url.rstrip("/")
    items = []
    skipped_without_image = 0
    for product in products:
        image_urls = [_image_url(api_base_url, image.path) for image in product.images if image.path]
        if not image_urls:
            # Google rejects listings without a real product photo
            skipped_without_image += 1
            continue

        items.append({
            "id": str(product.id),
            "title": product.nume,
            "description": product.description or f"{product.nume} - produs proaspăt de brutărie cu maia",
            "link": f"{frontend_url}/product/{product.id}",
            "image_link": image_urls[0],
            "additional_image_links": image_urls[1:1 + MAX_ADDITIONAL_IMAGES],
            # pret is stored in whole lei (16 means 16 RON), not cents
            "price": f"{product.pret:.2f} {CURRENCY}",
            "availability": get_availability(product.id, stock_by_product),
            "product_type": product.category.name if product.category else None,
            "unit_pricing": _unit_pricing(product),
        })

    if skipped_without_image:
        logger.info("Product feed: skipped %d products without images", skipped_without_image)
    return items


def _add(parent: ET.Element, tag: str, text: Optional[str]) -> None:
    text = _XML_INVALID_CHARS.sub("", text) if text else text
    if text:
        ET.SubElement(parent, tag).text = text


def _add_g(parent: ET.Element, tag: str, text: Optional[str]) -> None:
    _add(parent, f"{{{GOOGLE_NS}}}{tag}", text)


def render_feed_xml(items: list[dict], frontend_url: str) -> bytes:
    """Render feed entries as an RSS 2.0 document with the Google (g:) namespace."""
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    _add(channel, "title", BRAND_NAME)
    _add(channel, "link", frontend_url.rstrip("/"))
    _add(channel, "description", f"Produse {BRAND_NAME}")

    for item in items:
        entry = ET.SubElement(channel, "item")
        _add_g(entry, "id", item["id"])
        _add(entry, "title", item["title"])
        _add(entry, "description", item["description"])
        _add(entry, "link", item["link"])
        _add_g(entry, "image_link", item["image_link"])
        for url in item["additional_image_links"]:
            _add_g(entry, "additional_image_link", url)
        _add_g(entry, "price", item["price"])
        _add_g(entry, "availability", item["availability"])
        _add_g(entry, "brand", BRAND_NAME)
        _add_g(entry, "condition", "new")
        _add_g(entry, "identifier_exists", "no")
        _add_g(entry, "product_type", item["product_type"])
        if item["unit_pricing"]:
            measure, base_measure = item["unit_pricing"].feed_values()
            _add_g(entry, "unit_pricing_measure", measure)
            _add_g(entry, "unit_pricing_base_measure", base_measure)

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)
