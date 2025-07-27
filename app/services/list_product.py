from typing import List as TypeList
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.list import List
from app.models.product import Product
from app.models.list_product import ListProduct
from app.schemas.list_product import ListProductCreate, ListProductResponse


def get_list_products(db: Session, list_id: int) -> TypeList[dict]:
    """
    Get all products in a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        
    Returns:
        List of Product objects
        
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
        # Get products with their stock information through the many-to-many relationship
        list_products = db.query(ListProduct).filter(ListProduct.liste_id == list_id).all()
        result = []
        for list_product in list_products:
            product = list_product.product
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
                "images": product.images,
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


def add_product_to_list(db: Session, list_id: int, product_id: int, stoc_produs: int = None) -> ListProduct:
    """
    Add a product to a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        product_id: ID of the product to add
        
    Returns:
        Created ListProduct relationship
        
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
    existing_relationship = db.query(ListProduct).filter(
        ListProduct.liste_id == list_id,
        ListProduct.produse_id == product_id
    ).first()
    
    if existing_relationship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product {product_id} is already in list {list_id}"
        )
    
    try:
        # Create the relationship
        list_product = ListProduct(liste_id=list_id, produse_id=product_id, stoc_produs=stoc_produs)
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
        relationship = db.query(ListProduct).filter(
            ListProduct.liste_id == list_id,
            ListProduct.produse_id == product_id
        ).first()
        
        if not relationship:
            return False
        
        db.delete(relationship)
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
        db.query(ListProduct).filter(ListProduct.liste_id == list_id).delete()
        
        # Add new relationships
        for product_id in product_ids:
            list_product = ListProduct(liste_id=list_id, produse_id=product_id)
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