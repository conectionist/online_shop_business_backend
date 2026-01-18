from typing import List, Optional, List as TypeList
import os
import shutil

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, text, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.file_upload import delete_file, get_upload_dir
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


# GET all categories with pagination
def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
    """
    Retrieve all categories with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of Category objects
    """
    try:
        return db.query(Category).order_by(Category.order_index.asc(), Category.name.asc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# REORDER categories atomically
def reorder_categories(db: Session, ordered_ids: TypeList[int]):
    """Rewrite order_index based on the full ordered list of IDs.
    Requires the provided IDs to be an exact permutation of all existing categories.
    """
    if not ordered_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Ordered ID list must not be empty")

    try:
        # Fetch existing IDs
        existing_ids = [row[0] for row in db.query(Category.id).all()]
        total = len(existing_ids)

        # Validate counts and uniqueness
        if len(ordered_ids) != total:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="IDs list must include all categories")
        if len(set(ordered_ids)) != len(ordered_ids):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="IDs list contains duplicates")

        # Validate all IDs exist
        missing = [i for i in ordered_ids if i not in existing_ids]
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category IDs not found: {missing}")

        # 1) Temporarily negate order_index to avoid unique collisions during reassignment
        db.execute(text("UPDATE category SET order_index = -order_index"))

        # 2) Assign new order_index using a CASE expression
        # Build CASE ... WHEN id THEN position ... END
        case_clauses = []
        params = {}
        for position, cat_id in enumerate(ordered_ids, start=1):
            key_id = f"id_{position}"
            case_clauses.append(f"WHEN id = :{key_id} THEN {position}")
            params[key_id] = cat_id
        case_sql = " ".join(case_clauses)
        update_sql = f"UPDATE category SET order_index = CASE {case_sql} ELSE order_index END"
        db.execute(text(update_sql), params)

        db.commit()

        # Return updated list ordered by order_index, name
        return db.query(Category).order_by(Category.order_index.asc(), Category.name.asc()).all()
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error occurred: {str(e)}")


# GET category by ID
def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """
    Retrieve a specific category by its ID.
    
    Args:
        db: Database session
        category_id: ID of the category to retrieve
        
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
        category = db.query(Category).filter(Category.id == category_id).first()
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
def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """
    Retrieve a specific category by its name.
    
    Args:
        db: Database session
        name: Name of the category to retrieve
        
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
        return db.query(Category).filter(Category.name == name).first()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# CREATE new category
def create_category(db: Session, category: CategoryCreate) -> Category:
    """
    Create a new category.
    
    Args:
        db: Database session
        category: CategoryCreate object containing the data
        
    Returns:
        Created Category object
        
    Raises:
        HTTPException: If a duplicate name is found (status 409) or other validation/database errors occur
    """
    # Validate name (image_path is now optional)
    if not category.name or category.name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category name cannot be empty"
        )
    
    # Check if category with the same name already exists
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with name '{category.name}' already exists"
        )
    
    # Check for duplicate order_index
    existing_idx = db.query(Category).filter(Category.order_index == category.order_index).first()
    if existing_idx:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"order_index '{category.order_index}' is already used by another category"
        )
    
    # Create new category
    try:
        # image_path can be None, in which case the placeholder will be used
        db_category = Category(
            name=category.name,
            image_path=category.image_path,
            order_index=category.order_index
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
        hasattr(category, 'order_index') and category.order_index is not None
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
        
        # Update order_index if provided
        if category.order_index is not None:
            # Check for duplicate order_index if updating order_index
            existing_idx = db.query(Category).filter(
                and_(
                    Category.order_index == category.order_index,
                    Category.id != category_id
                )
            ).first()
            if existing_idx:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"order_index '{category.order_index}' is already used by another category"
                )
            db_category.order_index = category.order_index
        
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


# DELETE category
def delete_category(db: Session, category_id: int) -> bool:
    """
    Delete a category from the database.
    Also updates all products in this category to use the default "Uncategorized" category (ID 1).
    Also updates all list-product ordering records (liste_au_produse_ordered) that reference this category.
    Also removes all list-category ordering records (liste_au_categorii) that reference this category.
    
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
    
    # Protect against deletion of the default "Uncategorized" category
    from app.core.constants import UNCATEGORIZED_CATEGORY_ID
    if category_id == UNCATEGORIZED_CATEGORY_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete the default 'Uncategorized' category"
        )
    
    try:
        # Check if category exists
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if db_category is None:
            return False
        
        # Import models here to avoid circular imports
        from app.models.product import Product
        from app.models.list_product_ordered import ListProductOrdered
        from app.models.list_category import ListCategory
        
        # Update all products in this category to use the default "Uncategorized" category
        products_to_update = db.query(Product).filter(Product.category_id == category_id).all()
        for product in products_to_update:
            product.category_id = UNCATEGORIZED_CATEGORY_ID  # Default to "Uncategorized"
        
        # Update all list-product ordering records that reference this category
        # This preserves historical order data by moving it to the uncategorized category
        list_products_ordered = db.query(ListProductOrdered).filter(
            ListProductOrdered.category_id == category_id
        ).all()
        for list_product in list_products_ordered:
            list_product.category_id = UNCATEGORIZED_CATEGORY_ID
        
        # Delete all list-category ordering records that reference this category
        # These are just ordering metadata, so we can safely delete them
        db.query(ListCategory).filter(
            ListCategory.category_id == category_id
        ).delete()
        
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
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
