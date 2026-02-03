from typing import List, Optional, Annotated
import math
import os
import shutil

from fastapi import APIRouter, Depends, Path, Query, HTTPException, Body, status, UploadFile, File, Form
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.database import get_db
from app.core.file_upload import delete_file, is_valid_image, get_upload_dir
from app.core.image_processing import process_and_save_image_versions
from app.core.staging_uploads import resolve_staged_image, delete_staged_image
from app.services.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.category import Category, CategoryCreate, CategoryUpdate
from app.services.category import (
    create_category,
    get_categories,
    get_category_by_id,
    update_category,
    delete_category,
    reorder_categories,
)

router = APIRouter()


@router.post("/{category_id}/image", response_model=Category, responses={
    200: {"description": "Image uploaded successfully", "content": {
        "application/json": {
            "example": {
                "id": 1,
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "image_path": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "image_versions": {
                    "original": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479/f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg",
                    "medium": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479/f47ac10b-58cc-4372-a567-0e02b2c3d479-medium.jpg",
                    "thumbnail": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479/f47ac10b-58cc-4372-a567-0e02b2c3d479-thumbnail.jpg"
                },
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
    file: UploadFile = File(..., description="The image file to upload (JPEG, PNG, or GIF, max 25MB)"),
    db: Session = Depends(get_db)
):
    """Upload an image for a specific category
    
    This endpoint allows uploading an image file for a category. The image will be stored
    in the server's filesystem and the path will be saved in the category record.
    
    - Supported file formats: JPEG, PNG, GIF
    - Maximum file size: configurable via MAX_IMAGE_SIZE_MB (default 15 MB)
    - If the category already has an image, the old image will be replaced
    - The image directory will have a UUID-based name
    - Multiple versions of the image will be created (original, medium, thumbnail)
    
    Returns the updated category object with the new image_path and image_versions.
    """
    try:
        # Check if category exists
        category = get_category_by_id(db, category_id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Validate file (extension, size, optional MIME) before processing
        is_valid, error_message = is_valid_image(file)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        
        # Process and save multiple versions of the image
        # This will create a directory with the original, medium, and thumbnail versions
        image_dir_path = process_and_save_image_versions(file, subdirectory="categories")
        
        # If category already has an image, delete the old directory and all its contents
        if category.image_path:
            # We need to delete all files in the directory
            import os
            import shutil
            from app.core.file_upload import get_upload_dir
            
            full_dir_path = os.path.join(get_upload_dir(), category.image_path)
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
        
        # Update the category with the new image directory path
        updated_category = update_category(
            db=db, 
            category_id=category_id, 
            category=CategoryUpdate(image_path=image_dir_path)
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
    db: Session = Depends(get_db)
):
    """Get all categories with pagination"""
    try:
        categories = get_categories(db, skip=skip, limit=limit)
        return categories
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/reorder", response_model=List[Category], responses={
    200: {"description": "Reordered successfully; returns the ordered list"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "One or more categories not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def reorder_categories_endpoint(
    ordered_ids: List[int] = Body(..., min_items=1, description="Full ordered list of category IDs"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Atomically reorder categories by providing the full ordered list of IDs."""
    try:
        return reorder_categories(db=db, ordered_ids=ordered_ids)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Category created successfully"},
    400: {"description": "Bad request, e.g., duplicate category name or invalid image"},
    401: {"description": "Unauthorized - authentication required"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_category_endpoint(
    name: str = Form(..., description="The name of the category"),
    order_index: int = Form(..., ge=1, le=127, description="Manual ordering index (1-127), unique"),
    primary_image: Optional[UploadFile] = File(
        None,
        description=(
            "Image file for the category. "
            "Deprecated in favor of primary_image_upload_id from /uploads/images."
        ),
    ),
    primary_image_upload_id: Optional[str] = Form(
        None,
        description=(
            "Opaque upload_id returned by POST /api/v1/uploads/images. "
            "If provided, the staged image will be processed and linked as the primary image."
        ),
    ),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new category
    
    Accepts multipart/form-data with a name field, order_index field, and optional image:
    - Either a direct `primary_image` file (deprecated) or a `primary_image_upload_id`
      returned from POST /uploads/images.
    If no image is provided, a placeholder image will be used.
    """
    try:
        # Initialize image_path to None (will use placeholder)
        primary_image_path = None
        staged_upload_id: Optional[str] = None
        
        # It is ambiguous and likely an error if both a direct file and an upload_id are provided.
        if primary_image and primary_image_upload_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either primary_image or primary_image_upload_id, not both.",
            )

        # Process and save image if provided directly
        if primary_image:
            is_valid, error_message = is_valid_image(primary_image)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message,
                )

            primary_image_path = process_and_save_image_versions(
                primary_image, subdirectory="categories"
            )
        # Or via a staged upload_id
        elif primary_image_upload_id:
            from fastapi import UploadFile as _UploadFile

            staged_upload_id = primary_image_upload_id
            upload_dir, meta = resolve_staged_image(primary_image_upload_id)

            stored_filename = meta.get("stored_filename") or meta.get(
                "original_filename"
            )
            file_path = upload_dir / stored_filename if stored_filename else None

            # Fallback: pick the first non-meta file in the directory
            if not file_path or not file_path.exists():
                for child in upload_dir.iterdir():
                    if child.is_file() and child.name != "meta.json":
                        file_path = child
                        break

            if not file_path or not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Staged image file not found",
                )

            original_filename = meta.get("original_filename") or file_path.name

            try:
                with open(file_path, "rb") as f:
                    staged_upload = _UploadFile(
                        filename=original_filename,
                        file=f,
                    )
                    primary_image_path = process_and_save_image_versions(
                        staged_upload, subdirectory="categories"
                    )
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error processing staged image: {exc}",
                )
        
        # Create category object
        category = CategoryCreate(name=name, order_index=order_index, image_path=primary_image_path)
        
        # Create the category in the database
        created_category = create_category(db=db, category=category)
        # If we successfully linked a staged image, clean up the staging directory.
        if staged_upload_id:
            delete_staged_image(staged_upload_id)
        return created_category
    except HTTPException as e:
        # If an HTTP exception occurred and an image directory was created, clean it up
        if primary_image and primary_image_path:
            # Handle directory structure created by process_and_save_image_versions
            import os
            import shutil
            from app.core.file_upload import get_upload_dir
            
            full_dir_path = os.path.join(get_upload_dir(), primary_image_path)
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
        if "staged_upload_id" in locals() and staged_upload_id:
            delete_staged_image(staged_upload_id)
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # If any other exception occurred, also clean up image directory if created
        if primary_image and primary_image_path:
            import os
            import shutil
            from app.core.file_upload import get_upload_dir
            
            full_dir_path = os.path.join(get_upload_dir(), primary_image_path)
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
        if "staged_upload_id" in locals() and staged_upload_id:
            delete_staged_image(staged_upload_id)
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
    db: Session = Depends(get_db)
):
    """Get a specific category by ID"""
    try:
        return get_category_by_id(db, category_id=category_id)
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
    400: {"description": "Bad request, e.g., duplicate category name or invalid image"},
    401: {"description": "Unauthorized - authentication required"},
    404: {"description": "Category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_category_endpoint(
    category_id: int = Path(..., gt=0, description="The ID of the category to update"),
    name: str = Form(..., description="The name of the category"),
    order_index: int = Form(..., ge=1, le=127, description="Manual ordering index (1-127), unique"),
    primary_image: Optional[UploadFile] = File(None, description="Image file for the category"),
    clear_image: bool = Form(False, description="If true, will clear the image and use placeholder"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an existing category (PUT - full replacement)
    
    Accepts multipart/form-data with required name, order_index and optional image file.
    - Name and order_index are required for a PUT operation (replaces the entire resource)
    - If primary_image is not provided:
      - If clear_image is true: the image will be removed and placeholder will be used
      - If clear_image is false: the image will be set to placeholder (following PUT semantics)
    """
    try:
        # First check if the category exists
        existing_category = get_category_by_id(db, category_id=category_id)
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
            
        # Initialize update data and image path
        update_dict = {}
        primary_image_path = None
        
        # In PUT semantics, we always set the name and order_index (they're required)
        update_dict["name"] = name
        update_dict["order_index"] = order_index
        
        # Handle image updates
        if clear_image:
            # Explicitly set image path to None to use placeholder
            update_dict["image_path"] = None
            
            # Clean up old image directory if it exists
            if existing_category.image_path:
                import os
                import shutil
                from app.core.file_upload import get_upload_dir
                
                full_dir_path = os.path.join(get_upload_dir(), existing_category.image_path)
                if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                    shutil.rmtree(full_dir_path)
        
        elif primary_image:
            # If image is provided, process it
            # Validate image
            from app.core.file_upload import is_valid_image
            if not is_valid_image(primary_image):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "loc": ["body", "primary_image"],
                            "msg": "Invalid image format",
                            "type": "value_error.image"
                        }
                    ]
                )
                
            # Process and save multiple versions of the image
            primary_image_path = process_and_save_image_versions(primary_image, subdirectory="categories")
            update_dict["image_path"] = primary_image_path
            
            # Clean up old image directory if it exists
            if existing_category.image_path:
                import os
                import shutil
                from app.core.file_upload import get_upload_dir
                
                full_dir_path = os.path.join(get_upload_dir(), existing_category.image_path)
                if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                    shutil.rmtree(full_dir_path)
        else:
            # If no image is provided and clear_image is false, still set to null (PUT semantics)
            # This follows proper PUT behavior of replacing the entire resource
            update_dict["image_path"] = None
            
            # Clean up old image directory if it exists
            if existing_category.image_path:
                import os
                import shutil
                from app.core.file_upload import get_upload_dir
                
                full_dir_path = os.path.join(get_upload_dir(), existing_category.image_path)
                if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                    shutil.rmtree(full_dir_path)
        
        # If no fields were provided for update, return existing category
        if not update_dict:
            return existing_category
            
        # Create an update data object
        category_update = CategoryUpdate(**update_dict)
        
        # Update the category
        updated_category = update_category(
            db=db,
            category_id=category_id,
            category=category_update
        )
        return updated_category
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{category_id}", response_model=Category, responses={
    200: {"description": "Category updated successfully"},
    400: {"description": "Bad request, e.g., duplicate category name or invalid image"},
    404: {"description": "Category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def patch_category_endpoint(
    category_id: int = Path(..., gt=0, description="The ID of the category to update"),
    name: Optional[str] = Form(None, description="The name of the category"),
    order_index: Optional[int] = Form(None, ge=1, le=127, description="Manual ordering index (1-127), unique"),
    primary_image: Optional[UploadFile] = File(None, description="Image file for the category"),
    clear_image: bool = Form(False, description="If true, will clear the image and use placeholder"),
    db: Session = Depends(get_db)
):
    """Partially update an existing category (PATCH - only update provided fields)
    
    Accepts multipart/form-data with optional fields to update:
    - If name is not provided, the existing name will be kept
    - If primary_image is not provided:
      - If clear_image is true: the image will be removed and placeholder will be used
      - If clear_image is false: the existing image will be kept
    """
    try:
        # First check if the category exists
        existing_category = get_category_by_id(db, category_id=category_id)
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        
        # Initialize update data and image path
        update_dict = {}
        primary_image_path = None
        
        # Add name to update only if provided
        if name is not None:
            update_dict["name"] = name
        
        # Add order_index to update only if provided
        if order_index is not None:
            update_dict["order_index"] = order_index
        
        # Handle image updates
        if clear_image:
            # Explicitly set image path to None to use placeholder
            update_dict["image_path"] = None
            
            # Clean up old image directory if it exists
            if existing_category.image_path:
                import os
                import shutil
                from app.core.file_upload import get_upload_dir
                
                full_dir_path = os.path.join(get_upload_dir(), existing_category.image_path)
                if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                    shutil.rmtree(full_dir_path)
        
        elif primary_image:
            # If image is provided, process it
            # Validate image
            from app.core.file_upload import is_valid_image
            if not is_valid_image(primary_image):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "loc": ["body", "primary_image"],
                            "msg": "Invalid image format",
                            "type": "value_error.image"
                        }
                    ]
                )
                
            # Process and save multiple versions of the image
            primary_image_path = process_and_save_image_versions(primary_image, subdirectory="categories")
            update_dict["image_path"] = primary_image_path
            
            # Clean up old image directory if it exists
            if existing_category.image_path:
                import os
                import shutil
                from app.core.file_upload import get_upload_dir
                
                full_dir_path = os.path.join(get_upload_dir(), existing_category.image_path)
                if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                    shutil.rmtree(full_dir_path)
        
        # If no fields were provided for update, return existing category
        if not update_dict:
            return existing_category
            
        # Create an update data object
        category_update = CategoryUpdate(**update_dict)
        
        # Update the category
        updated_category = update_category(
            db=db,
            category_id=category_id,
            category=category_update
        )
        return updated_category
    except HTTPException as e:
        # If an HTTP exception occurred and an image directory was created, clean it up
        if primary_image and primary_image_path:
            import os
            import shutil
            from app.core.file_upload import get_upload_dir
            
            full_dir_path = os.path.join(get_upload_dir(), primary_image_path)
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # If any other exception occurred, also clean up image directory if created
        if primary_image and primary_image_path:
            import os
            import shutil
            from app.core.file_upload import get_upload_dir
            
            full_dir_path = os.path.join(get_upload_dir(), primary_image_path)
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Category deleted successfully"},
    401: {"description": "Unauthorized - authentication required"},
    404: {"description": "Category not found"},
    409: {"description": "Conflict, category is in use by at least one product"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_category_endpoint(
    category_id: int = Path(..., gt=0, description="The ID of the category to delete"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a category (permanently)"""
    try:
        result = delete_category(db=db, category_id=category_id)
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
