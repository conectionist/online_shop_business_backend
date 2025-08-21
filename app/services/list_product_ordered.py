from typing import List as TypeList
import os
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

from app.models.list import List
from app.models.product import Product
from app.models.category import Category
from app.models.list_product_ordered import ListProductOrdered


def _get_image_versions(image_path: str) -> dict:
    """Generate image versions with dynamic extension detection"""
    if not image_path:
        return {
            "original": "/api/v1/static/placeholders/product_placeholder.jpg",
            "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
            "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
        }
    
    # Extract the image ID from the path
    image_id = os.path.basename(image_path)
    
    # Detect the actual file extension by checking what files exist
    from app.core.file_upload import get_upload_dir
    full_path = os.path.join(get_upload_dir(), image_path)
    if os.path.exists(full_path):
        # Check for common extensions
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            original_file = os.path.join(full_path, f"{image_id}{ext}")
            if os.path.exists(original_file):
                # Found the actual extension, use it for all versions
                return {
                    "original": f"{image_path}/{image_id}{ext}",
                    "medium": f"{image_path}/{image_id}-medium{ext}",
                    "thumbnail": f"{image_path}/{image_id}-thumbnail{ext}"
                }
    
    # Fallback to jpg if no files found
    return {
        "original": f"{image_path}/{image_id}.jpg",
        "medium": f"{image_path}/{image_id}-medium.jpg",
        "thumbnail": f"{image_path}/{image_id}-thumbnail.jpg"
    }


