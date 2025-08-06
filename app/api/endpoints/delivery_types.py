from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.delivery_type import DeliveryType, DeliveryTypeCreate, DeliveryTypeUpdate
from app.services.delivery_type import (
    create_delivery_type,
    delete_delivery_type,
    get_delivery_type_by_id,
    get_delivery_types,
    update_delivery_type,
)

router = APIRouter()


@router.get("/", response_model=List[DeliveryType], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_delivery_types(
    skip: int = Query(0, ge=0, le=100, description="Number of items to skip (max 100)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """Get all delivery types with pagination support"""
    try:
        delivery_types = get_delivery_types(db, skip=skip, limit=limit)
        return delivery_types
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=DeliveryType, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Delivery type created successfully"},
    400: {"description": "Bad request, e.g. duplicate delivery type"},
    401: {"description": "Unauthorized - Authentication required"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_delivery_type_endpoint(
    delivery_type: DeliveryTypeCreate, 
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new delivery type"""
    try:
        return create_delivery_type(db=db, delivery_type=delivery_type)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{delivery_type_id}", response_model=DeliveryType, responses={
    200: {"description": "Successful response"},
    404: {"description": "Delivery type not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_delivery_type(
    delivery_type_id: int = Path(..., gt=0, description="The ID of the delivery type"),
    db: Session = Depends(get_db)
):
    """Get a specific delivery type by ID"""
    try:
        return get_delivery_type_by_id(db=db, delivery_type_id=delivery_type_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/{delivery_type_id}", response_model=DeliveryType, responses={
    200: {"description": "Delivery type updated successfully"},
    400: {"description": "Bad request, e.g. duplicate delivery type or no valid fields"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Delivery type not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_delivery_type_endpoint(
    delivery_type_id: int = Path(..., gt=0, description="The ID of the delivery type to update"),
    delivery_type: DeliveryTypeUpdate = ...,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a delivery type (PUT - full replacement)"""
    try:
        return update_delivery_type(db=db, delivery_type_id=delivery_type_id, delivery_type=delivery_type)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{delivery_type_id}", response_model=DeliveryType, responses={
    200: {"description": "Delivery type updated successfully"},
    400: {"description": "Bad request, e.g., no valid fields to update"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Delivery type not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def patch_delivery_type_endpoint(
    delivery_type_id: int = Path(..., gt=0, description="The ID of the delivery type to update"),
    delivery_type: DeliveryTypeUpdate = ...,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Partially update a delivery type (PATCH - only update provided fields)"""
    try:
        return update_delivery_type(db=db, delivery_type_id=delivery_type_id, delivery_type=delivery_type)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{delivery_type_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Delivery type deleted successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Delivery type not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_delivery_type_endpoint(
    delivery_type_id: int = Path(..., gt=0, description="The ID of the delivery type to delete"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a delivery type"""
    try:
        result = delete_delivery_type(db=db, delivery_type_id=delivery_type_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery type with ID {delivery_type_id} not found"
            )
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
