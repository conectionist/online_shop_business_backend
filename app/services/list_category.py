from typing import List as TypeList
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.list import List
from app.models.category import Category
from app.models.list_category import ListCategory


def get_list_categories_ordered(db: Session, list_id: int) -> TypeList[dict]:
    """
    Get all categories in a list, ordered by their position.
    
    Args:
        db: Database session
        list_id: ID of the list
        
    Returns:
        List of Category objects with position information, ordered by position
        
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
        # Get categories with their position information, ordered by position
        list_categories = db.query(ListCategory).filter(
            ListCategory.liste_id == list_id
        ).order_by(ListCategory.position).all()
        
        result = []
        for list_category in list_categories:
            category = list_category.category
            category_dict = {
                "id": category.id,
                "name": category.name,
                "image_path": category.image_path,
                "position": list_category.position,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "is_deleted": category.is_deleted
            }
            result.append(category_dict)
        
        return result
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def add_category_to_list(db: Session, list_id: int, category_id: int, position: int = None) -> ListCategory:
    """
    Add a category to a list at a specific position.
    
    Args:
        db: Database session
        list_id: ID of the list
        category_id: ID of the category to add
        position: Position where to add the category (if None, adds at the end)
        
    Returns:
        Created ListCategory relationship
        
    Raises:
        HTTPException: If list or category not found, or relationship already exists
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Check if relationship already exists
    existing_relationship = db.query(ListCategory).filter(
        ListCategory.liste_id == list_id,
        ListCategory.category_id == category_id
    ).first()
    
    if existing_relationship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category {category_id} is already in list {list_id}"
        )
    
    try:
        # If position is not specified, add at the end
        if position is None:
            max_position = db.query(ListCategory).filter(
                ListCategory.liste_id == list_id
            ).with_entities(func.max(ListCategory.position)).scalar()
            position = 0 if max_position is None else max_position + 1
        
        # Create the relationship
        list_category = ListCategory(
            liste_id=list_id,
            category_id=category_id,
            position=position
        )
        db.add(list_category)
        db.commit()
        db.refresh(list_category)
        return list_category
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add category to list: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def update_category_position(db: Session, list_id: int, category_id: int, new_position: int) -> ListCategory:
    """
    Update the position of a category in a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        category_id: ID of the category to update
        new_position: New position for the category
        
    Returns:
        Updated ListCategory relationship
        
    Raises:
        HTTPException: If list, category, or relationship not found
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Check if relationship exists
    list_category = db.query(ListCategory).filter(
        ListCategory.liste_id == list_id,
        ListCategory.category_id == category_id
    ).first()
    
    if not list_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} is not in list {list_id}"
        )
    
    try:
        old_position = list_category.position
        
        # If position isn't changing, nothing to do
        if old_position == new_position:
            return list_category
        
        # Get all categories in this list, ordered by position
        categories = db.query(ListCategory).filter(
            ListCategory.liste_id == list_id
        ).order_by(ListCategory.position).all()
        
        # Validate new position
        if new_position < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid position {new_position}. Must be non-negative"
            )
        
        # Update positions of other categories
        if old_position < new_position:
            # Moving forward: shift categories between old and new position back by 1
            db.query(ListCategory).filter(
                ListCategory.liste_id == list_id,
                ListCategory.position > old_position,
                ListCategory.position <= new_position
            ).update({ListCategory.position: ListCategory.position - 1})
        else:
            # Moving backward: shift categories between new and old position forward by 1
            db.query(ListCategory).filter(
                ListCategory.liste_id == list_id,
                ListCategory.position >= new_position,
                ListCategory.position < old_position
            ).update({ListCategory.position: ListCategory.position + 1})
        
        # Update the target category's position
        list_category.position = new_position
        db.commit()
        db.refresh(list_category)
        return list_category
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def remove_category_from_list(db: Session, list_id: int, category_id: int) -> bool:
    """
    Remove a category from a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        category_id: ID of the category to remove
        
    Returns:
        True if category was removed, False if relationship didn't exist
        
    Raises:
        HTTPException: If list or category not found
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    try:
        # Find and delete the relationship
        relationship = db.query(ListCategory).filter(
            ListCategory.liste_id == list_id,
            ListCategory.category_id == category_id
        ).first()
        
        if not relationship:
            return False
        
        # Get the position of the category being removed
        removed_position = relationship.position
        
        # Delete the relationship
        db.delete(relationship)
        
        # Update positions of remaining categories (shift them down)
        db.query(ListCategory).filter(
            ListCategory.liste_id == list_id,
            ListCategory.position > removed_position
        ).update({ListCategory.position: ListCategory.position - 1})
        
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        ) 