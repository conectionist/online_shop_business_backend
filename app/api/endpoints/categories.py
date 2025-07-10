from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.category import Category, CategoryCreate, CategoryUpdate
from app.services.category import (
    create_category,
    get_categories,
    get_category_by_id,
    soft_delete_category,
    update_category,
    hard_delete_category
)

router = APIRouter()


@router.get("/", response_model=List[Category], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_categories(
    skip: int = Query(0, ge=0, le=1000, description="Number of items to skip (max 1000)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    include_deleted: bool = Query(False, description="Whether to include soft-deleted categories"),
    db: Session = Depends(get_db)
):
    """Get all categories with pagination and optional filtering for deleted items"""
    try:
        categories = get_categories(db, skip=skip, limit=limit, include_deleted=include_deleted)
        return categories
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Category created successfully"},
    400: {"description": "Bad request, e.g., duplicate category name"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_category_endpoint(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    try:
        return create_category(db=db, category=category)
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


@router.get("/{category_id}", response_model=Category, responses={
    200: {"description": "Successful response"},
    404: {"description": "Category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_category(
    category_id: int = Path(..., gt=0, description="The ID of the category to retrieve"),
    include_deleted: bool = Query(False, description="Whether to include soft-deleted categories"),
    db: Session = Depends(get_db)
):
    """Get a specific category by ID"""
    try:
        return get_category_by_id(db, category_id=category_id, include_deleted=include_deleted)
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


@router.put("/{category_id}", response_model=Category, responses={
    200: {"description": "Category updated successfully"},
    400: {"description": "Bad request, e.g., duplicate category name"},
    404: {"description": "Category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_category_endpoint(
    category_id: int = Path(..., gt=0, description="The ID of the category to update"),
    category: CategoryUpdate = Body(..., description="Updated category data"),
    db: Session = Depends(get_db)
):
    """Update an existing category"""
    try:
        return update_category(db=db, category_id=category_id, category=category)
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


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Category deleted successfully"},
    404: {"description": "Category not found"},
    409: {"description": "Conflict, category is in use by at least one product"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_category(
    category_id: int = Path(..., gt=0, description="The ID of the category to delete"),
    permanent: bool = Query(False, description="Whether to permanently delete the category"),
    db: Session = Depends(get_db)
):
    """Delete a category (soft delete by default, hard delete if permanent=True)"""
    try:
        if permanent:
            result = hard_delete_category(db=db, category_id=category_id)
        else:
            result = soft_delete_category(db=db, category_id=category_id)
            
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
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
