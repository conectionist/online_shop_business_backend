from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import unicodedata
import re
import logging

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy import and_, or_, asc, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.order import Order as OrderModel
from app.models.order_item import OrderItem as OrderItemModel
from app.models.product import Product
from app.models.list import List as ListModel
from app.models.list_product_ordered import ListProductOrdered
from app.models.unitati import Unitati
from app.models.delivery_type import DeliveryType
from app.models.modalitati_plata import ModalitatiPlata
from app.models.business_details import BusinessDetails
from app.core.config import settings
from app.schemas.order import (
    Order as OrderSchema,
    OrderCreate,
    OrderUpdate,
    OrderItemBase,
    OrderFilterParams,
)
logger = logging.getLogger(__name__)


def _format_order_for_debug(
    db: Session,
    order: OrderModel,
    items_count: int,
    source: Optional[str] = None,
) -> str:
    """Create a human-friendly multi-line representation of an order for debug logs.

    Includes names for related entities with their IDs in parentheses for traceability.
    """
    # Friendly names for related entities
    list_obj = db.query(ListModel).filter(ListModel.id == order.liste_id).first()
    list_friendly = None
    if list_obj:
        try:
            list_friendly = f"List {list_obj.data} (id={order.liste_id})"
        except Exception:
            list_friendly = f"List (id={order.liste_id})"
    else:
        list_friendly = f"List (id={order.liste_id})"

    delivery = db.query(DeliveryType).filter(DeliveryType.id == order.delivery_type_id).first()
    delivery_friendly = f"{getattr(delivery, 'denumire', 'Unknown')} (id={order.delivery_type_id})"

    payment = db.query(ModalitatiPlata).filter(ModalitatiPlata.id == order.payment_method_id).first()
    payment_friendly = f"{getattr(payment, 'name', 'Unknown')} (id={order.payment_method_id})"

    # Build items summary: "nume x qty unit (prod_id=X, unit_id=Y, price=Z)"
    items_lines: List[str] = []
    if getattr(order, 'items', None):
        for it in order.items:
            product = db.query(Product).filter(Product.id == it.produse_id).first()
            unit = db.query(Unitati).filter(Unitati.id == it.unitati_id).first()
            product_name = getattr(product, 'nume', 'Unknown')
            unit_name = getattr(unit, 'denumire', '')
            items_lines.append(
                f"- {product_name} x {int(it.cantitate_produs)} {unit_name} "
                f"(product_id={it.produse_id}, unit_id={it.unitati_id}, price={it.pret_produs})"
            )

    items_block = "\n".join(items_lines) if items_lines else "- (no items)"

    phone = getattr(order, 'phone_number', None) or "-"
    address = getattr(order, 'delivery_address', None) or "-"
    notes = getattr(order, 'order_notes', None) or "-"

    # Compose a readable block
    return (
        "\n"  # start on new line for nicer separation
        "Order Created\n"
        f"  ID: {order.id}\n"
        f"  Customer: {order.nume_client}\n"
        f"  Phone: {phone}\n"
        f"  Placed At: {order.data_plasarii}\n"
        f"  List: {list_friendly}\n"
        f"  Delivery: {delivery_friendly}\n"
        f"  Payment: {payment_friendly}\n"
        f"  Address: {address}\n"
        f"  Notes: {notes}\n"
        f"  Source: {source or '-'}\n"
        f"  Items ({items_count}):\n"
        f"{items_block}"
    )


 

