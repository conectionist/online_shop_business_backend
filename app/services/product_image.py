from typing import List, Optional, Dict

from sqlalchemy import update, delete
from sqlalchemy.orm import Session

from app.models.product_image import ProductImage
from app.schemas.product_image import ProductImageCreate, ProductImageUpdate


def create_product_image(db: Session, product_id: int, image_data: ProductImageCreate) -> ProductImage:
    """
    Create a new product image
    
    If position=0 is specified, reorders existing images
    """
    # Check if position=0 is being added (new primary image)
    if image_data.position == 0:
        # Update existing primary image positions if any
        existing_primary = db.query(ProductImage).filter(
            ProductImage.produse_id == product_id,
            ProductImage.position == 0
        ).first()
        if existing_primary:
            # Shift all positions up by 1
            db.execute(
                update(ProductImage)
                .where(ProductImage.produse_id == product_id)
                .values(position=ProductImage.position + 1)
            )
    
    # Create new product image
    db_image = ProductImage(**image_data.model_dump(), produse_id=product_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def get_product_images(db: Session, product_id: int) -> List[ProductImage]:
    """
    Get all images for a product, ordered by position
    """
    return db.query(ProductImage).filter(
        ProductImage.produse_id == product_id
    ).order_by(ProductImage.position).all()


def get_product_image(db: Session, image_id: int) -> Optional[ProductImage]:
    """
    Get a specific product image by ID
    """
    return db.query(ProductImage).filter(ProductImage.id == image_id).first()


def get_product_image_by_product_and_position(
    db: Session, product_id: int, position: int
) -> Optional[ProductImage]:
    """
    Get a product image by product_id and position
    """
    return db.query(ProductImage).filter(
        ProductImage.produse_id == product_id,
        ProductImage.position == position
    ).first()


def update_product_image(db: Session, image_id: int, image_data: ProductImageUpdate) -> Optional[ProductImage]:
    """
    Update a product image's position
    
    If setting as primary (position=0), handles existing primary image
    """
    db_image = get_product_image(db, image_id)
    if not db_image:
        return None
        
    # Get current position to check if changing
    current_position = db_image.position
    new_position = image_data.position
    
    # If position isn't changing, nothing to do with other images
    if current_position == new_position:
        return db_image
        
    # If setting as primary (position=0)
    if new_position == 0 and current_position != 0:
        # Find existing primary image if any
        existing_primary = db.query(ProductImage).filter(
            ProductImage.produse_id == db_image.produse_id,
            ProductImage.position == 0,
            ProductImage.id != image_id
        ).first()
        
        if existing_primary:
            # Move the existing primary to this image's position
            existing_primary.position = current_position
            
    # If this was the primary and now isn't
    elif current_position == 0 and new_position != 0:
        # Shift all positions to make room for new position
        db.execute(
            update(ProductImage)
            .where(
                ProductImage.produse_id == db_image.produse_id,
                ProductImage.position >= new_position,
                ProductImage.id != image_id
            )
            .values(position=ProductImage.position + 1)
        )
    
    # Update the image position
    db_image.position = new_position
    
    db.commit()
    db.refresh(db_image)
    return db_image


def delete_product_image(db: Session, image_id: int) -> bool:
    """
    Delete a product image and reorder remaining images
    """
    db_image = get_product_image(db, image_id)
    if not db_image:
        return False
        
    # Save position and product_id for later
    position = db_image.position
    product_id = db_image.produse_id
    
    # Delete the image
    db.delete(db_image)
    
    # Reorder remaining images to ensure continuous positions
    db.execute(
        update(ProductImage)
        .where(
            ProductImage.produse_id == product_id,
            ProductImage.position > position
        )
        .values(position=ProductImage.position - 1)
    )
    
    db.commit()
    return True


def reorder_product_images(db: Session, product_id: int, image_order: List[Dict[str, int]]) -> List[ProductImage]:
    """
    Bulk update image positions (reordering)
    
    image_order should be a list of dicts with {id: int, position: int}
    """
    # Verify all images exist and belong to this product
    image_ids = [item["id"] for item in image_order]
    db_images = db.query(ProductImage).filter(
        ProductImage.id.in_(image_ids),
        ProductImage.produse_id == product_id
    ).all()
    
    # If not all images were found, return None
    if len(db_images) != len(image_ids):
        return []
    
    # Update positions
    for item in image_order:
        db.execute(
            update(ProductImage)
            .where(
                ProductImage.id == item["id"],
                ProductImage.produse_id == product_id
            )
            .values(position=item["position"])
        )
    
    db.commit()
    return get_product_images(db, product_id)
