from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.modalitati_plata import (
    ModalitatePlata, 
    ModalitatePlataCreate, 
    ModalitatePlataUpdate
)
from app.services.modalitati_plata import (
    create_modalitate_plata,
    delete_modalitate_plata,
    get_modalitate_plata_by_id,
    get_modalitati_plata,
    update_modalitate_plata,
)

router = APIRouter()


@router.get("/", response_model=List[ModalitatePlata], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_modalitati_plata(
    skip: int = Query(0, ge=0, le=100, description="Number of items to skip (max 100)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """Get all payment methods with pagination support"""
    try:
        modalitati = get_modalitati_plata(db, skip=skip, limit=limit)
        return modalitati
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/", 
    response_model=ModalitatePlata, 
    status_code=status.HTTP_201_CREATED, 
    responses={
        201: {"description": "Payment method created successfully"},
        400: {"description": "Bad request, e.g., duplicate payment method"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
def create_modalitati_plata(
    modalitate: ModalitatePlataCreate, 
    db: Session = Depends(get_db)
):
    """Create a new payment method"""
    try:
        return create_modalitate_plata(db=db, modalitate=modalitate)
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


@router.get("/{modalitate_id}", response_model=ModalitatePlata, responses={
    200: {"description": "Successful response"},
    404: {"description": "Payment method not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_modalitate_plata(
    modalitate_id: int = Path(..., gt=0, description="The ID of the payment method to retrieve"),
    db: Session = Depends(get_db)
):
    """Get a specific payment method by ID"""
    try:
        db_modalitate = get_modalitate_plata_by_id(db, modalitate_id=modalitate_id)
        if db_modalitate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found"
            )
        return db_modalitate
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


@router.put("/{modalitate_id}", response_model=ModalitatePlata, responses={
    200: {"description": "Payment method updated successfully"},
    400: {"description": "Bad request, e.g., duplicate name"},
    404: {"description": "Payment method not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_modalitati_plata(
    modalitate_id: int = Path(..., gt=0, description="The ID of the payment method to update"),
    modalitate: ModalitatePlataUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update an existing payment method (PUT - full replacement)"""
    try:
        db_modalitate = update_modalitate_plata(
            db=db, 
            modalitate_id=modalitate_id, 
            modalitate=modalitate
        )
        
        if db_modalitate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found"
            )
            
        return db_modalitate
        
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


@router.patch("/{modalitate_id}", response_model=ModalitatePlata, responses={
    200: {"description": "Payment method updated successfully"},
    400: {"description": "Bad request, e.g., no valid fields to update"},
    404: {"description": "Payment method not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def patch_modalitati_plata(
    modalitate_id: int = Path(..., gt=0, description="The ID of the payment method to update"),
    modalitate: ModalitatePlataUpdate = ...,
    db: Session = Depends(get_db)
):
    """Partially update a payment method (PATCH - only update provided fields)"""
    try:
        db_modalitate = update_modalitate_plata(
            db=db, 
            modalitate_id=modalitate_id, 
            modalitate=modalitate
        )
        
        if db_modalitate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found"
            )
            
        return db_modalitate
        
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


@router.delete("/{modalitate_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Payment method deleted successfully"},
    400: {"description": "Bad request, e.g., payment method is in use"},
    404: {"description": "Payment method not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_modalitati_plata(
    modalitate_id: int = Path(..., gt=0, description="The ID of the payment method to delete"),
    db: Session = Depends(get_db)
):
    """Delete a payment method by ID"""
    try:
        success = delete_modalitate_plata(db=db, modalitate_id=modalitate_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found"
            )
        return None  # Will return 204 No Content
        
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
