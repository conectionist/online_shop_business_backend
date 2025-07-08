from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.schemas.unitati import Unitat, UnitatCreate, UnitatUpdate
from app.services.unitati import (
    create_unitat,
    delete_unitat,
    get_unitat_by_id,
    get_unitati,
    update_unitat,
)

router = APIRouter()


@router.get("/", response_model=List[Unitat], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_unitati(
    skip: int = Query(0, ge=0, le=100, description="Number of items to skip (max 100)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """Get all units with pagination support"""
    try:
        unitati = get_unitati(db, skip=skip, limit=limit)
        return unitati
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=Unitat, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Unit created successfully"},
    400: {"description": "Bad request, e.g., duplicate unit"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_unitati(unitat: UnitatCreate, db: Session = Depends(get_db)):
    """Create a new unit"""
    try:
        return create_unitat(db=db, unitat=unitat)
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


@router.get("/{unitat_id}", response_model=Unitat, responses={
    200: {"description": "Successful response"},
    404: {"description": "Unit not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_unitat(
    unitat_id: int = Path(..., gt=0, description="The ID of the unit to retrieve"),
    db: Session = Depends(get_db)
):
    """Get a specific unit by ID"""
    try:
        db_unitat = get_unitat_by_id(db, unitat_id=unitat_id)
        if db_unitat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        return db_unitat
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


@router.put("/{unitat_id}", response_model=Unitat, responses={
    200: {"description": "Unit updated successfully"},
    400: {"description": "Bad request, e.g., duplicate unit name"},
    404: {"description": "Unit not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_unitati(
    unitat_id: int = Path(..., gt=0, description="The ID of the unit to update"),
    unitat: UnitatUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update an existing unit"""
    try:
        db_unitat = update_unitat(db=db, unitat_id=unitat_id, unitat=unitat)
        if db_unitat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        return db_unitat
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


@router.delete("/{unitat_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Unit deleted successfully"},
    404: {"description": "Unit not found"},
    409: {"description": "Conflict, unit is in use"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_unitati(
    unitat_id: int = Path(..., gt=0, description="The ID of the unit to delete"),
    db: Session = Depends(get_db)
):
    """Delete a unit"""
    try:
        result = delete_unitat(db=db, unitat_id=unitat_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        return None
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete unit because it is in use by at least one product."
        )
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