def _compose_order_push_message_ro(
    db: Session,
    order: OrderModel,
    items_count: int,
) -> Dict[str, str]:
    """Compose a Romanian multi-line body similar to WhatsApp/UI order summary.

    Format example:
    John Doe
    3 x Gogoasa (21 RON)
    1 x Briose duble (10 RON)
    =======================
    Total: 31 RON
    Plata cash.
    Ridicare de la brutărie.
    28 octombrie 2025
    """
    def _format_price_ron(amount_bani: int) -> str:
        try:
            # Frontend expects whole-number RON values (no implicit cents scaling here)
            return f"{amount_bani} RON"
        except Exception:
            return "- RON"

    def _format_date_ro(d: datetime) -> str:
        luni = [
            "ianuarie", "februarie", "martie", "aprilie", "mai", "iunie",
            "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie",
        ]
        try:
            return f"{d.day} {luni[d.month - 1]} {d.year}"
        except Exception:
            return d.strftime("%d.%m.%Y")

    # Header: client name
    nume_client = (getattr(order, "nume_client", None) or "-").strip()

    # Items lines (line total in RON per item)
    items_lines: List[str] = []
    subtotal_ron = 0
    try:
        items = db.query(OrderItemModel).filter(OrderItemModel.comenzi_id == order.id).all()
        for it in items:
            product = db.query(Product).filter(Product.id == it.produse_id).first()
            product_name = getattr(product, 'nume', 'Produs')
            qty = int(getattr(it, 'cantitate_produs', 0) or 0)
            unit_price_ron = int(getattr(it, 'pret_produs', 0) or 0)
            line_total_ron = unit_price_ron * qty
            items_lines.append(f"{qty} x {product_name} ({_format_price_ron(line_total_ron)})")
            subtotal_ron += line_total_ron
    except Exception:
        pass

    separator = "======================="

    # Total line computed with optional delivery tax (added below)

    # Delivery tax from business details (RON)
    try:
        business = db.query(BusinessDetails).first()
        delivery_tax_ron = int(getattr(business, 'delivery_tax', 0) or 0)
    except Exception:
        delivery_tax_ron = 0

    # Apply delivery tax ONLY when an address is provided
    addr_for_tax = (getattr(order, 'delivery_address', None) or '').strip()
    apply_tax = bool(addr_for_tax)
    total_ron = subtotal_ron + (delivery_tax_ron if apply_tax else 0)

    # Payment line
    try:
        payment = db.query(ModalitatiPlata).filter(ModalitatiPlata.id == order.payment_method_id).first()
        payment_name = (getattr(payment, 'name', '') or '').strip()
        payment_line = f"Plata {payment_name.lower()}." if payment_name else "Plata -."
    except Exception:
        payment_line = "Plata -."

    # Delivery line
    try:
        delivery = db.query(DeliveryType).filter(DeliveryType.id == order.delivery_type_id).first()
        delivery_name = (getattr(delivery, 'denumire', '') or '').strip()
        addr = (getattr(order, 'delivery_address', None) or '').strip()
        if addr:
            delivery_line = f"Livrare la adresa: {addr}"
        else:
            delivery_line = f"{delivery_name}." if delivery_name else "-"
    except Exception:
        delivery_line = "-"

    # Date line (list date only; no fallback)
    date_line = None
    try:
        list_obj = db.query(ListModel).filter(ListModel.id == order.liste_id).first()
        list_date = getattr(list_obj, 'data', None)
        if isinstance(list_date, datetime):
            date_line = _format_date_ro(list_date)
        elif list_date:
            parsed = datetime.fromisoformat(str(list_date))
            date_line = _format_date_ro(parsed)
    except Exception:
        date_line = None

    # Build body
    phone_number = getattr(order, 'phone_number', None)
    notes = getattr(order, 'order_notes', None)

    body_lines: List[str] = [nume_client]
    body_lines.extend(items_lines)
    body_lines.append(separator)
    if apply_tax and delivery_tax_ron > 0:
        body_lines.append(f"Subtotal: {_format_price_ron(subtotal_ron)}")
        body_lines.append(f"Taxă livrare: {_format_price_ron(delivery_tax_ron)}")
    body_lines.append(f"Total: {_format_price_ron(total_ron)}")
    body_lines.append(payment_line)
    body_lines.append(delivery_line)
    if phone_number:
        body_lines.append(f"Telefon: {phone_number}")
    if notes:
        body_lines.append(f"Observații: {notes}")
    if date_line:
        body_lines.append(date_line)

    title = "Comandă nouă"
    body = "\n".join([line for line in body_lines if line])
    return {"title": title, "body": body}



