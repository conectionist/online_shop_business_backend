from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from fastapi.responses import Response
from app.core.cache import build_cache_key, get_cached_response, set_cached_response, invalidate_for_reference_data
from app.services.auth import get_current_admin_from_cookie
from app.models.admin import Admin
from app.schemas.delivery_type import DeliveryType, DeliveryTypeCreate, DeliveryTypeUpdate
from app.services.delivery_type import (
    create_delivery_type,
    delete_delivery_type,
    get_delivery_type_by_id,
    get_delivery_types,
    update_delivery_type,
    reorder_delivery_types,
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
    cache_key = build_cache_key("delivery_types_list", skip=skip, limit=limit)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="application/json", headers={"X-Cache": "HIT"})

    try:
        delivery_types = get_delivery_types(db, skip=skip, limit=limit)
        serialized = [DeliveryType.model_validate(dt, from_attributes=True).model_dump() for dt in delivery_types]
        set_cached_response(cache_key, serialized)
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
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Create a new delivery type"""
    try:
        created = create_delivery_type(db=db, delivery_type=delivery_type)
        invalidate_for_reference_data("delivery_types")
        return created
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/reorder", response_model=List[DeliveryType], responses={
    200: {"description": "Reordered successfully; returns the ordered list"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "One or more delivery types not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def reorder_delivery_types_endpoint(
    ordered_ids: List[int] = Body(..., min_items=1, description="Full ordered list of delivery type IDs"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Atomically reorder delivery types by providing the full ordered list of IDs."""
    try:
        reordered = reorder_delivery_types(db=db, ordered_ids=ordered_ids)
        invalidate_for_reference_data("delivery_types")
        return reordered
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
    cache_key = build_cache_key("delivery_types_detail", delivery_type_id=delivery_type_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="application/json", headers={"X-Cache": "HIT"})

    try:
        delivery_type = get_delivery_type_by_id(db=db, delivery_type_id=delivery_type_id)
        serialized = DeliveryType.model_validate(delivery_type, from_attributes=True).model_dump()
        set_cached_response(cache_key, serialized)
        return delivery_type
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
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Update a delivery type (PUT - full replacement)"""
    try:
        updated = update_delivery_type(db=db, delivery_type_id=delivery_type_id, delivery_type=delivery_type)
        invalidate_for_reference_data("delivery_types")
        return updated
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
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Partially update a delivery type (PATCH - only update provided fields)"""
    try:
        updated = update_delivery_type(db=db, delivery_type_id=delivery_type_id, delivery_type=delivery_type)
        invalidate_for_reference_data("delivery_types")
        return updated
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
    current_admin: Admin = Depends(get_current_admin_from_cookie),
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
        invalidate_for_reference_data("delivery_types")
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/reorder", response_model=List[DeliveryType], responses={
    200: {"description": "Reordered successfully; returns the ordered list"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "One or more delivery types not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def reorder_delivery_types_endpoint(
    ordered_ids: List[int] = Body(..., min_items=1, description="Full ordered list of delivery type IDs"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Atomically reorder delivery types by providing the full ordered list of IDs."""
    try:
        reordered = reorder_delivery_types(db=db, ordered_ids=ordered_ids)
        invalidate_for_reference_data("delivery_types")
        return reordered
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
