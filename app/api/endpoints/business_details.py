from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.business_details import BusinessDetails, BusinessDetailsCreate, BusinessDetailsUpdate
from app.services.business_details import (
    create_business_details,
    delete_business_details,
    get_business_details_by_id,
    get_business_details,
    update_business_details,
)

router = APIRouter()


@router.get("/", response_model=List[BusinessDetails], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_business_details(
    skip: int = Query(0, ge=0, le=100, description="Number of items to skip (max 100)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """Get all business details with pagination support"""
    try:
        return get_business_details(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=BusinessDetails, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Business details created successfully"},
    409: {"description": "Business details record already exists"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_business_details_endpoint(business_details: BusinessDetailsCreate = Body(..., description="Business details data"), db: Session = Depends(get_db)):
    """Create a new business details record (fails with 409 if a record already exists)"""
    try:
        return create_business_details(db=db, business_details=business_details)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{business_details_id}", response_model=BusinessDetails, responses={
    200: {"description": "Successful response"},
    404: {"description": "Business details not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_business_details_by_id(
    business_details_id: int = Path(..., gt=0, description="The ID of the business details"),
    db: Session = Depends(get_db)
):
    """Get a specific business details record by ID"""
    try:
        return get_business_details_by_id(db=db, business_details_id=business_details_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/{business_details_id}", response_model=BusinessDetails, responses={
    200: {"description": "Business details updated successfully"},
    400: {"description": "Bad request, e.g. no valid fields to update"},
    404: {"description": "Business details not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_business_details_endpoint(
    business_details_id: int = Path(..., gt=0, description="The ID of the business details to update"),
    business_details: BusinessDetailsUpdate = Body(..., description="Updated business details data"),
    db: Session = Depends(get_db)
):
    """Update a business details record (PUT - full replacement)"""
    try:
        return update_business_details(db=db, business_details_id=business_details_id, business_details=business_details)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{business_details_id}", response_model=BusinessDetails, responses={
    200: {"description": "Business details updated successfully"},
    400: {"description": "Bad request, e.g. no valid fields to update"},
    404: {"description": "Business details not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def patch_business_details_endpoint(
    business_details_id: int = Path(..., gt=0, description="The ID of the business details to update"),
    business_details: BusinessDetailsUpdate = Body(..., description="Partial business details data"),
    db: Session = Depends(get_db)
):
    """Partially update a business details record (PATCH - only update provided fields)"""
    try:
        return update_business_details(db=db, business_details_id=business_details_id, business_details=business_details)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{business_details_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Business details deleted successfully"},
    404: {"description": "Business details not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_business_details_endpoint(
    business_details_id: int = Path(..., gt=0, description="The ID of the business details to delete"),
    db: Session = Depends(get_db)
):
    """Delete a business details record"""
    try:
        result = delete_business_details(db=db, business_details_id=business_details_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business details with ID {business_details_id} not found"
            )
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
