from typing import List, Optional
import os
import shutil
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.file_upload import delete_file, get_upload_dir
from app.models.product import Product
from app.models.product_image import ProductImage
from app.schemas.product import ProductCreate, ProductUpdate


# GET all products with pagination and filter by is_deleted
def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    include_deleted: bool = False,
    category_id: Optional[int] = None
) -> List[Product]:
    """
    Retrieve all products with pagination and optional filtering by category and deletion status.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_deleted: Whether to include soft-deleted products
        category_id: Optional filter by category ID
        
    Returns:
        List of Product objects
    """
    # Validate pagination parameters
    # Protect against integer overflow and extremely large values
    try:
        if skip < 0 or skip > 10000:  # Cap maximum skip to 10000
            skip = 0
        if limit <= 0 or limit > 1000:  # Cap maximum limit to 1000
            limit = 100
    except (OverflowError, ValueError, TypeError):
        # If any conversion error occurs, use safe defaults
        skip = 0
        limit = 100
        
    try:
        query = db.query(Product)
        
        # Apply filters
        if not include_deleted:
            query = query.filter(Product.is_deleted == False)
        
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
            
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# GET product by ID
def get_product_by_id(db: Session, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    """
    Retrieve a specific product by its ID.
    
    Args:
        db: Database session
        product_id: ID of the product to retrieve
        include_deleted: Whether to include soft-deleted products
        
    Returns:
        Product object if found
        
    Raises:
        HTTPException: If the ID is invalid or the product is not found
    """
    
    try:
        query = db.query(Product).filter(Product.id == product_id)
        if not include_deleted:
            query = query.filter(Product.is_deleted == False)
            
        product = query.first()
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        return product
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# GET product by name
def get_product_by_name(db: Session, nume: str, include_deleted: bool = False) -> Optional[Product]:
    """
    Retrieve a specific product by its name.
    
    Args:
        db: Database session
        nume: Name of the product to retrieve
        include_deleted: Whether to include soft-deleted products
        
    Returns:
        Product object if found
        
    Raises:
        HTTPException: If the name is invalid or the product is not found
    """
    if not nume or nume.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Product name cannot be empty"
        )
        
    try:
        query = db.query(Product).filter(Product.nume == nume)
        if not include_deleted:
            query = query.filter(Product.is_deleted == False)
            
        return query.first()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# CREATE new product
def create_product(db: Session, product: ProductCreate) -> Product:
    """
    Create a new product.
    
    Args:
        db: Database session
        product: Product data
        
    Returns:
        Created product object
        
    Raises:
        HTTPException: If a product with the same name already exists or validation fails
    """
    try:
        # Sanitize and validate inputs
        if not product.nume or str(product.nume).strip() == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["body", "nume"],
                        "msg": "field required",
                        "type": "value_error.missing"
                    }
                ]
            )
        
        # Check if product with this name exists (including soft-deleted ones)
        existing_product = get_product_by_name(db, str(product.nume), include_deleted=True)
        if existing_product:
            if existing_product.is_deleted:
                # Restore the soft-deleted product
                try:
                    existing_product.is_deleted = False
                    existing_product.cantitate = product.cantitate
                    existing_product.pret = product.pret
                    existing_product.description = product.description
                    # primary_image_path removed - images are now managed through product_images relationship
                    existing_product.category_id = product.category_id
                    existing_product.unitati_id = product.unitati_id
                    existing_product.updated_at = datetime.now()
                    
                    db.commit()
                    db.refresh(existing_product)
                    return existing_product
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=[{
                            "loc": ["body"],
                            "msg": "Error restoring product",
                            "type": "server_error"
                        }]
                    )
            else:
                # Product exists and is not deleted
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=[{
                        "loc": ["body", "nume"],
                        "msg": "Product with this name already exists",
                        "type": "value_error.already_exists"
                    }]
                )
        
        # Create new product
        db_product = Product(
            nume=str(product.nume),
            cantitate=product.cantitate,
            pret=product.pret,
            description=product.description,
            # primary_image_path removed - images are now managed through product_images relationship
            category_id=product.category_id,
            unitati_id=product.unitati_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False
        )
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError as e:
        db.rollback()
        if "foreign key constraint fails" in str(e).lower():
            # Check if it's a category_id or unitati_id constraint violation
            if "category_id" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "loc": ["body", "category_id"],
                            "msg": f"Category with ID {product.category_id} does not exist",
                            "type": "value_error.foreign_key"
                        }
                    ]
                )
            elif "unitati_id" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "loc": ["body", "unitati_id"],
                            "msg": f"Unit with ID {product.unitati_id} does not exist",
                            "type": "value_error.foreign_key"
                        }
                    ]
                )
            else:
                # Generic foreign key error with proper format
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "loc": ["body"],
                            "msg": "Foreign key constraint violation",
                            "type": "value_error.foreign_key"
                        }
                    ]
                )
        else:
            # Other integrity errors with proper format
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[
                    {
                        "loc": ["body"],
                        "msg": "Database integrity error",
                        "type": "value_error.database"
                    }
                ]
            )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# UPDATE existing product
