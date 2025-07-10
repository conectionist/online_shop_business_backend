from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
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
    try:
        units = get_units(db, skip=skip, limit=limit)
        return units
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=Unit, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Unit created successfully"},
    400: {"description": "Bad request, e.g., duplicate unit"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_units(unit: UnitCreate, db: Session = Depends(get_db)):
    """Create a new unit"""
    try:
        return create_unit(db=db, unit=unit)
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
    try:
        db_unit = get_unit_by_id(db, unit_id=unit_id)
        if db_unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
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
    404: {"description": "Unit not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_units(
    unit_id: int = Path(..., gt=0, description="The ID of the unit to update"),
    unit: UnitUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update an existing unit"""
    try:
        db_unit = update_unit(db=db, unit_id=unit_id, unit=unit)
        if db_unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
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
    404: {"description": "Unit not found"},
    409: {"description": "Conflict, unit is in use"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_units(
    unit_id: int = Path(..., gt=0, description="The ID of the unit to delete"),
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
