import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from fastapi.responses import JSONResponse
from app.core.cache import build_cache_key, get_cached_response, set_cached_response, invalidate_for_reference_data
from app.services.auth import get_current_admin_from_cookie
from app.models.admin import Admin
from app.schemas.delivery_schedule import DeliverySchedule, DeliveryScheduleCreate, DeliveryScheduleUpdate
from app.services.delivery_schedule import (
    create_delivery_schedule,
    delete_delivery_schedule,
    get_delivery_schedule_by_id,
    get_delivery_schedules,
    update_delivery_schedule,
)

router = APIRouter()


@router.get("/", response_model=List[DeliverySchedule], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_delivery_schedules(
    skip: int = Query(0, ge=0, le=100, description="Number of items to skip (max 100)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """Get all delivery schedules with pagination support"""
    cache_key = build_cache_key("delivery_schedules_list", skip=skip, limit=limit)
    cached = get_cached_response(cache_key)
    if cached is not None:
        try:
            payload = json.loads(cached)
            validated_payload = [
                DeliverySchedule.model_validate(item).model_dump()
                for item in payload
            ]
            return JSONResponse(content=validated_payload, headers={"X-Cache": "HIT"})
        except Exception:
            pass

    try:
        delivery_schedules = get_delivery_schedules(db, skip=skip, limit=limit)
        payload = [DeliverySchedule.model_validate(ds, from_attributes=True).model_dump() for ds in delivery_schedules]
        set_cached_response(cache_key, payload)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=DeliverySchedule, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Delivery schedule created successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_delivery_schedule_endpoint(
    delivery_schedule: DeliveryScheduleCreate, 
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Create a new delivery schedule"""
    try:
        created = create_delivery_schedule(db=db, delivery_schedule=delivery_schedule)
        invalidate_for_reference_data("delivery_schedules")
        return created
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{delivery_schedule_id}", response_model=DeliverySchedule, responses={
    200: {"description": "Successful response"},
    404: {"description": "Delivery schedule not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_delivery_schedule(
    delivery_schedule_id: int = Path(..., gt=0, description="The ID of the delivery schedule"),
    db: Session = Depends(get_db)
):
    """Get a specific delivery schedule by ID"""
    cache_key = build_cache_key("delivery_schedules_detail", delivery_schedule_id=delivery_schedule_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        try:
            payload = json.loads(cached)
            validated_payload = DeliverySchedule.model_validate(payload).model_dump()
            return JSONResponse(content=validated_payload, headers={"X-Cache": "HIT"})
        except Exception:
            pass

    try:
        delivery_schedule = get_delivery_schedule_by_id(db=db, delivery_schedule_id=delivery_schedule_id)
        if delivery_schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery schedule with ID {delivery_schedule_id} not found",
            )
        payload = DeliverySchedule.model_validate(delivery_schedule, from_attributes=True).model_dump()
        set_cached_response(cache_key, payload)
        return payload
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/{delivery_schedule_id}", response_model=DeliverySchedule, responses={
    200: {"description": "Delivery schedule updated successfully"},
    400: {"description": "Bad request, no valid fields to update"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Delivery schedule not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_delivery_schedule_endpoint(
    delivery_schedule_id: int = Path(..., gt=0, description="The ID of the delivery schedule to update"),
    delivery_schedule: DeliveryScheduleUpdate = ...,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Update a delivery schedule (PUT - full replacement)"""
    try:
        updated = update_delivery_schedule(
            db=db, 
            delivery_schedule_id=delivery_schedule_id, 
            delivery_schedule=delivery_schedule
        )
        invalidate_for_reference_data("delivery_schedules")
        return updated
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{delivery_schedule_id}", response_model=DeliverySchedule, responses={
    200: {"description": "Delivery schedule updated successfully"},
    400: {"description": "Bad request, e.g., no valid fields to update"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Delivery schedule not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def patch_delivery_schedule(
    delivery_schedule_id: int = Path(..., gt=0, description="The ID of the delivery schedule to update"),
    delivery_schedule: DeliveryScheduleUpdate = ...,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Partially update a delivery schedule (PATCH - only update provided fields)"""
    try:
        updated = update_delivery_schedule(
            db=db, 
            delivery_schedule_id=delivery_schedule_id, 
            delivery_schedule=delivery_schedule
        )
        invalidate_for_reference_data("delivery_schedules")
        return updated
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{delivery_schedule_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Delivery schedule deleted successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Delivery schedule not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_delivery_schedule_endpoint(
    delivery_schedule_id: int = Path(..., gt=0, description="The ID of the delivery schedule to delete"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Delete a delivery schedule"""
    try:
        result = delete_delivery_schedule(db=db, delivery_schedule_id=delivery_schedule_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery schedule with ID {delivery_schedule_id} not found"
            )
        invalidate_for_reference_data("delivery_schedules")
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
