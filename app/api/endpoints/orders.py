from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.order import (
    Order as OrderSchema,
    OrderCreate,
    OrderUpdate,
    OrderItem as OrderItemSchema,
    OrderItemBase,
)
from app.services.order import (
    create_order,
    get_order_by_id,
    list_orders,
    update_order,
    delete_order,
    list_order_items,
    add_order_item,
    update_order_item,
    remove_order_item,
)
from app.schemas.order import OrderFilterParams


router = APIRouter()


@router.get("/", response_model=List[OrderSchema], responses={
    200: {"description": "List of orders"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"},
})
def read_orders(
    nume_client: Optional[str] = Query(None, description="Filter by customer name (substring)"),
    liste_id: Optional[int] = Query(None, gt=0, description="Filter by list ID"),
    data_plasarii_start: Optional[str] = Query(None, description="Start datetime (ISO 8601)"),
    data_plasarii_end: Optional[str] = Query(None, description="End datetime (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("data_plasarii", pattern="^(data_plasarii|nume_client|liste_id)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    filters = OrderFilterParams(
        nume_client=nume_client,
        liste_id=liste_id,
        data_plasarii_start=data_plasarii_start,
        data_plasarii_end=data_plasarii_end,
        skip=skip,
        limit=limit,
        sort_by=sort_by,  # type: ignore
        sort_order=sort_order,  # type: ignore
    )
    return list_orders(db=db, filters=filters)


@router.post("/", response_model=OrderSchema, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Order created"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized"},
    422: {"description": "Validation error"},
})
def create_order_endpoint(
    order_in: OrderCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create_order(db=db, order_in=order_in)


@router.get("/{order_id}", response_model=OrderSchema, responses={
    200: {"description": "Order details"},
    404: {"description": "Not found"},
    422: {"description": "Validation error"},
})
def read_order(
    order_id: int = Path(..., gt=0),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_order_by_id(db=db, order_id=order_id)


@router.patch("/{order_id}", response_model=OrderSchema, responses={
    200: {"description": "Order updated"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized"},
    404: {"description": "Not found"},
    422: {"description": "Validation error"},
})
def update_order_endpoint(
    order_id: int = Path(..., gt=0),
    order_update: OrderUpdate = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_order(db=db, order_id=order_id, order_update=order_update)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Order deleted"},
    401: {"description": "Unauthorized"},
    404: {"description": "Not found"},
    422: {"description": "Validation error"},
})
def delete_order_endpoint(
    order_id: int = Path(..., gt=0),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    deleted = delete_order(db=db, order_id=order_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found")
    return None


@router.get("/{order_id}/products", response_model=List[OrderItemSchema], responses={
    200: {"description": "Order items"},
    404: {"description": "Order not found"},
    422: {"description": "Validation error"},
})
def read_order_items(
    order_id: int = Path(..., gt=0),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # Ensure order exists (service validates, but making explicit 404 behavior consistent)
    _ = get_order_by_id(db=db, order_id=order_id)
    return list_order_items(db=db, order_id=order_id)


@router.post("/{order_id}/products", response_model=OrderItemSchema, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Item added"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized"},
    404: {"description": "Not found"},
    422: {"description": "Validation error"},
})
def add_order_item_endpoint(
    order_id: int = Path(..., gt=0),
    item_in: OrderItemBase = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return add_order_item(db=db, order_id=order_id, item_in=item_in)


@router.patch("/{order_id}/products/{produse_id}", response_model=OrderItemSchema, responses={
    200: {"description": "Item updated"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized"},
    404: {"description": "Not found"},
    422: {"description": "Validation error"},
})
def update_order_item_endpoint(
    order_id: int = Path(..., gt=0),
    produse_id: int = Path(..., gt=0),
    item_in: OrderItemBase = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_order_item(db=db, order_id=order_id, produse_id=produse_id, item_in=item_in)


@router.delete("/{order_id}/products/{produse_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Item removed"},
    401: {"description": "Unauthorized"},
    404: {"description": "Not found"},
    422: {"description": "Validation error"},
})
def remove_order_item_endpoint(
    order_id: int = Path(..., gt=0),
    produse_id: int = Path(..., gt=0),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    removed = remove_order_item(db=db, order_id=order_id, produse_id=produse_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    return None


