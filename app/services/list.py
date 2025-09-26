from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List as TypeList, Optional

from app.models.list import List
from app.schemas.list import ListCreate, ListUpdate


def _ensure_single_published_list(db: Session, list_id: int = None):
    """
    Ensure only one list is published at a time.
    Unpublishes all other lists when a new one is being published.
    
    Args:
        db: Database session
        list_id: ID of the list being published (optional, to exclude from unpublishing)
    """
    try:
        # Unpublish all other published lists
        query = db.query(List).filter(List.is_published == True)
        if list_id is not None:
            query = query.filter(List.id != list_id)
        
        published_lists = query.all()
        for published_list in published_lists:
            published_list.is_published = False
        
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred while managing published lists: {str(e)}"
        )


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
            orare_livrari_id=list_data.orare_livrari_id,
            expiration_date=list_data.expiration_date
        )
        
        db.add(db_list)
        db.commit()
        db.refresh(db_list)
        
        # If this list is being published, unpublish all others AFTER successful creation
        if list_data.is_published:
            _ensure_single_published_list(db, db_list.id)
        
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
    
    # Convert to dict and remove None values, but allow None for expiration_date when explicitly provided
    update_data = {}
    for k, v in list_data.model_dump(exclude_unset=True, exclude_none=False).items():
        if v is not None or k == 'expiration_date':
            update_data[k] = v
    
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
        
        # If this list is being published, unpublish all others AFTER successful update
        if 'is_published' in update_data and update_data['is_published'] is True:
            _ensure_single_published_list(db, list_id)
        
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


def clone_list(db: Session, source_list_id: int) -> List:
    """
    Clone an existing list with all its structure, ordering, and products.
    
    Args:
        db: Database session
        source_list_id: ID of the list to clone
        
    Returns:
        Newly created List object (clone)
        
    Raises:
        HTTPException: If cloning fails or source list is not found
    """
    if source_list_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid source list ID: {source_list_id} - must be positive"
        )
    
    try:
        # Get the source list
        source_list = get_list_by_id(db=db, list_id=source_list_id, include_deleted=False)
        
        # Create new list with same metadata (new ID will be auto-generated)
        new_list = List(
            data=source_list.data,
            is_current=False,  # New list should not be current by default
            is_published=False,  # New list should not be published by default
            mesaj_introducere=source_list.mesaj_introducere,
            alte_detalii=source_list.alte_detalii,
            numar_whatsapp=source_list.numar_whatsapp,
            orare_livrari_id=source_list.orare_livrari_id,
            expiration_date=source_list.expiration_date
        )
        
        db.add(new_list)
        db.flush()  # Flush to get the new ID without committing
        
        # Clone category ordering
        from app.models.list_category import ListCategory
        source_categories = db.query(ListCategory).filter(
            ListCategory.liste_id == source_list_id
        ).order_by(ListCategory.position).all()
        
        for source_cat in source_categories:
            new_category = ListCategory(
                liste_id=new_list.id,
                category_id=source_cat.category_id,
                position=source_cat.position
            )
            db.add(new_category)
        
        # Clone product ordering within categories
        from app.models.list_product_ordered import ListProductOrdered
        source_products = db.query(ListProductOrdered).filter(
            ListProductOrdered.liste_id == source_list_id
        ).order_by(ListProductOrdered.category_id, ListProductOrdered.position).all()
        
        for source_prod in source_products:
            new_product = ListProductOrdered(
                liste_id=new_list.id,
                produse_id=source_prod.produse_id,
                category_id=source_prod.category_id,
                position=source_prod.position,
                stoc_produs=source_prod.stoc_produs
            )
            db.add(new_product)
        
        # Commit all changes
        db.commit()
        db.refresh(new_list)
        
        return new_list
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for source list not found)
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred during cloning: {str(e)}"
        )
