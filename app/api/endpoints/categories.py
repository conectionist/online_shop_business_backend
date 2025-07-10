from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Path, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.file_upload import save_upload_file, delete_file
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


@router.post("/{category_id}/image", response_model=Category, responses={
    200: {"description": "Image uploaded successfully", "content": {
        "application/json": {
            "example": {
                "id": 1,
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "image_path": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg",
                "is_deleted": False
            }
        }
    }},
    400: {"description": "Bad request, e.g., invalid file format or size"},
    404: {"description": "Category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def upload_category_image(
    category_id: int = Path(..., gt=0, description="The ID of the category to upload an image for"),
    file: UploadFile = File(..., description="The image file to upload (JPEG, PNG, or GIF, max 5MB)"),
    db: Session = Depends(get_db)
):
    """Upload an image for a specific category
    
    This endpoint allows uploading an image file for a category. The image will be stored
    in the server's filesystem and the path will be saved in the category record.
    
    - Supported file formats: JPEG, PNG, GIF
    - Maximum file size: 5MB
    - If the category already has an image, the old image will be replaced
    - The image filename will be converted to a secure UUID-based name
    
    Returns the updated category object with the new image_path.
    """
    try:
        # Check if category exists
        category = get_category_by_id(db, category_id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Save the file to the uploads directory in a 'categories' subdirectory
        relative_path = save_upload_file(file, subdirectory="categories")
        
        # If category already has an image, delete the old one
        if category.image_path:
            delete_file(category.image_path)
        
        # Update the category with the new image path
        updated_category = update_category(
            db=db, 
            category_id=category_id, 
            category=CategoryUpdate(image_path=relative_path)
        )
        
        return updated_category
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


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
