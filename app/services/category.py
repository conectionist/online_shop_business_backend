from typing import List, Optional
import os
import shutil

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.file_upload import delete_file, get_upload_dir
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


# GET all categories with pagination and filter by is_deleted
def get_categories(db: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[Category]:
    """
    Retrieve all categories with pagination and optional filtering for deleted items.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_deleted: Whether to include soft-deleted categories
        
    Returns:
        List of Category objects
    """
    try:
        query = db.query(Category)
        if not include_deleted:
            query = query.filter(Category.is_deleted == False)
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# GET category by ID
def get_category_by_id(db: Session, category_id: int, include_deleted: bool = False) -> Optional[Category]:
    """
    Retrieve a specific category by its ID.
    
    Args:
        db: Database session
        category_id: ID of the category to retrieve
        include_deleted: Whether to include soft-deleted categories
        
    Returns:
        Category object if found
        
    Raises:
        HTTPException: If the ID is invalid or the category is not found
    """
    if category_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {category_id} - must be positive"
        )
    
    try:
        query = db.query(Category).filter(Category.id == category_id)
        if not include_deleted:
            query = query.filter(Category.is_deleted == False)
            
        category = query.first()
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        return category
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# GET category by name
def get_category_by_name(db: Session, name: str, include_deleted: bool = False) -> Optional[Category]:
    """
    Retrieve a specific category by its name.
    
    Args:
        db: Database session
        name: Name of the category to retrieve
        include_deleted: Whether to include soft-deleted categories
        
    Returns:
        Category object if found
        
    Raises:
        HTTPException: If the name is invalid or the category is not found
    """
    if not name or name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category name cannot be empty"
        )
        
    try:
        query = db.query(Category).filter(Category.name == name)
        if not include_deleted:
            query = query.filter(Category.is_deleted == False)
            
        return query.first()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# CREATE new category
def create_category(db: Session, category: CategoryCreate) -> Category:
    """
    Create a new category or restore a soft-deleted one.
    
    If a soft-deleted category with the same name exists, it will be restored instead.
    
    Args:
        db: Database session
        category: CategoryCreate object containing the data
        
    Returns:
        Created or restored Category object
        
    Raises:
        HTTPException: If a duplicate name is found (status 400) or other validation/database errors occur
    """
    # Validate name (image_path is now optional)
    if not category.name or category.name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category name cannot be empty"
        )
    
    # First check if category with the same name already exists (not soft-deleted)
    existing_active = db.query(Category).filter(
        and_(Category.name == category.name, Category.is_deleted == False)
    ).first()
    
    if existing_active:
        # Return 409 Conflict for duplicate name (REST API best practice)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with name '{category.name}' already exists"
        )
    
    # Check if a soft-deleted category with the same name exists
    soft_deleted_category = db.query(Category).filter(
        and_(Category.name == category.name, Category.is_deleted == True)
    ).first()
    
    if soft_deleted_category:
        # Restore the soft-deleted category
        soft_deleted_category.is_deleted = False
        soft_deleted_category.image_path = category.image_path
        db.commit()
        db.refresh(soft_deleted_category)
        return soft_deleted_category
    
    # Create new category
    try:
        # image_path can be None, in which case the placeholder will be used
        db_category = Category(
            name=category.name,
            image_path=category.image_path,
            is_deleted=False
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category with the name '{category.name}' already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# UPDATE existing category
def update_category(db: Session, category_id: int, category: CategoryUpdate) -> Category:
    """
    Update an existing category.
    
    Args:
        db: Database session
        category_id: ID of the category to update
        category: CategoryUpdate object containing the new data
        
    Returns:
        Updated Category object
        
    Raises:
        HTTPException: If validation fails, the category is not found, or a database error occurs
    """
    # Validate ID
    if category_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {category_id} - must be positive"
        )
    
    # Check if any fields are provided for update
    # We need to check if fields are present in the request, not just if they're None
    # For image_path, None is a valid value (to use placeholder)
    fields_provided = [
        hasattr(category, 'name') and category.name is not None,
        hasattr(category, 'image_path'),  # image_path can be None explicitly
        hasattr(category, 'is_deleted') and category.is_deleted is not None
    ]
    if not any(fields_provided):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )
    
    try:
        # Get the category to update
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if db_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        
        # Update name if provided
        if category.name is not None:
            # Check if the new name already exists for another category
            existing = db.query(Category).filter(
                and_(
                    Category.name == category.name,
                    Category.id != category_id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A category with the name '{category.name}' already exists"
                )
            
            db_category.name = category.name
        
        # Update image_path if explicitly included in the update request
        # Note: image_path can be explicitly set to None to use the placeholder image
        if hasattr(category, '__fields_set__') and 'image_path' in category.__fields_set__:
            db_category.image_path = category.image_path
        
        # Update is_deleted if provided
        if category.is_deleted is not None:
            db_category.is_deleted = category.is_deleted
        
        db.commit()
        db.refresh(db_category)
        return db_category
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate category name"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# DELETE category (soft delete)
def soft_delete_category(db: Session, category_id: int) -> bool:
    """
    Soft delete a category by setting is_deleted to True.
    
    Args:
        db: Database session
        category_id: ID of the category to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        HTTPException: If the ID is invalid or a database error occurs
    """
    # Validate ID
    if category_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {category_id} - must be positive"
        )
    
    try:
        # Check if category exists and is not already deleted
        db_category = db.query(Category).filter(
            and_(Category.id == category_id, Category.is_deleted == False)
        ).first()
        
        if db_category is None:
            return False
        
        # Soft delete by setting is_deleted to True
        db_category.is_deleted = True
        db.commit()
        return True
        # Note: We don't delete the image file on soft delete
        # This allows for easy restoration if the category is undeleted
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# HARD DELETE category (physical deletion)
def hard_delete_category(db: Session, category_id: int) -> bool:
    """
    Hard delete a category from the database.
    
    Args:
        db: Database session
        category_id: ID of the category to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        HTTPException: If the ID is invalid, the category is in use, or a database error occurs
    """
    # Validate ID
    if category_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {category_id} - must be positive"
        )
    
    try:
        # Check if category exists
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if db_category is None:
            return False
        
        # Store the image directory path before deletion for cleanup
        image_dir_path = db_category.image_path
        
        # Attempt to delete from database
        db.delete(db_category)
        db.commit()
        
        # Delete the associated image directory and all its contents if it exists
        if image_dir_path:
            # Get the full directory path
            full_dir_path = os.path.join(get_upload_dir(), image_dir_path)
            
            # Check if it's a directory and delete it with all contents
            if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                shutil.rmtree(full_dir_path)
            else:
                # Fallback to the old method for backward compatibility
                delete_file(image_dir_path)
            
        return True
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete category because it is in use by at least one product"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
