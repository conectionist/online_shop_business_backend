"""Google Merchant Center product feed.

Builds an RSS 2.0 feed in Google's product data format, so Merchant Center can read
prices, availability and unit pricing without rendering the client-side storefront.
"""
import logging
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.image_versions import resolve_image_versions
from app.models.list import List
from app.models.list_product_ordered import ListProductOrdered
from app.models.product import Product
from app.utils.unit_pricing import get_unit_pricing

logger = logging.getLogger(__name__)

GOOGLE_NS = "http://base.google.com/ns/1.0"
ET.register_namespace("g", GOOGLE_NS)

# Matches the brand in the storefront's product JSON-LD (frontend src/utils/schema.ts)
BRAND_NAME = "Paine cu Maia de la Andreea"
CURRENCY = "RON"
SHOP_TIMEZONE = ZoneInfo("Europe/Bucharest")
MAX_ADDITIONAL_IMAGES = 10
PRODUCT_PLACEHOLDER_URL = "/api/v1/static/placeholders/product_placeholder.jpg"


def get_current_published_list(db: Session) -> Optional[List]:
    """Return the list customers can order from right now, or None.

    Mirrors listService.getPublishedList in the frontend: published, not deleted and
    not expired. expiration_date is stored as naive Romania-local time.
    """
    now_local = datetime.now(SHOP_TIMEZONE).replace(tzinfo=None)
    return (
        db.query(List)
        .filter(
            List.is_published == 1,
            List.is_deleted == 0,
            or_(List.expiration_date.is_(None), List.expiration_date > now_local),
        )
        .order_by(List.id.desc())
        .first()
    )


def _image_url(api_base_url: str, image_path: str) -> str:
    original = resolve_image_versions(image_path, placeholder_url=PRODUCT_PLACEHOLDER_URL)["original"]
    return f"{api_base_url}/api/v1/static/uploads/{original}"


def build_feed_items(db: Session, frontend_url: str, api_base_url: str) -> list[dict]:
    """Collect feed entries for every non-deleted product that has at least one image.

    Products in the current published list are in stock unless their list stock is 0;
    every other product is listed as out of stock so it stays approved between lists.
    """
    current_list = get_current_published_list(db)
    stock_by_product: dict[int, Optional[int]] = {}
    if current_list is not None:
        stock_by_product = {
            entry.produse_id: entry.stoc_produs
            for entry in db.query(ListProductOrdered).filter(ListProductOrdered.liste_id == current_list.id)
        }

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

        in_stock = product.id in stock_by_product and stock_by_product[product.id] != 0
        items.append({
            "id": str(product.id),
            "title": product.nume,
            "description": product.description or f"{product.nume} - produs proaspăt de brutărie cu maia",
            "link": f"{frontend_url}/product/{product.id}",
            "image_link": image_urls[0],
            "additional_image_links": image_urls[1:1 + MAX_ADDITIONAL_IMAGES],
            # pret is stored in whole lei (16 means 16 RON), not cents
            "price": f"{product.pret:.2f} {CURRENCY}",
            "availability": "in_stock" if in_stock else "out_of_stock",
            "product_type": product.category.name if product.category else None,
            "unit_pricing": get_unit_pricing(product.cantitate, product.unit.denumire if product.unit else None),
        })

    if skipped_without_image:
        logger.info("Product feed: skipped %d products without images", skipped_without_image)
    return items


def _add(parent: ET.Element, tag: str, text: Optional[str]) -> None:
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
            measure, base_measure = item["unit_pricing"]
            _add_g(entry, "unit_pricing_measure", measure)
            _add_g(entry, "unit_pricing_base_measure", base_measure)

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)
