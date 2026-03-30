from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from fastapi.responses import Response
from app.core.cache import build_cache_key, get_cached_response, set_cached_response, invalidate_for_reference_data
from app.services.auth import get_current_admin_from_cookie
from app.models.admin import Admin
from app.schemas.unitati import Unit, UnitCreate, UnitUpdate
from app.services.unitati import (
    create_unit,
    delete_unit,
    get_unit_by_id,
    get_units,
    update_unit,
)

router = APIRouter()


@router.get("/", response_model=List[Unit], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_units(
    skip: int = Query(0, ge=0, le=100, description="Number of items to skip (max 100)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """Get all units with pagination support"""
    cache_key = build_cache_key("unitati_list", skip=skip, limit=limit)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="application/json", headers={"X-Cache": "HIT"})

    try:
        units = get_units(db, skip=skip, limit=limit)
        serialized = [Unit.model_validate(u, from_attributes=True).model_dump() for u in units]
        set_cached_response(cache_key, serialized)
        return units
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=Unit, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Unit created successfully"},
    400: {"description": "Bad request, e.g., duplicate unit"},
    401: {"description": "Unauthorized - Authentication required"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_units(
    unit: UnitCreate, 
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Create a new unit"""
    try:
        created = create_unit(db=db, unit=unit)
        invalidate_for_reference_data("unitati")
        return created
    except HTTPException:
        # Re-raise HTTP exceptions from the service layer
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{unit_id}", response_model=Unit, responses={
    200: {"description": "Successful response"},
    404: {"description": "Unit not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_unit(
    unit_id: int = Path(..., gt=0, description="The ID of the unit to retrieve"),
    db: Session = Depends(get_db)
):
    """Get a specific unit by ID"""
    cache_key = build_cache_key("unitati_detail", unit_id=unit_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="application/json", headers={"X-Cache": "HIT"})

    try:
        db_unit = get_unit_by_id(db, unit_id=unit_id)
        if db_unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        serialized = Unit.model_validate(db_unit, from_attributes=True).model_dump()
        set_cached_response(cache_key, serialized)
        return db_unit
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/{unit_id}", response_model=Unit, responses={
    200: {"description": "Unit updated successfully"},
    400: {"description": "Bad request, e.g., duplicate unit name"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Unit not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_units(
    unit_id: int = Path(..., gt=0, description="The ID of the unit to update"),
    unit: UnitUpdate = ...,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Update an existing unit (PUT - full replacement)"""
    try:
        db_unit = update_unit(db=db, unit_id=unit_id, unit=unit)
        if db_unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        invalidate_for_reference_data("unitati")
        return db_unit
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{unit_id}", response_model=Unit, responses={
    200: {"description": "Unit updated successfully"},
    400: {"description": "Bad request, e.g., duplicate unit name"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Unit not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def patch_units(
    unit_id: int = Path(..., gt=0, description="The ID of the unit to update"),
    unit: UnitUpdate = ...,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Partially update an existing unit (PATCH - only update provided fields)"""
    try:
        db_unit = update_unit(db=db, unit_id=unit_id, unit=unit)
        if db_unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        invalidate_for_reference_data("unitati")
        return db_unit
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Unit deleted successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Unit not found"},
    409: {"description": "Conflict, unit is in use"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_units(
    unit_id: int = Path(..., gt=0, description="The ID of the unit to delete"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """Delete a unit"""
    try:
        result = delete_unit(db=db, unit_id=unit_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        invalidate_for_reference_data("unitati")
        return None
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