def _format_order_failure_for_debug(
    db: Session,
    order_in: OrderCreate,
    status_code: int,
    reason: str,
    source: Optional[str] = None,
) -> str:
    """Create a human-friendly multi-line representation of a failed order creation attempt."""
    try:
        items = getattr(order_in, 'items', None) or []
        items_count = len(items)
    except Exception:
        items = []
        items_count = 0

    list_id = getattr(order_in, 'liste_id', None)
    list_friendly = f"List (id={list_id})"
    if list_id is not None:
        list_obj = db.query(ListModel).filter(ListModel.id == list_id).first()
        if list_obj:
            try:
                list_friendly = f"List {list_obj.data} (id={list_id})"
            except Exception:
                list_friendly = f"List (id={list_id})"

    delivery_id = getattr(order_in, 'delivery_type_id', None)
    delivery = db.query(DeliveryType).filter(DeliveryType.id == delivery_id).first() if delivery_id is not None else None
    delivery_friendly = f"{getattr(delivery, 'denumire', 'Unknown')} (id={delivery_id})" if delivery_id is not None else "-"

    payment_id = getattr(order_in, 'payment_method_id', None)
    payment = db.query(ModalitatiPlata).filter(ModalitatiPlata.id == payment_id).first() if payment_id is not None else None
    payment_friendly = f"{getattr(payment, 'name', 'Unknown')} (id={payment_id})" if payment_id is not None else "-"

    items_lines: List[str] = []
    for it in items:
        try:
            product = db.query(Product).filter(Product.id == it.produse_id).first()
            unit = db.query(Unitati).filter(Unitati.id == it.unitati_id).first()
            product_name = getattr(product, 'nume', 'Unknown')
            unit_name = getattr(unit, 'denumire', '')
            qty = int(it.cantitate_produs)
            price = getattr(it, 'pret_produs', None)
            price_str = f", price={price}" if price is not None else ""
            items_lines.append(
                f"- {product_name} x {qty} {unit_name} (product_id={it.produse_id}, unit_id={it.unitati_id}{price_str})"
            )
        except Exception:
            items_lines.append("- (unreadable item)")

    items_block = "\n".join(items_lines) if items_lines else "- (no items)"

    customer = None
    if getattr(order_in, 'nume_client', None) is not None:
        customer = str(order_in.nume_client).strip()
    phone = getattr(order_in, 'phone_number', None) or "-"
    address = getattr(order_in, 'delivery_address', None) or "-"
    notes = getattr(order_in, 'order_notes', None) or "-"

    return (
        "\n"
        f"Order Create Failed ({status_code})\n"
        f"  Reason: {reason}\n"
        f"  Customer: {customer}\n"
        f"  Phone: {phone}\n"
        f"  List: {list_friendly}\n"
        f"  Delivery: {delivery_friendly}\n"
        f"  Payment: {payment_friendly}\n"
        f"  Address: {address}\n"
        f"  Notes: {notes}\n"
        f"  Source: {source or '-'}\n"
        f"  Items ({items_count}):\n"
        f"{items_block}"
    )

 

def _apply_order_filters(query, filters: OrderFilterParams):
    if filters is None:
        return query
    if filters.nume_client:
        like_value = f"%{filters.nume_client}%"
        query = query.filter(OrderModel.nume_client.like(like_value))
    if filters.liste_id:
        query = query.filter(OrderModel.liste_id == filters.liste_id)
    if filters.delivery_type_id:
        query = query.filter(OrderModel.delivery_type_id == filters.delivery_type_id)
    if filters.payment_method_id:
        query = query.filter(OrderModel.payment_method_id == filters.payment_method_id)
    if filters.data_plasarii_start:
        query = query.filter(OrderModel.data_plasarii >= filters.data_plasarii_start)
    if filters.data_plasarii_end:
        query = query.filter(OrderModel.data_plasarii <= filters.data_plasarii_end)
    return query


def _apply_sorting(query, sort_by: str, sort_order: str):
    column = {
        "data_plasarii": OrderModel.data_plasarii,
        "nume_client": OrderModel.nume_client,
        "liste_id": OrderModel.liste_id,
        "delivery_type_id": OrderModel.delivery_type_id,
        "payment_method_id": OrderModel.payment_method_id,
    }.get(sort_by, OrderModel.data_plasarii)
    direction = desc if sort_order == "desc" else asc
    return query.order_by(direction(column))


