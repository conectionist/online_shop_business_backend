from typing import List as TypeList
import os
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.list import List
from app.models.product import Product
from app.models.list_product_ordered import ListProductOrdered
from app.models.category import Category


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


def get_list_products(db: Session, list_id: int) -> TypeList[dict]:
    """
    Get all products in a list, ordered by category and position.
    
    Args:
        db: Database session
        list_id: ID of the list
        
    Returns:
        List of Product objects with full image data and stock information, ordered by category and position
        
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
        # Get products with their stock information through the new ordered relationship
        list_products = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id
        ).order_by(
            ListProductOrdered.category_id,
            ListProductOrdered.position
        ).all()
        
        result = []
        for list_product in list_products:
            product = list_product.product
            # Convert the SQLAlchemy product to a dict with all computed fields
            # This ensures image_versions and is_primary are included
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
                ],
                "stoc_produs": list_product.stoc_produs
            }
            result.append(product_dict)
        return result
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def add_product_to_list(db: Session, list_id: int, product_id: int, stoc_produs: int = None) -> ListProductOrdered:
    """
    Add a product to a list (legacy function - adds to product's default category).
    
    Args:
        db: Database session
        list_id: ID of the list
        product_id: ID of the product to add
        stoc_produs: Stock quantity for this product in this list
        
    Returns:
        Created ListProductOrdered relationship
        
    Raises:
        HTTPException: If list or product not found, or relationship already exists
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
        # Get the product's default category
        category_id = product.category_id
        
        # Get the next position in this category
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
        # Find and delete the relationship
        relationship = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.produse_id == product_id
        ).first()
        
        if not relationship:
            return False
        
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

        db.commit()

        # After committing the transaction, check if there are no more products in this category for this list,
        # and remove the category from the list as well to avoid leaving empty categories being shown
        remaining_count = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id,
            ListProductOrdered.category_id == category_id
        ).count()

        if remaining_count == 0:
            # Remove the category from the list directly to avoid leaving empty categories
            from app.models.list_category import ListCategory
            list_category_rel = db.query(ListCategory).filter(
                ListCategory.liste_id == list_id,
                ListCategory.category_id == category_id
            ).first()
            if list_category_rel:
                removed_cat_position = list_category_rel.position
                db.delete(list_category_rel)
                # Shift positions of remaining categories down
                db.query(ListCategory).filter(
                    ListCategory.liste_id == list_id,
                    ListCategory.position > removed_cat_position
                ).update({ListCategory.position: ListCategory.position - 1})
                db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def replace_list_products(db: Session, list_id: int, product_ids: TypeList[int]) -> TypeList[Product]:
    """
    Replace all products in a list with the given product IDs.
    
    Args:
        db: Database session
        list_id: ID of the list
        product_ids: List of product IDs to add to the list
        
    Returns:
        List of Product objects in the list
        
    Raises:
        HTTPException: If list not found or any product doesn't exist
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if all products exist
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    if len(products) != len(product_ids):
        found_ids = [p.id for p in products]
        missing_ids = [pid for pid in product_ids if pid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products with IDs {missing_ids} not found"
        )
    
    try:
        # Remove all existing relationships
        db.query(ListProductOrdered).filter(ListProductOrdered.liste_id == list_id).delete()
        
        # Add new relationships grouped by category
        category_products = {}
        for product in products:
            category_id = product.category_id
            if category_id not in category_products:
                category_products[category_id] = []
            category_products[category_id].append(product)
        
        # Add products to their respective categories with positions
        for category_id, category_products_list in category_products.items():
            for position, product in enumerate(category_products_list):
                list_product = ListProductOrdered(
                    liste_id=list_id,
                    produse_id=product.id,
                    category_id=category_id,
                    position=position
                )
                db.add(list_product)
        
        db.commit()
        
        # Return the products
        return products
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def add_products_to_list(db: Session, list_id: int, product_ids: TypeList[int]) -> TypeList[Product]:
    """
    Add multiple products to a list without replacing existing ones.
    
    Args:
        db: Database session
        list_id: ID of the list
        product_ids: List of product IDs to add to the list
        
    Returns:
        List of Product objects that were added to the list
        
    Raises:
        HTTPException: If list not found or any product doesn't exist
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if all products exist
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    if len(products) != len(product_ids):
        found_ids = [p.id for p in products]
        missing_ids = [pid for pid in product_ids if pid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products with IDs {missing_ids} not found"
        )
    
    try:
        # Get existing product IDs in the list
        existing_relationships = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == list_id
        ).all()
        existing_product_ids = [rel.produse_id for rel in existing_relationships]
        
        # Filter out products that are already in the list
        new_product_ids = [pid for pid in product_ids if pid not in existing_product_ids]
        
        if not new_product_ids:
            # All products are already in the list
            return []
        
        # Group new products by category
        category_products = {}
        for product in products:
            if product.id in new_product_ids:
                category_id = product.category_id
                if category_id not in category_products:
                    category_products[category_id] = []
                category_products[category_id].append(product)
        
        # Add new relationships with proper positioning
        added_products = []
        for category_id, category_products_list in category_products.items():
            # Get the next position in this category
            max_position = db.query(ListProductOrdered).filter(
                ListProductOrdered.liste_id == list_id,
                ListProductOrdered.category_id == category_id
            ).with_entities(func.max(ListProductOrdered.position)).scalar()
            start_position = 0 if max_position is None else max_position + 1
            
            for position, product in enumerate(category_products_list):
                list_product = ListProductOrdered(
                    liste_id=list_id,
                    produse_id=product.id,
                    category_id=category_id,
                    position=start_position + position
                )
                db.add(list_product)
                added_products.append(product)
        
        db.commit()
        
        # Return only the products that were actually added
        return added_products
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        ) 