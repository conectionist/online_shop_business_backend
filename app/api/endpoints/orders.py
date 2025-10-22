from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, BackgroundTasks
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
    list_orders_merged,
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
    200: {
        "description": "List of orders with delivery and payment information",
        "content": {
            "application/json": {
                "example": [
                    {
                        "id": 1,
                        "nume_client": "John Doe",
                        "data_plasarii": "2024-01-15T10:30:00.000000Z",
                        "liste_id": 5,
                        "delivery_type_id": 2,
                        "payment_method_id": 1,
                        "delivery_address": "123 Main St, City",
                        "order_notes": "Please deliver in the morning",
                        "created_at": "2024-01-15T10:30:00.000000Z",
                        "updated_at": "2024-01-15T10:30:00.000000Z",
                        "items": [
                            {
                                "produse_id": 10,
                                "pret_produs": 1500,
                                "cantitate_produs": 2,
                                "unitati_id": 1
                            }
                        ]
                    }
                ]
            }
        }
    },
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"},
})
def read_orders(
    nume_client: Optional[str] = Query(None, description="Filter by customer name (substring)"),
    liste_id: Optional[int] = Query(None, gt=0, description="Filter by list ID"),
    delivery_type_id: Optional[int] = Query(None, gt=0, description="Filter by delivery type ID"),
    payment_method_id: Optional[int] = Query(None, gt=0, description="Filter by payment method ID"),
    data_plasarii_start: Optional[str] = Query(None, description="Start datetime (ISO 8601)"),
    data_plasarii_end: Optional[str] = Query(None, description="End datetime (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("data_plasarii", pattern="^(data_plasarii|nume_client|liste_id|delivery_type_id|payment_method_id)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    merge_similar: bool = Query(False, description="If true, merge similar orders within the same list by customer name."),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    filters = OrderFilterParams(
        nume_client=nume_client,
        liste_id=liste_id,
        delivery_type_id=delivery_type_id,
        payment_method_id=payment_method_id,
        data_plasarii_start=data_plasarii_start,
        data_plasarii_end=data_plasarii_end,
        skip=skip,
        limit=limit,
        sort_by=sort_by,  # type: ignore
        sort_order=sort_order,  # type: ignore
    )
    if merge_similar:
        return list_orders_merged(db=db, filters=filters)
    return list_orders(db=db, filters=filters)


@router.post("/", response_model=OrderSchema, status_code=status.HTTP_201_CREATED, responses={
    201: {
        "description": "Order created successfully with delivery and payment information",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "nume_client": "John Doe",
                    "data_plasarii": "2024-01-15T10:30:00.000000Z",
                    "liste_id": 5,
                    "delivery_type_id": 2,
                    "payment_method_id": 1,
                    "delivery_address": "123 Main St, City",
                    "order_notes": "Please deliver in the morning",
                    "created_at": "2024-01-15T10:30:00.000000Z",
                    "updated_at": "2024-01-15T10:30:00.000000Z",
                    "items": [
                        {
                            "produse_id": 10,
                            "pret_produs": 1500,
                            "cantitate_produs": 2,
                            "unitati_id": 1
                        }
                    ]
                }
            }
        }
    },
    400: {"description": "Bad request - validation failed (e.g., delivery type not available for list, missing address for home delivery)"},
    409: {"description": "Conflict - duplicate order detected (same customer, list, and items quantities)"},
    422: {"description": "Validation error - invalid input data"},
    500: {"description": "Internal server error"},
})
def create_order_endpoint(
    order_in: OrderCreate,
    source: Optional[str] = Query(None, max_length=50, description="Optional request source identifier (e.g., 'ProductPage', 'Cart', 'Admin')"),
    background: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Create a new order with delivery and payment method information.
    
    **Required Fields:**
    - `nume_client`: Customer name
    - `data_plasarii`: Order placement date
    - `liste_id`: List ID
    - `delivery_type_id`: Delivery method ID (must be available for the selected list)
    - `payment_method_id`: Payment method ID
    
    **Optional Fields:**
    - `delivery_address`: Required for home delivery types
    - `order_notes`: Additional order notes
    - `items`: List of order items
    
    **Business Rules:**
    - Delivery type must be available for the selected list
    - Delivery address is required for home delivery types
    - Payment method must exist in the system
    
    **Example Request Body:**
    ```json
    {
        "nume_client": "John Doe",
        "data_plasarii": "2024-01-15T10:30:00Z",
        "liste_id": 5,
        "delivery_type_id": 2,
        "payment_method_id": 1,
        "delivery_address": "123 Main St, City",
        "order_notes": "Please deliver in the morning",
        "items": [
            {
                "produse_id": 10,
                "pret_produs": 1500,
                "cantitate_produs": 2,
                "unitati_id": 1
            }
        ]
    }
    ```
    """
    # Pass the query source directly to the service for logging
    return create_order(db=db, order_in=order_in, source=source, background=background)


@router.get("/{order_id}", response_model=OrderSchema, responses={
    200: {
        "description": "Order details retrieved successfully with delivery and payment information",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "nume_client": "John Doe",
                    "data_plasarii": "2024-01-15T10:30:00.000000Z",
                    "liste_id": 5,
                    "delivery_type_id": 2,
                    "payment_method_id": 1,
                    "delivery_address": "123 Main St, City",
                    "order_notes": "Please deliver in the morning",
                    "created_at": "2024-01-15T10:30:00.000000Z",
                    "updated_at": "2024-01-15T10:30:00.000000Z",
                    "items": [
                        {
                            "produse_id": 10,
                            "pret_produs": 1500,
                            "cantitate_produs": 2,
                            "unitati_id": 1
                        }
                    ]
                }
            }
        }
    },
    404: {"description": "Order not found"},
    422: {"description": "Validation error - invalid order ID"},
    500: {"description": "Internal server error"},
})
def read_order(
    order_id: int = Path(..., gt=0),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific order by ID including delivery and payment method information.
    
    **Response includes:**
    - Order details (customer, date, list)
    - Delivery method information
    - Payment method information
    - Delivery address (if provided)
    - Order notes and timestamps
    """
    return get_order_by_id(db=db, order_id=order_id)


@router.patch("/{order_id}", response_model=OrderSchema, responses={
    200: {"description": "Order updated successfully"},
    400: {"description": "Bad request - validation failed (e.g., delivery type not available for list, missing address for home delivery)"},
    401: {"description": "Unauthorized"},
    404: {"description": "Order not found"},
    422: {"description": "Validation error - invalid input data"},
    500: {"description": "Internal server error"},
})
def update_order_endpoint(
    order_id: int = Path(..., gt=0),
    order_update: OrderUpdate = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Update an existing order with new delivery and payment method information.
    
    **Updatable Fields:**
    - `nume_client`: Customer name
    - `data_plasarii`: Order placement date
    - `liste_id`: List ID
    - `delivery_type_id`: Delivery method ID (must be available for the selected list)
    - `payment_method_id`: Payment method ID
    - `delivery_address`: Required for home delivery types
    - `order_notes`: Additional order notes
    
    **Business Rules:**
    - Delivery type must be available for the selected list
    - Delivery address is required for home delivery types
    - Payment method must exist in the system
    - All validations are applied when updating delivery-related fields
    
    **Example Request Body:**
    ```json
    {
        "delivery_type_id": 3,
        "delivery_address": "456 Oak Ave, Town",
        "order_notes": "Updated delivery instructions"
    }
    ```
    """
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