def _validate_foreign_keys(db: Session, order_in: OrderCreate):
    # Check list exists
    list_obj = db.query(ListModel).filter(ListModel.id == order_in.liste_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"List with ID {order_in.liste_id} does not exist",
        )
    # Check delivery type exists
    if not db.query(DeliveryType).filter(DeliveryType.id == order_in.delivery_type_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery type with ID {order_in.delivery_type_id} does not exist",
        )
    # Check payment method exists
    if not db.query(ModalitatiPlata).filter(ModalitatiPlata.id == order_in.payment_method_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment method with ID {order_in.payment_method_id} does not exist",
        )
    # Validate each item FKs
    if order_in.items:
        for item in order_in.items:
            if not db.query(Product).filter(Product.id == item.produse_id).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {item.produse_id} does not exist",
                )
            if not db.query(Unitati).filter(Unitati.id == item.unitati_id).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unit with ID {item.unitati_id} does not exist",
                )


def _fill_missing_item_price(db: Session, item: OrderItemBase, liste_id: int) -> int:
    # If price is missing, fallback to product price (or overridden price if business rules later require)
    if item.pret_produs is not None:
        return item.pret_produs
    product = db.query(Product).filter(Product.id == item.produse_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {item.produse_id} not found")
    return product.pret


def _check_stock(db: Session, liste_id: int, produse_id: int, requested_qty: int):
    # Optional stock check: if stoc_produs exists and is not null, ensure sufficient stock
    lp = db.query(ListProductOrdered).filter(
        and_(
            ListProductOrdered.liste_id == liste_id,
            ListProductOrdered.produse_id == produse_id,
        )
    ).first()
    if lp and lp.stoc_produs is not None and requested_qty > lp.stoc_produs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "INSUFFICIENT_STOCK",
                "message": "Insufficient stock for product",
                "product_id": produse_id,
                "list_id": liste_id,
                "requested_quantity": requested_qty,
                "available_quantity": lp.stoc_produs,
            },
        )


def _validate_delivery_method_availability(db: Session, liste_id: int, delivery_type_id: int):
    """Validate that the selected delivery type is available for the specific list"""
    from app.models.list_delivery_type import ListDeliveryType
    
    # Check if the delivery type is available for this list
    list_delivery = db.query(ListDeliveryType).filter(
        and_(
            ListDeliveryType.liste_id == liste_id,
            ListDeliveryType.tipuri_livrare_id == delivery_type_id,
        )
    ).first()
    
    if not list_delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery type {delivery_type_id} is not available for list {liste_id}",
        )


def _validate_delivery_address(db: Session, delivery_type_id: int, delivery_address: Optional[str]):
    """Validate delivery address based on delivery type (frontend responsibility, but backend validation for consistency)"""
    from app.models.delivery_type import DeliveryType
    
    # Get delivery type to check if it requires address
    delivery_type = db.query(DeliveryType).filter(DeliveryType.id == delivery_type_id).first()
    if not delivery_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery type {delivery_type_id} not found",
        )
    
    # Check if delivery type name suggests home delivery (case-insensitive)
    delivery_name_lower = delivery_type.denumire.lower()
    home_delivery_keywords = ['acasa', 'domiciliu', 'home', 'livrare', 'delivery']
    
    is_home_delivery = any(keyword in delivery_name_lower for keyword in home_delivery_keywords)
    
    if is_home_delivery and not delivery_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery address is required for delivery type '{delivery_type.denumire}'",
        )


def _items_to_quantity_map(items: Optional[List[OrderItemBase]]) -> Dict[int, int]:
    """Build a product->quantity mapping from incoming order items.

    - Ignores price and unit when determining duplicates.
    - Treats None or empty list as an empty mapping.
    """
    quantity_by_product: Dict[int, int] = {}
    if not items:
        return quantity_by_product
    for it in items:
        # Sum quantities per product to be robust to potential duplicates in input
        quantity_by_product[it.produse_id] = quantity_by_product.get(it.produse_id, 0) + int(it.cantitate_produs)
    return quantity_by_product


def _existing_order_items_quantity_map(db: Session, order_id: int) -> Dict[int, int]:
    """Build a product->quantity mapping from an existing order's items."""
    quantity_by_product: Dict[int, int] = {}
    existing_items = db.query(OrderItemModel).filter(OrderItemModel.comenzi_id == order_id).all()
    for it in existing_items:
        quantity_by_product[it.produse_id] = quantity_by_product.get(it.produse_id, 0) + int(it.cantitate_produs)
    return quantity_by_product