def update_product(db: Session, product_id: int, product: ProductUpdate) -> Product:
    """
    Update an existing product.
    
    Args:
        db: Database session
        product_id: ID of the product to update
        product: ProductUpdate object containing the new data
        
    Returns:
        Updated Product object
        
    Raises:
        HTTPException: If validation fails, the product is not found, or a database error occurs
    """
    # Validate ID
    if product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {product_id} - must be positive"
        )
    
    # Convert Pydantic model to dict excluding unset fields
    update_data = product.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
        
    try:
        # Check if product exists
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if db_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
            
        # If updating the name, check if it would cause a duplicate
        if "nume" in update_data and update_data["nume"] != db_product.nume:
            existing_product = (
                db.query(Product)
                .filter(
                    Product.nume == update_data["nume"],
                    Product.id != product_id,
                    Product.is_deleted == False,
                )
                .first()
            )
            if existing_product:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with name '{update_data['nume']}' already exists"
                )
                
        # Handle image update
        old_image_path = None
        # primary_image_path handling removed - images are now managed through product_images relationship
                
        # Update product attributes
        for key, value in update_data.items():
            setattr(db_product, key, value)
            
        db.commit()
        db.refresh(db_product)
        
        # Clean up old image file if image was updated
        if old_image_path:
            # Get the full directory path
            full_dir_path = os.path.join(get_upload_dir(), old_image_path)
            
            # Check if it's a directory and delete it with all contents
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
            else:
                # Fallback to the old method for backward compatibility
                delete_file(old_image_path)
            
        return db_product
    except IntegrityError as e:
        db.rollback()
        if "foreign key constraint fails" in str(e).lower():
            # Check if it's a category_id or unitati_id constraint violation
            if "category_id" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with ID {product.category_id} does not exist"
                )
            elif "unitati_id" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unit with ID {product.unitati_id} does not exist"
                )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate product name"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# SOFT DELETE product (soft delete)
def soft_delete_product(db: Session, product_id: int) -> bool:
    """
    Soft delete a product by setting is_deleted to True.
    
    Args:
        db: Database session
        product_id: ID of the product to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        HTTPException: If the ID is invalid or a database error occurs
    """
    # Validate ID
    if product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {product_id} - must be positive"
        )
    
    try:
        # Check if product exists and is not already deleted
        db_product = db.query(Product).filter(
            and_(Product.id == product_id, Product.is_deleted == False)
        ).first()
        
        if db_product is None:
            return False
        
        # Soft delete by setting is_deleted to True
        db_product.is_deleted = True
        db.commit()
        return True
        # Note: We don't delete the image file on soft delete
        # This allows for easy restoration if the product is undeleted
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# HARD DELETE product (physical deletion)
def hard_delete_product(db: Session, product_id: int) -> bool:
    """
    Hard delete a product from the database.
    
    Args:
        db: Database session
        product_id: ID of the product to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        HTTPException: If the ID is invalid, the product is in use, or a database error occurs
    """
    # Validate ID
    if product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {product_id} - must be positive"
        )
    
    try:
        # Check if product exists
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if db_product is None:
            return False
        
        # Store all image paths before deletion for cleanup
        # The images will be automatically deleted from the database due to cascade
        # But we need to clean up the files on disk
        image_paths = [image.path for image in db_product.images]
        
        # primary_image_path field has been removed from the model
        
        # Attempt to delete from database (will cascade delete product_images)
        db.delete(db_product)
        db.commit()
        
        # Delete all the associated image directories
        for image_path in image_paths:
            if image_path:
                # Get the full directory path
                full_dir_path = os.path.join(get_upload_dir(), image_path)
                
                # Check if it's a directory and delete it with all contents
                if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                    shutil.rmtree(full_dir_path)
        
        # Legacy primary_image_path field handling has been completely removed
            
        return True
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete product because it is in use by other records"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