def get_list_products_by_category(db: Session, list_id: int) -> dict:
    """
    Get all products in a list, grouped by category and ordered by position.
    
    Args:
        db: Database session
        list_id: ID of the list
        
    Returns:
        Dictionary with list_id and categories containing ordered products
        
    Raises:
        HTTPException: If list not found
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    try:
        # Get all products in this list, ordered by category and position
        list_products = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id
        ).order_by(
            ListProductOrdered.category_id,
            ListProductOrdered.position
        ).all()
        
        # Get category positions from list_categories table
        from app.models.list_category import ListCategory
        list_categories = db.query(ListCategory).filter(
            ListCategory.liste_id == list_id
        ).all()
        

        
        # Group products by category
        categories = {}
        
        # First, add all categories that are explicitly in the list
        for list_category in list_categories:
            category = db.query(Category).filter(Category.id == list_category.category_id).first()
            if category:
                categories[list_category.category_id] = {
                    "id": list_category.category_id,
                    "name": category.name,
                    "position": list_category.position,
                    "products": []
                }
        
        # Then add products to their categories
        for list_product in list_products:
            product = list_product.product
            category_id = list_product.category_id
            
            # If category is not in categories (shouldn't happen, but just in case)
            if category_id not in categories:
                category = db.query(Category).filter(Category.id == category_id).first()
                categories[category_id] = {
                    "id": category_id,
                    "name": category.name if category else "Unknown Category",
                    "position": list_product.position,  # This will be updated with actual category position
                    "products": []
                }
            
            # Add product to its category
            product_dict = {
                "id": product.id,
                "nume": product.nume,
                "cantitate": product.cantitate,
                "pret": product.pret,
                "description": product.description,
                "category_id": product.category_id,
                "unitati_id": product.unitati_id,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "is_deleted": product.is_deleted,
                "position": list_product.position,
                "stoc_produs": list_product.stoc_produs,
                "images": [
                    {
                        "id": img.id,
                        "path": img.path,
                        "position": img.position,
                        "produse_id": img.produse_id,
                        "is_primary": img.position == 0,
                        "image_versions": _get_image_versions(img.path)
                    }
                    for img in product.images
                ]
            }
            categories[category_id]["products"].append(product_dict)
        
        # Convert to list and sort by category position
        categories_list = list(categories.values())
        categories_list.sort(key=lambda x: x["position"])
        
        return {
            "list_id": list_id,
            "categories": categories_list
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def add_product_to_category(db: Session, list_id: int, product_id: int, category_id: int, position: int = None, stoc_produs: int = None) -> ListProductOrdered:
    """
    Add a product to a specific category in a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        product_id: ID of the product to add
        category_id: ID of the category to add the product to
        position: Position within the category (if None, adds at the end)
        stoc_produs: Stock quantity for this product in this list
        
    Returns:
        Created ListProductOrdered relationship
        
    Raises:
        HTTPException: If list, product, category not found, or relationship already exists
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Check if category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Check if relationship already exists
    existing_relationship = db.query(ListProductOrdered).filter(
        ListProductOrdered.liste_id == list_id,
        ListProductOrdered.produse_id == product_id
    ).first()
    
    if existing_relationship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product {product_id} is already in list {list_id}"
        )
    
    try:
        # If position is not specified, add at the end of the category
        if position is None:
            max_position = db.query(ListProductOrdered).filter(
                ListProductOrdered.liste_id == list_id,
                ListProductOrdered.category_id == category_id
            ).with_entities(func.max(ListProductOrdered.position)).scalar()
            position = 0 if max_position is None else max_position + 1
        
        # Create the relationship
        list_product = ListProductOrdered(
            liste_id=list_id,
            produse_id=product_id,
            category_id=category_id,
            position=position,
            stoc_produs=stoc_produs
        )
        db.add(list_product)
        db.commit()
        db.refresh(list_product)
        return list_product
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add product to list: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def update_product_position(db: Session, list_id: int, product_id: int, new_position: int) -> ListProductOrdered:
    """
    Update the position of a product within its category in a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        product_id: ID of the product to update
        new_position: New position within the category
        
    Returns:
        Updated ListProductOrdered relationship
        
    Raises:
        HTTPException: If list, product, or relationship not found
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Check if relationship exists
    list_product = db.query(ListProductOrdered).filter(
        ListProductOrdered.liste_id == list_id,
        ListProductOrdered.produse_id == product_id
    ).first()
    
    if not list_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} is not in list {list_id}"
        )
    
    try:
        old_position = list_product.position
        category_id = list_product.category_id
        
        # If position isn't changing, nothing to do
        if old_position == new_position:
            return list_product
        
        # Get all products in this category for this list, ordered by position
        products = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.category_id == category_id
        ).order_by(ListProductOrdered.position).all()
        
        # Validate new position
        if new_position < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid position {new_position}. Must be non-negative"
            )
        
        # Update positions of other products in the same category
        if old_position < new_position:
            # Moving forward: shift products between old and new position back by 1
            db.query(ListProductOrdered).filter(
                ListProductOrdered.liste_id == list_id,
                ListProductOrdered.category_id == category_id,
                ListProductOrdered.position > old_position,
                ListProductOrdered.position <= new_position
            ).update({ListProductOrdered.position: ListProductOrdered.position - 1})
        else:
            # Moving backward: shift products between new and old position forward by 1
            db.query(ListProductOrdered).filter(
                ListProductOrdered.liste_id == list_id,
                ListProductOrdered.category_id == category_id,
                ListProductOrdered.position >= new_position,
                ListProductOrdered.position < old_position
            ).update({ListProductOrdered.position: ListProductOrdered.position + 1})
        
        # Update the target product's position
        list_product.position = new_position
        db.commit()
        db.refresh(list_product)
        return list_product
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def move_product_between_categories(db: Session, list_id: int, product_id: int, new_category_id: int, position: int = None) -> ListProductOrdered:
    """
    Move a product from one category to another within a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        product_id: ID of the product to move
        new_category_id: ID of the category to move the product to
        position: Position within the new category (if None, adds at the end)
        
    Returns:
        Updated ListProductOrdered relationship
        
    Raises:
        HTTPException: If list, product, category not found, or relationship not found
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Check if new category exists
    new_category = db.query(Category).filter(Category.id == new_category_id).first()
    if not new_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {new_category_id} not found"
        )
    
    # Check if relationship exists
    list_product = db.query(ListProductOrdered).filter(
        ListProductOrdered.liste_id == list_id,
        ListProductOrdered.produse_id == product_id
    ).first()
    
    if not list_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} is not in list {list_id}"
        )
    
    try:
        old_category_id = list_product.category_id
        old_position = list_product.position
        
        # If moving to the same category, just update position
        if old_category_id == new_category_id:
            return update_product_position(db, list_id, product_id, position or 0)
        
        # If position is not specified, add at the end of the new category
        if position is None:
            max_position = db.query(ListProductOrdered).filter(
                ListProductOrdered.liste_id == list_id,
                ListProductOrdered.category_id == new_category_id
            ).with_entities(func.max(ListProductOrdered.position)).scalar()
            position = 0 if max_position is None else max_position + 1
        else:
            # If position is specified, validate it's not negative
            if position < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid position {position}. Must be non-negative"
                )
            
            # If the target category is empty, allow any position
            # If not empty, validate the position is within bounds
            if new_category_id != old_category_id:  # Only check if moving to different category
                existing_products = db.query(ListProductOrdered).filter(
                    ListProductOrdered.liste_id == list_id,
                    ListProductOrdered.category_id == new_category_id
                ).count()
                if existing_products > 0 and position > existing_products:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid position {position}. Must be between 0 and {existing_products} for category with {existing_products} products"
                    )
        
        # Update positions of products in the old category (shift them down)
        db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.category_id == old_category_id,
            ListProductOrdered.position > old_position
        ).update({ListProductOrdered.position: ListProductOrdered.position - 1})
        
        # Update positions of products in the new category (shift them up)
        db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.category_id == new_category_id,
            ListProductOrdered.position >= position
        ).update({ListProductOrdered.position: ListProductOrdered.position + 1})
        
        # Update the product's category and position
        list_product.category_id = new_category_id
        list_product.position = position
        db.commit()
        db.refresh(list_product)
        return list_product
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def remove_product_from_list(db: Session, list_id: int, product_id: int) -> bool:
    """
    Remove a product from a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        product_id: ID of the product to remove
        
    Returns:
        True if product was removed, False if relationship didn't exist
        
    Raises:
        HTTPException: If list or product not found
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    try:
        logger.info(f"DEBUG: Starting remove_product_from_list for product {product_id} from list {list_id}")
        # Find and delete the relationship
        relationship = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.produse_id == product_id
        ).first()
        
        if not relationship:
            logger.info(f"DEBUG: No relationship found for product {product_id} in list {list_id}")
            return False
        
        logger.info(f"DEBUG: Found relationship for product {product_id} in category {relationship.category_id} at position {relationship.position}")
        # Get the position and category of the product being removed
        removed_position = relationship.position
        category_id = relationship.category_id
        
        # Delete the relationship
        db.delete(relationship)
        
        # Update positions of remaining products in the same category (shift them down)
        db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.category_id == category_id,
            ListProductOrdered.position > removed_position
        ).update({ListProductOrdered.position: ListProductOrdered.position - 1})

        # After removing the product, if there are no more products in this category for this list,
        # remove the category from the list as well to avoid empty categories being shown
        remaining_count = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.category_id == category_id
        ).count()
        
        logger.info(f"DEBUG: After removing product {product_id}, remaining products in category {category_id}: {remaining_count}")

        if remaining_count == 0:
            logger.info(f"DEBUG: Category {category_id} is empty, will remove it from list")
            # Remove the category from the list directly to avoid leaving empty categories
            from app.models.list_category import ListCategory
            logger.info(f"DEBUG: No products remaining in category {category_id}, removing from list")
            list_category_rel = db.query(ListCategory).filter(
                ListCategory.liste_id == list_id,
                ListCategory.category_id == category_id
            ).first()
            if list_category_rel:
                removed_cat_position = list_category_rel.position
                logger.info(f"DEBUG: Deleting category {category_id} at position {removed_cat_position}")
                db.delete(list_category_rel)
                # Shift positions of remaining categories down
                db.query(ListCategory).filter(
                    ListCategory.liste_id == list_id,
                    ListCategory.position > removed_cat_position
                ).update({ListCategory.position: ListCategory.position - 1})
                logger.info(f"DEBUG: Category {category_id} deleted successfully")
            else:
                logger.info(f"DEBUG: Category {category_id} not found in ListCategory table")
        else:
            logger.info(f"DEBUG: Category {category_id} still has {remaining_count} products, keeping it")

        db.commit()

        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def bulk_update_positions(db: Session, list_id: int, positions_data: TypeList[dict]) -> dict:
    """
    Bulk update positions of categories and products in a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        positions_data: List of category positions with their product orderings
        
    Returns:
        Updated list structure with categories and products in new order
        
    Raises:
        HTTPException: If list not found, invalid data, or database error
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    try:
        # Import the schema for validation
        from app.schemas.list_product_ordered import BulkUpdatePositionsRequest, CategoryPosition
        
        # Convert the raw data to proper schema objects for validation
        category_positions = []
        for pos_data in positions_data:
            category_positions.append(CategoryPosition(**pos_data))
        
        # Validate the entire structure
        bulk_request = BulkUpdatePositionsRequest(positions=category_positions)
        
        # Clear all existing product positions for this list
        db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id
        ).delete()
        
        # Clear all existing category positions for this list
        from app.models.list_category import ListCategory
        db.query(ListCategory).filter(
            ListCategory.liste_id == list_id
        ).delete()
        
        # Process each category in order (array index becomes category position)
        for category_index, category_pos in enumerate(bulk_request.positions):
            # Add category to list with position
            list_category = ListCategory(
                liste_id=list_id,
                category_id=category_pos.category_id,
                position=category_index
            )
            db.add(list_category)
            
            # Add products to category with positions based on array indices
            for product_index, product_id in enumerate(category_pos.products):
                # Check if product exists
                product = db.query(Product).filter(Product.id == product_id).first()
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product with ID {product_id} not found"
                    )
                
                # Check if category exists
                category = db.query(Category).filter(Category.id == category_pos.category_id).first()
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Category with ID {category_pos.category_id} not found"
                    )
                
                # Create the product-category relationship
                list_product = ListProductOrdered(
                    liste_id=list_id,
                    produse_id=product_id,
                    category_id=category_pos.category_id,
                    position=product_index,
                    stoc_produs=None  # Keep existing stock logic if needed
                )
                db.add(list_product)
        
        db.commit()
        
        # Return the updated list structure
        return get_list_products_by_category(db=db, list_id=list_id)
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data provided: {str(e)}"
        ) 