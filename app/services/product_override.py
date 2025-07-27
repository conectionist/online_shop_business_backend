from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.product_override import ProductOverride
from app.models.product import Product
from app.schemas.product_override import ProductOverrideCreate, ProductOverrideUpdate


def get_product_overrides(db: Session, product_id: Optional[int] = None, is_active: Optional[bool] = None) -> List[ProductOverride]:
    """
    Get product overrides with optional filtering.
    
    Args:
        db: Database session
        product_id: Optional product ID to filter by
        is_active: Optional active status to filter by
        
    Returns:
        List of ProductOverride objects
    """
    query = db.query(ProductOverride)
    
    if product_id is not None:
        query = query.filter(ProductOverride.produse_id == product_id)
    
    if is_active is not None:
        query = query.filter(ProductOverride.is_active == is_active)
    
    try:
        return query.all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_product_override(db: Session, override_id: int) -> ProductOverride:
    """
    Get a specific product override by ID.
    
    Args:
        db: Database session
        override_id: ID of the override to retrieve
        
    Returns:
        ProductOverride object
        
    Raises:
        HTTPException: If override not found
    """
    override = db.query(ProductOverride).filter(ProductOverride.id == override_id).first()
    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product override with ID {override_id} not found"
        )
    return override


def create_product_override(db: Session, override_data: ProductOverrideCreate) -> ProductOverride:
    """
    Create a new product override.
    
    Args:
        db: Database session
        override_data: ProductOverrideCreate data
        
    Returns:
        Created ProductOverride object
        
    Raises:
        HTTPException: If product not found or override already exists
    """
    # Check if product exists
    product = db.query(Product).filter(Product.id == override_data.produse_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {override_data.produse_id} not found"
        )
    
    # Check if override already exists for this product and field
    existing_override = db.query(ProductOverride).filter(
        ProductOverride.produse_id == override_data.produse_id,
        ProductOverride.field_name == override_data.field_name,
        ProductOverride.is_active == True
    ).first()
    
    if existing_override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Active override already exists for product {override_data.produse_id} field {override_data.field_name}"
        )
    
    try:
        override = ProductOverride(**override_data.model_dump())
        db.add(override)
        db.commit()
        db.refresh(override)
        return override
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create product override: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def update_product_override(db: Session, override_id: int, override_data: ProductOverrideUpdate) -> ProductOverride:
    """
    Update an existing product override.
    
    Args:
        db: Database session
        override_id: ID of the override to update
        override_data: ProductOverrideUpdate data
        
    Returns:
        Updated ProductOverride object
        
    Raises:
        HTTPException: If override not found
    """
    override = get_product_override(db, override_id)
    
    try:
        update_data = override_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(override, field, value)
        
        db.commit()
        db.refresh(override)
        return override
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def delete_product_override(db: Session, override_id: int) -> bool:
    """
    Delete a product override.
    
    Args:
        db: Database session
        override_id: ID of the override to delete
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If override not found
    """
    override = get_product_override(db, override_id)
    
    try:
        db.delete(override)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_product_with_overrides(db: Session, product_id: int) -> dict:
    """
    Get a product with all its active overrides.
    
    Args:
        db: Database session
        product_id: ID of the product
        
    Returns:
        Dictionary with product data and overrides
        
    Raises:
        HTTPException: If product not found
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Get active overrides for this product
    overrides = db.query(ProductOverride).filter(
        ProductOverride.produse_id == product_id,
        ProductOverride.is_active == True
    ).all()
    
    # Create override mapping
    override_map = {override.field_name: override for override in overrides}
    
    # Build product data with overrides
    product_data = {
        "id": product.id,
        "nume": product.nume,
        "cantitate": product.cantitate,
        "pret": product.pret,
        "description": product.description,
        "category_id": product.category_id,
        "unitati_id": product.unitati_id,
        "stock": product.stock,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "is_deleted": product.is_deleted,
        "overrides": override_map
    }
    
    return product_data 