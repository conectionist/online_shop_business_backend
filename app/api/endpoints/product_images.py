import os
import shutil
import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import get_current_admin
from app.core.file_upload import is_valid_image, get_upload_dir
from app.core.image_errors import image_validation_detail
from app.core.image_processing import process_and_save_image_versions
from app.models.admin import Admin
from app.models.product import Product
from app.schemas.product_image import ProductImage as ProductImageSchema
from app.services.product import get_product_by_id
from app.services.product_image import (
    create_product_image, get_product_images, get_product_image,
    update_product_image, delete_product_image, reorder_product_images
)
from app.schemas.product_image import ProductImageCreate, ProductImageUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{product_id}/images", response_model=ProductImageSchema, responses={
    201: {"description": "Image uploaded successfully"},
    400: {"description": "Bad request, e.g., invalid file format or size"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Product not found"},
    422: {"description": "Validation error"}
})
async def upload_product_image(
    product_id: int = Path(..., gt=0, description="The ID of the product to upload an image for"),
    file: UploadFile = File(..., description="The image file to upload (JPEG, PNG, GIF, WEBP; max size configurable via MAX_IMAGE_SIZE_MB, default 15 MB)"),
    position: int = Form(None, description="Image position (0=primary, if not specified will be added at the end)"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Upload a new image for a product
    
    This endpoint allows uploading an image file for a product. The image will be stored
    in the server's filesystem with multiple versions (original, medium, thumbnail) and 
    added to the product's image gallery.
    
    - Supported file formats: JPEG, PNG, GIF, WEBP
    - Maximum file size: configurable via MAX_IMAGE_SIZE_MB (default 15 MB)
    - Position 0 indicates primary image
    - If position is not specified, the image will be added at the end of the gallery
    
    Returns the created product image with path and image versions.
    """
    try:
        # Check if product exists
        product = get_product_by_id(db, product_id=product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Validate file (extension, size, optional MIME) before processing
        is_valid, error_detail = is_valid_image(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=image_validation_detail(
                    error_detail["type"], error_detail["msg"], ["body", "file"]
                ),
            )
        
        # Process and save multiple versions of the image
        image_dir_path = process_and_save_image_versions(file, subdirectory="products")
        
        # Determine position if not specified
        if position is None:
            existing_images = get_product_images(db, product_id)
            if not existing_images:
                # If no images exist, this will be the primary image
                position = 0
            else:
                # Otherwise, add at the end
                position = max([img.position for img in existing_images]) + 1
        
        # Create the product image record
        image_data = ProductImageCreate(path=image_dir_path, position=position)
        db_image = create_product_image(db, product_id, image_data)
        
        return db_image
    except HTTPException:
        # If an HTTP exception occurred and an image directory was created, clean it up
        if 'image_dir_path' in locals():
            full_dir_path = os.path.join(get_upload_dir(), image_dir_path)
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
        raise


@router.get("/{product_id}/images", response_model=List[ProductImageSchema], responses={
    200: {"description": "List of product images"},
    404: {"description": "Product not found"}
})
async def get_product_images_endpoint(
    product_id: int = Path(..., gt=0, description="The ID of the product to get images for"),
    db: Session = Depends(get_db)
):
    """
    Get all images for a product
    
    Returns a list of all images for the product ordered by position.
    Position 0 indicates the primary image.
    """
    # Check if product exists
    product = get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return get_product_images(db, product_id)


@router.get("/{product_id}/images/{image_id}", response_model=ProductImageSchema, responses={
    200: {"description": "Product image details"},
    404: {"description": "Product or image not found"}
})
async def get_product_image_endpoint(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    image_id: int = Path(..., gt=0, description="The ID of the image to get"),
    db: Session = Depends(get_db)
):
    """
    Get a specific product image by ID
    
    Returns the details of a specific image for the product.
    """
    # Check if product exists
    product = get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get the image
    db_image = get_product_image(db, image_id)
    if not db_image or db_image.produse_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found for this product"
        )
    
    return db_image


@router.put("/{product_id}/images/{image_id}/position", response_model=ProductImageSchema, responses={
    200: {"description": "Image position updated"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Product or image not found"},
    422: {"description": "Validation error"}
})
async def update_product_image_position(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    image_id: int = Path(..., gt=0, description="The ID of the image to update"),
    position: int = Form(..., ge=0, description="New position for the image (0=primary)"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update a product image position
    
    Changes the position of an image in the product gallery.
    Position 0 indicates the primary image.
    """
    # Check if product exists
    product = get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get the image
    db_image = get_product_image(db, image_id)
    if not db_image or db_image.produse_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found for this product"
        )
    
    # Update image position
    image_data = ProductImageUpdate(position=position)
    updated_image = update_product_image(db, image_id, image_data)
    
    return updated_image


@router.put("/{product_id}/images/{image_id}/primary", response_model=ProductImageSchema, responses={
    200: {"description": "Image set as primary"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Product or image not found"}
})
async def set_product_image_as_primary(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    image_id: int = Path(..., gt=0, description="The ID of the image to set as primary"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Set a product image as primary
    
    This is a convenience endpoint to set an image as the primary image (position=0).
    """
    # Check if product exists
    product = get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get the image
    db_image = get_product_image(db, image_id)
    if not db_image or db_image.produse_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found for this product"
        )
    
    # Set as primary (position=0)
    image_data = ProductImageUpdate(position=0)
    updated_image = update_product_image(db, image_id, image_data)
    
    return updated_image


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Image deleted successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Product or image not found"}
})
async def delete_product_image_endpoint(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    image_id: int = Path(..., gt=0, description="The ID of the image to delete"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a product image
    
    Removes an image from the product gallery and deletes the image files.
    Remaining images are automatically reordered to ensure continuous positions.
    """
    # Check if product exists
    product = get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get the image to check ownership and get the path
    db_image = get_product_image(db, image_id)
    if not db_image or db_image.produse_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found for this product"
        )
    
    # Get the path to delete the files
    image_path = db_image.path
    
    # Delete from database (this reorders remaining images)
    success = delete_product_image(db, image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting image"
        )
    
    # Delete image files from filesystem
    image_dir_path = os.path.join(get_upload_dir(), image_path)
    if os.path.exists(image_dir_path) and os.path.isdir(image_dir_path):
        shutil.rmtree(image_dir_path)
    
    return None


@router.put("/{product_id}/images/reorder", response_model=List[ProductImageSchema], responses={
    200: {"description": "Images reordered successfully"},
    400: {"description": "Invalid image IDs or positions"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Product not found"}
})
async def reorder_product_images_endpoint(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    image_order: List[Dict[str, int]] = Body(..., description="List of image IDs and positions to reorder"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Reorder product images
    
    Updates the positions of multiple images at once.
    Expects a list of dictionaries with image IDs and desired positions.
    
    Example:
    ```
    [
      {"id": 1, "position": 0},
      {"id": 2, "position": 1},
      {"id": 3, "position": 2}
    ]
    ```
    """
    logger.info(f"Reorder images request for product_id={product_id}, image_order={image_order}")
    
    if not image_order:
        logger.warning(f"Reorder images failed: image_order not provided for product_id={product_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image order not provided"
        )
    
    # Validate each item in the image_order list has required fields
    for i, item in enumerate(image_order):
        if not isinstance(item, dict) or 'id' not in item or 'position' not in item:
            logger.warning(
                f"Reorder images failed: item at position {i} missing required fields "
                f"for product_id={product_id}, item={item}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item at position {i} is missing required fields 'id' and 'position'"
            )
        
        # Check that id and position are integers
        try:
            int(item['id'])
            int(item['position'])
        except (ValueError, TypeError):
            logger.warning(
                f"Reorder images failed: invalid values at position {i} "
                f"for product_id={product_id}, item={item}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item at position {i} has invalid values: 'id' and 'position' must be integers"
            )
    
    # Check if product exists
    product = get_product_by_id(db, product_id=product_id)
    if not product:
        logger.warning(f"Reorder images failed: product not found, product_id={product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Reorder images
    updated_images = reorder_product_images(db, product_id, image_order)
    
    if not updated_images:
        # Get more context about which images weren't found
        image_ids = [item["id"] for item in image_order]
        existing_images = get_product_images(db, product_id)
        existing_image_ids = [img.id for img in existing_images]
        missing_ids = set(image_ids) - set(existing_image_ids)
        
        logger.warning(
            f"Reorder images failed: invalid image IDs for product_id={product_id}. "
            f"Requested IDs: {image_ids}, Existing IDs: {existing_image_ids}, Missing: {missing_ids}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image IDs provided. Missing image IDs: {sorted(missing_ids) if missing_ids else 'none'} (existing IDs: {existing_image_ids})"
        )
    
    logger.info(f"Reorder images successful for product_id={product_id}, reordered {len(updated_images)} images")
    return updated_images
