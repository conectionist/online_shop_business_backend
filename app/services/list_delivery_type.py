from typing import List as TypeList
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.list import List
from app.models.delivery_type import DeliveryType
from app.models.list_delivery_type import ListDeliveryType
from app.schemas.list_delivery_type import ListDeliveryTypeCreate, ListDeliveryTypeResponse


def get_list_delivery_types(db: Session, list_id: int) -> TypeList[DeliveryType]:
    """
    Get all delivery types for a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        
    Returns:
        List of DeliveryType objects
        
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
        # Get delivery types through the many-to-many relationship, ordered by order_index then denumire
        delivery_types = (
            db.query(DeliveryType)
            .join(ListDeliveryType)
            .filter(ListDeliveryType.liste_id == list_id)
            .order_by(DeliveryType.order_index.asc(), DeliveryType.denumire.asc())
            .all()
        )
        return delivery_types
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def add_delivery_type_to_list(db: Session, list_id: int, delivery_type_id: int) -> ListDeliveryType:
    """
    Add a delivery type to a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        delivery_type_id: ID of the delivery type to add
        
    Returns:
        Created ListDeliveryType relationship
        
    Raises:
        HTTPException: If list or delivery type not found, or relationship already exists
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if delivery type exists
    delivery_type = db.query(DeliveryType).filter(DeliveryType.id == delivery_type_id).first()
    if not delivery_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery type with ID {delivery_type_id} not found"
        )
    
    # Check if relationship already exists
    existing_relationship = db.query(ListDeliveryType).filter(
        ListDeliveryType.liste_id == list_id,
        ListDeliveryType.tipuri_livrare_id == delivery_type_id
    ).first()
    
    if existing_relationship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery type {delivery_type_id} is already in list {list_id}"
        )
    
    try:
        # Create the relationship
        list_delivery_type = ListDeliveryType(liste_id=list_id, tipuri_livrare_id=delivery_type_id)
        db.add(list_delivery_type)
        db.commit()
        db.refresh(list_delivery_type)
        return list_delivery_type
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add delivery type to list: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def remove_delivery_type_from_list(db: Session, list_id: int, delivery_type_id: int) -> bool:
    """
    Remove a delivery type from a list.
    
    Args:
        db: Database session
        list_id: ID of the list
        delivery_type_id: ID of the delivery type to remove
        
    Returns:
        True if delivery type was removed, False if relationship didn't exist
        
    Raises:
        HTTPException: If list or delivery type not found
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if delivery type exists
    delivery_type = db.query(DeliveryType).filter(DeliveryType.id == delivery_type_id).first()
    if not delivery_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery type with ID {delivery_type_id} not found"
        )
    
    try:
        # Find and delete the relationship
        relationship = db.query(ListDeliveryType).filter(
            ListDeliveryType.liste_id == list_id,
            ListDeliveryType.tipuri_livrare_id == delivery_type_id
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


def replace_list_delivery_types(db: Session, list_id: int, delivery_type_ids: TypeList[int]) -> TypeList[DeliveryType]:
    """
    Replace all delivery types in a list with the given delivery type IDs.
    
    Args:
        db: Database session
        list_id: ID of the list
        delivery_type_ids: List of delivery type IDs to add to the list
        
    Returns:
        List of DeliveryType objects in the list
        
    Raises:
        HTTPException: If list not found or any delivery type doesn't exist
    """
    # Check if list exists
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check if all delivery types exist
    delivery_types = db.query(DeliveryType).filter(DeliveryType.id.in_(delivery_type_ids)).all()
    if len(delivery_types) != len(delivery_type_ids):
        found_ids = [dt.id for dt in delivery_types]
        missing_ids = [dtid for dtid in delivery_type_ids if dtid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery types with IDs {missing_ids} not found"
        )
    
    try:
        # Remove all existing relationships
        db.query(ListDeliveryType).filter(ListDeliveryType.liste_id == list_id).delete()
        
        # Add new relationships
        for delivery_type_id in delivery_type_ids:
            list_delivery_type = ListDeliveryType(liste_id=list_id, tipuri_livrare_id=delivery_type_id)
            db.add(list_delivery_type)
        
        db.commit()
        
        # Return the delivery types
        return delivery_types
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        ) 