def _is_duplicate_order(db: Session, order_in: OrderCreate) -> Optional[OrderModel]:
    """Check if an order already exists with same nume_client, liste_id, and identical items (by product and quantity).

    Returns the existing duplicate Order if found, otherwise None.
    """
    normalized_name = _normalize_name_for_matching(order_in.nume_client)
    incoming_items_map = _items_to_quantity_map(order_in.items)

    candidates: List[OrderModel] = (
        db.query(OrderModel)
        .filter(
            and_(
                OrderModel.liste_id == order_in.liste_id,
                # Match by normalized key using SQL LIKE on collapsed/stripped version.
                # Since we don't store a normalized column, fetch candidates by same list
                # and filter in Python using the same normalization.
                OrderModel.nume_client.isnot(None),
            )
        )
        .all()
    )

    # Filter by normalized name equality in Python
    for candidate in candidates:
        if _normalize_name_for_matching(candidate.nume_client) != normalized_name:
            continue
        existing_map = _existing_order_items_quantity_map(db, candidate.id)
        if existing_map == incoming_items_map:
            return candidate
    return None


def create_order(db: Session, order_in: OrderCreate, source: Optional[str] = None, background: BackgroundTasks | None = None) -> OrderModel:
    try:
        # Prepare items count for pretty summary after creation
        try:
            items_count = len(order_in.items) if order_in.items else 0
        except Exception:
            items_count = 0

        _validate_foreign_keys(db, order_in)
        
        # Validate delivery method availability for the selected list
        _validate_delivery_method_availability(db, order_in.liste_id, order_in.delivery_type_id)
        
        # Validate delivery address based on delivery type
        _validate_delivery_address(db, order_in.delivery_type_id, order_in.delivery_address)

        # Duplicate detection: same nume_client, same liste_id, and identical items (product and quantity)
        duplicate = _is_duplicate_order(db, order_in)
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "DUPLICATE_ORDER",
                    "message": "Duplicate order detected: an order with the same customer and items already exists",
                    "order_id": duplicate.id,
                },
            )

        db_order = OrderModel(
            nume_client=order_in.nume_client.strip(),
            phone_number=order_in.phone_number,
            data_plasarii=order_in.data_plasarii,
            liste_id=order_in.liste_id,
            delivery_type_id=order_in.delivery_type_id,
            payment_method_id=order_in.payment_method_id,
            delivery_address=order_in.delivery_address,
            order_notes=order_in.order_notes,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(db_order)
        db.flush()  # obtain order id for items

        if order_in.items:
            for item in order_in.items:
                _check_stock(db, order_in.liste_id, item.produse_id, item.cantitate_produs)
                price = _fill_missing_item_price(db, item, order_in.liste_id)
                db_item = OrderItemModel(
                    comenzi_id=db_order.id,
                    produse_id=item.produse_id,
                    pret_produs=price,
                    cantitate_produs=item.cantitate_produs,
                    unitati_id=item.unitati_id,
                )
                db.add(db_item)

        db.commit()
        db.refresh(db_order)

        # Fire-and-forget: notify admins subscribed to 'new_order' topic
        if background is not None:
            def _notify_new_order(order_id: int, items_count_inner: int):
                try:
                    from app.core.database import SessionLocal
                    from app.services.push_notifications import send_to_subscriptions_by_topic
                    session = SessionLocal()
                    try:
                        # Fetch order for summary details
                        order_obj = session.query(OrderModel).filter(OrderModel.id == order_id).first()
                        if order_obj is not None:
                            msg = _compose_order_push_message_ro(session, order_obj, items_count_inner)
                            title = msg["title"]
                            body = msg["body"]
                        else:
                            # Fallback minimal message
                            title = "Comandă nouă"
                            body = f"Comandă #{order_id} · {int(items_count_inner or 0)} produse"

                        # Compose frontend link:
                        # If both IDs are available: {FRONTEND_URL}/admin/lists/{list_id}/manage?tab=orders&highlight_order={order_id}
                        # Otherwise, fall back to lists root: {FRONTEND_URL}/admin/lists/
                        try:
                            list_id = int(getattr(order_obj, 'liste_id', 0) or 0)
                        except Exception:
                            list_id = 0
                        try:
                            order_id_int = int(order_id or 0)
                        except Exception:
                            order_id_int = 0
                        base_url = settings.FRONTEND_URL.rstrip('/')
                        if list_id > 0 and order_id_int > 0:
                            order_link = f"{base_url}/admin/lists/{list_id}/manage?tab=orders&highlight_order={order_id_int}"
                        else:
                            order_link = f"{base_url}/admin/lists/"

                        payload = {
                            "title": title,
                            "body": body,
                            "data": {"type": "new_order", "order_id": order_id, "url": order_link},
                            "tag": f"new_order_{order_id}",
                        }
                        send_to_subscriptions_by_topic(
                            session,
                            "new_order",
                            payload,
                            event_id=f"new_order_{order_id}"
                        )
                    finally:
                        session.close()
                except Exception:
                    # Best-effort; do not impact order creation
                    pass

            background.add_task(_notify_new_order, db_order.id, items_count)
        # Pretty multi-line info log with friendly names
        logger.info(_format_order_for_debug(db, db_order, items_count, source))
        return db_order
    except HTTPException as e:
        db.rollback()
        status_code = int(getattr(e, 'status_code', 500))
        level = logging.ERROR if status_code >= 500 else logging.WARNING
        logger.log(
            level,
            _format_order_failure_for_debug(
                db,
                order_in,
                status_code,
                str(getattr(e, 'detail', '')),
                source=source,
            ),
        )
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(
            _format_order_failure_for_debug(
                db,
                order_in,
                status_code=400,
                reason="Integrity error while creating order",
                source=source,
            )
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error while creating order")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            _format_order_failure_for_debug(
                db,
                order_in,
                status_code=500,
                reason=f"Database error: {str(e)}",
                source=source,
            )
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def get_order_by_id(db: Session, order_id: int) -> OrderModel:
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid order ID")
    try:
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found")
        return order
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def list_orders(db: Session, filters: Optional[OrderFilterParams] = None) -> List[OrderModel]:
    try:
        if filters is None:
            filters = OrderFilterParams()
        query = db.query(OrderModel)
        query = _apply_order_filters(query, filters)
        query = _apply_sorting(query, filters.sort_by, filters.sort_order)
        return query.offset(filters.skip).limit(filters.limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def _normalize_romanian(text: Optional[str]) -> str:
    if text is None:
        return ""
    # Lowercase and strip diacritics via NFD decomposition
    lowered = text.strip().lower()
    normalized = unicodedata.normalize('NFD', lowered)
    without_marks = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_marks


def _normalize_name_for_matching(text: Optional[str]) -> str:
    """Normalize names for matching:

    - Trim leading/trailing spaces
    - Lowercase and remove diacritics (Romanian included)
    - Collapse any internal whitespace runs to a single space
    """
    if text is None:
        return ""
    base = _normalize_romanian(text)
    # Collapse all Unicode whitespace to single ASCII space
    collapsed = re.sub(r"\s+", " ", base)
    return collapsed.strip()


def _merge_order_group(orders: List[OrderModel]) -> Dict[str, Any]:
    # Determine oldest and newest with business-oriented semantics
    # Oldest: by created_at (fallback to id)
    oldest = min(
        orders,
        key=lambda o: (
            (o.created_at or datetime.min),
            o.id or 0,
        )
    )
    # Newest: primarily by data_plasarii, then updated_at, then created_at, then id
    newest = max(
        orders,
        key=lambda o: (
            (o.data_plasarii or datetime.min),
            (o.updated_at or datetime.min),
            (o.created_at or datetime.min),
            o.id or 0,
        )
    )

    # Phone number rule
    phone_candidates = [o.phone_number for o in orders if o.phone_number]
    phone_number = None
    if phone_candidates:
        # Use newest non-empty phone (aligned with "if both, use the new one")
        newest_with_phone = max(
            (o for o in orders if o.phone_number),
            key=lambda o: (
                (o.data_plasarii or datetime.min),
                (o.updated_at or datetime.min),
                (o.created_at or datetime.min),
                o.id or 0,
            )
        )
        phone_number = newest_with_phone.phone_number

    # Order notes merge per rules
    def equals_notes(a: Optional[str], b: Optional[str]) -> bool:
        return _normalize_romanian(a) == _normalize_romanian(b) and a is not None and b is not None

    notes_present = [o for o in orders if o.order_notes]
    if not notes_present:
        order_notes = None
    else:
        # If multiple notes exist
        # Check if all notes are equal ignoring diacritics/case
        normalized_set = { _normalize_romanian(o.order_notes) for o in notes_present }
        if len(normalized_set) == 1:
            # Equal → use newest's note
            newest_with_note = max(
                notes_present,
                key=lambda o: (
                    (o.data_plasarii or datetime.min),
                    (o.updated_at or datetime.min),
                    (o.created_at or datetime.min),
                    o.id or 0,
                )
            )
            order_notes = newest_with_note.order_notes
        else:
            # Different → concatenate old first, new second (by created_at then updated_at then id)
            ordered = sorted(
                notes_present,
                key=lambda o: (
                    (o.created_at or datetime.min),
                    (o.updated_at or datetime.min),
                    o.id or 0,
                )
            )
            order_notes = " | ".join([o.order_notes for o in ordered if o.order_notes])

    # Items: aggregate identical items across orders by (produse_id, unitati_id, pret_produs)
    # Sum quantities to avoid duplicated lines when merging similar orders
    totals: Dict[Tuple[int, int, int], int] = {}
    for o in orders:
        for it in getattr(o, 'items', []) or []:
            key = (it.produse_id, it.unitati_id, it.pret_produs)
            totals[key] = totals.get(key, 0) + int(it.cantitate_produs)

    merged_items: List[Dict[str, Any]] = [
        {
            'produse_id': produse_id,
            'pret_produs': pret_produs,  # keep unit price
            'cantitate_produs': qty,
            'unitati_id': unitati_id,
        }
        for (produse_id, unitati_id, pret_produs), qty in totals.items()
    ]

    # Build merged dict matching Order schema
    merged: Dict[str, Any] = {
        'id': oldest.id,  # keep old one
        'nume_client': oldest.nume_client,  # keep original name spelling
        'phone_number': phone_number,
        'data_plasarii': newest.data_plasarii,  # use new one
        'liste_id': oldest.liste_id,  # same across group
        'delivery_type_id': newest.delivery_type_id,  # use new one
        'payment_method_id': newest.payment_method_id,  # use new one
        'delivery_address': newest.delivery_address,  # use new one
        'order_notes': order_notes,
        'created_at': oldest.created_at,  # keep old one
        'updated_at': newest.updated_at,  # use new one
        'items': merged_items,
    }
    return merged


def list_orders_merged(db: Session, filters: Optional[OrderFilterParams] = None) -> List[Dict[str, Any]]:
    """List orders and merge similar ones by (liste_id, normalized nume_client).

    Merging is performed only within the same list id to satisfy the caution requirement.
    """
    raw = list_orders(db=db, filters=filters)
    if not raw:
        return []

    groups: Dict[Tuple[int, str], List[OrderModel]] = {}
    for o in raw:
        key = (o.liste_id, _normalize_name_for_matching(o.nume_client))
        groups.setdefault(key, []).append(o)

    merged_results: List[Dict[str, Any]] = []
    for _, group_orders in groups.items():
        if len(group_orders) == 1:
            # Return as-is; rely on ORM dict via Pydantic by returning the model instance
            o = group_orders[0]
            merged_results.append({
                'id': o.id,
                'nume_client': o.nume_client,
                'phone_number': o.phone_number,
                'data_plasarii': o.data_plasarii,
                'liste_id': o.liste_id,
                'delivery_type_id': o.delivery_type_id,
                'payment_method_id': o.payment_method_id,
                'delivery_address': o.delivery_address,
                'order_notes': o.order_notes,
                'created_at': o.created_at,
                'updated_at': o.updated_at,
                'items': [
                    {
                        'produse_id': it.produse_id,
                        'pret_produs': it.pret_produs,  # keep unit price
                        'cantitate_produs': it.cantitate_produs,
                        'unitati_id': it.unitati_id,
                    } for it in getattr(o, 'items', []) or []
                ],
            })
        else:
            merged_results.append(_merge_order_group(group_orders))

    # Sort final results similar to default: by data_plasarii desc
    merged_results.sort(key=lambda d: d['data_plasarii'], reverse=True)
    # Apply pagination semantics if provided
    skip = filters.skip if filters else 0
    limit = filters.limit if filters else 100
    return merged_results[skip: skip + limit]

def update_order(db: Session, order_id: int, order_update: OrderUpdate) -> OrderModel:
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid order ID")
    update_data = order_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields to update")
    try:
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found")

        # Validate delivery method changes
        if "delivery_type_id" in update_data:
            _validate_delivery_method_availability(db, order.liste_id, update_data["delivery_type_id"])
        
        # Validate payment method changes
        if "payment_method_id" in update_data:
            if not db.query(ModalitatiPlata).filter(ModalitatiPlata.id == update_data["payment_method_id"]).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment method with ID {update_data['payment_method_id']} does not exist",
                )
        
        # Validate delivery address changes
        if "delivery_address" in update_data or "delivery_type_id" in update_data:
            delivery_type_id = update_data.get("delivery_type_id", order.delivery_type_id)
            delivery_address = update_data.get("delivery_address", order.delivery_address)
            _validate_delivery_address(db, delivery_type_id, delivery_address)

        if "nume_client" in update_data:
            update_data["nume_client"] = str(update_data["nume_client"]).strip()

        for key, value in update_data.items():
            setattr(order, key, value)
        db.commit()
        db.refresh(order)
        return order
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def delete_order(db: Session, order_id: int) -> bool:
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid order ID")
    try:
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            return False
        # Delete items then order (FK is NO ACTION)
        db.query(OrderItemModel).filter(OrderItemModel.comenzi_id == order_id).delete()
        db.delete(order)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def list_order_items(db: Session, order_id: int) -> List[OrderItemModel]:
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid order ID")
    try:
        return db.query(OrderItemModel).filter(OrderItemModel.comenzi_id == order_id).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def add_order_item(db: Session, order_id: int, item_in: OrderItemBase) -> OrderItemModel:
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid order ID")
    try:
        # Ensure order exists
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found")

        # Validate item FKs
        if not db.query(Product).filter(Product.id == item_in.produse_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {item_in.produse_id} not found")
        if not db.query(Unitati).filter(Unitati.id == item_in.unitati_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unit {item_in.unitati_id} not found")

        _check_stock(db, order.liste_id, item_in.produse_id, item_in.cantitate_produs)
        price = _fill_missing_item_price(db, item_in, order.liste_id)

        db_item = db.query(OrderItemModel).filter(
            and_(
                OrderItemModel.comenzi_id == order_id,
                OrderItemModel.produse_id == item_in.produse_id,
            )
        ).first()
        if db_item:
            # Update quantity/price/unit if already exists
            db_item.pret_produs = price
            db_item.cantitate_produs = item_in.cantitate_produs
            db_item.unitati_id = item_in.unitati_id
        else:
            db_item = OrderItemModel(
                comenzi_id=order_id,
                produse_id=item_in.produse_id,
                pret_produs=price,
                cantitate_produs=item_in.cantitate_produs,
                unitati_id=item_in.unitati_id,
            )
            db.add(db_item)

        db.commit()
        return db_item
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def update_order_item(db: Session, order_id: int, produse_id: int, item_in: OrderItemBase) -> OrderItemModel:
    if order_id <= 0 or produse_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid IDs")
    try:
        db_item = db.query(OrderItemModel).filter(
            and_(
                OrderItemModel.comenzi_id == order_id,
                OrderItemModel.produse_id == produse_id,
            )
        ).first()
        if not db_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")

        # Validate FKs
        if not db.query(Product).filter(Product.id == item_in.produse_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {item_in.produse_id} not found")
        if not db.query(Unitati).filter(Unitati.id == item_in.unitati_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unit {item_in.unitati_id} not found")

        _check_stock(db, db.query(OrderModel).get(order_id).liste_id, item_in.produse_id, item_in.cantitate_produs)

        db_item.pret_produs = item_in.pret_produs
        db_item.cantitate_produs = item_in.cantitate_produs
        db_item.unitati_id = item_in.unitati_id
        db.commit()
        return db_item
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


def remove_order_item(db: Session, order_id: int, produse_id: int) -> bool:
    if order_id <= 0 or produse_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid IDs")
    try:
        deleted = db.query(OrderItemModel).filter(
            and_(
                OrderItemModel.comenzi_id == order_id,
                OrderItemModel.produse_id == produse_id,
            )
        ).delete()
        if deleted == 0:
            return False
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


