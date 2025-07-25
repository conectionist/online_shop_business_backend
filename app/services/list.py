from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List as TypeList, Optional

from app.models.list import List
from app.schemas.list import ListCreate, ListUpdate


def get_lists(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    include_deleted: bool = False
) -> TypeList[List]:
    """
    Get all lists with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_deleted: Whether to include soft-deleted records
        
    Returns:
        List of List objects
    """
    try:
        query = db.query(List)
        
        if not include_deleted and hasattr(List, 'is_deleted'):
            query = query.filter(List.is_deleted == False)
            
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_list_by_id(
    db: Session, 
    list_id: int,
    include_deleted: bool = False
) -> List:
    """
    Get a list by its ID.
    
    Args:
        db: Database session
        list_id: ID of the list to retrieve
        include_deleted: Whether to include soft-deleted records
        
    Returns:
        List object if found
        
    Raises:
        HTTPException: If list is not found or database error occurs
    """
    if list_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {list_id} - must be positive"
        )
    
    try:
        query = db.query(List).filter(List.id == list_id)
        
        if not include_deleted and hasattr(List, 'is_deleted'):
            query = query.filter(List.is_deleted == False)
            
        list_obj = query.first()
        
        if list_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"List with ID {list_id} not found"
            )
            
        return list_obj
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def create_list(db: Session, list_data: ListCreate) -> List:
    """
    Create a new list.
    
    Args:
        db: Database session
        list_data: Data for creating a new list
        
    Returns:
        Created List object
        
    Raises:
        HTTPException: If creation fails due to validation or database error
    """
    try:
        db_list = List(
            data=list_data.data,
            is_current=list_data.is_current,
            is_published=list_data.is_published,
            mesaj_introducere=list_data.mesaj_introducere,
            alte_detalii=list_data.alte_detalii,
            numar_whatsapp=list_data.numar_whatsapp,
            orare_livrari_id=list_data.orare_livrari_id
        )
        
        db.add(db_list)
        db.commit()
        db.refresh(db_list)
        return db_list
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e)
        if "foreign key constraint" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid delivery schedule ID: {list_data.orare_livrari_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity error: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def update_list(
    db: Session, 
    list_id: int, 
    list_data: ListUpdate
) -> List:
    """
    Update an existing list.
    
    Args:
        db: Database session
        list_id: ID of the list to update
        list_data: Data for updating the list
        
    Returns:
        Updated List object
        
    Raises:
        HTTPException: If update fails due to validation or database error
    """
    if list_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {list_id} - must be positive"
        )
    
    # Convert to dict and remove None values
    update_data = {k: v for k, v in list_data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    try:
        # Check if list exists and is not deleted
        db_list = db.query(List).filter(List.id == list_id)
        if hasattr(List, 'is_deleted'):
            db_list = db_list.filter(List.is_deleted == False)
            
        db_list = db_list.first()
        
        if db_list is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"List with ID {list_id} not found"
            )
        
        # Update fields
        for key, value in update_data.items():
            setattr(db_list, key, value)
        
        db.commit()
        db.refresh(db_list)
        return db_list
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e)
        if "foreign key constraint" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid delivery schedule ID in update data"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity error: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def delete_list(db: Session, list_id: int, soft_delete: bool = True) -> dict:
    """
    Delete a list by its ID.
    
    Args:
        db: Database session
        list_id: ID of the list to delete
        soft_delete: If True, perform soft delete; otherwise, hard delete
        
    Returns:
        Message indicating successful deletion
        
    Raises:
        HTTPException: If deletion fails or list is not found
    """
    if list_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {list_id} - must be positive"
        )
    
    try:
        db_list = db.query(List).filter(List.id == list_id)
        
        if hasattr(List, 'is_deleted') and soft_delete:
            # Check if already deleted
            if db.query(List).filter(List.id == list_id, List.is_deleted == False).first() is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"List with ID {list_id} not found or already deleted"
                )
            
            # Soft delete
            db_list.update({"is_deleted": True})
            db.commit()
            return {"message": f"List with ID {list_id} has been soft deleted"}
        else:
            # Hard delete
            db_list = db_list.first()
            if db_list is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"List with ID {list_id} not found"
                )
            
            db.delete(db_list)
            db.commit()
            return {"message": f"List with ID {list_id} has been permanently deleted"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
