from typing import List, Optional, Tuple
from datetime import datetime

from fastapi import HTTPException, status
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
from app.schemas.order import (
    Order as OrderSchema,
    OrderCreate,
    OrderUpdate,
    OrderItemBase,
    OrderFilterParams,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock for product {produse_id} in list {liste_id}",
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


def create_order(db: Session, order_in: OrderCreate) -> OrderModel:
    try:
        _validate_foreign_keys(db, order_in)
        
        # Validate delivery method availability for the selected list
        _validate_delivery_method_availability(db, order_in.liste_id, order_in.delivery_type_id)
        
        # Validate delivery address based on delivery type
        _validate_delivery_address(db, order_in.delivery_type_id, order_in.delivery_address)

        db_order = OrderModel(
            nume_client=order_in.nume_client.strip(),
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
        return db_order
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error while creating order")
    except SQLAlchemyError as e:
        db.rollback()
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


