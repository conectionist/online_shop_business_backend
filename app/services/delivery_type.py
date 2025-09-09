from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.delivery_type import DeliveryType
from app.schemas.delivery_type import DeliveryTypeCreate, DeliveryTypeUpdate


# GET all delivery types with pagination
def get_delivery_types(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve all delivery types with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of DeliveryType objects
    """
    try:
        return (
            db.query(DeliveryType)
            .order_by(DeliveryType.order_index.asc(), DeliveryType.denumire.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# GET delivery type by ID
def get_delivery_type_by_id(db: Session, delivery_type_id: int):
    """
    Retrieve a specific delivery type by its ID.
    
    Args:
        db: Database session
        delivery_type_id: ID of the delivery type to retrieve
        
    Returns:
        DeliveryType object if found
        
    Raises:
        HTTPException: If the ID is invalid or the delivery type is not found
    """
    if delivery_type_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {delivery_type_id} - must be positive"
        )
    
    try:
        delivery_type = db.query(DeliveryType).filter(DeliveryType.id == delivery_type_id).first()
        if delivery_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery type with ID {delivery_type_id} not found"
            )
        return delivery_type
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# CREATE new delivery type
def create_delivery_type(db: Session, delivery_type: DeliveryTypeCreate):
    """
    Create a new delivery type.
    
    Args:
        db: Database session
        delivery_type: DeliveryTypeCreate object containing the data
        
    Returns:
        Created DeliveryType object
        
    Raises:
        HTTPException: If validation fails or a duplicate is found
    """
    # Validate inputs
    if not delivery_type.denumire or delivery_type.denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Delivery type name cannot be empty"
        )
    
    # Check for duplicate name
    existing = db.query(DeliveryType).filter(DeliveryType.denumire == delivery_type.denumire).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A delivery type with the name '{delivery_type.denumire}' already exists"
        )
    # Check for duplicate order_index
    existing_idx = db.query(DeliveryType).filter(DeliveryType.order_index == delivery_type.order_index).first()
    if existing_idx:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"order_index '{delivery_type.order_index}' is already used by another delivery type"
        )
    
    try:
        db_delivery_type = DeliveryType(
            denumire=delivery_type.denumire,
            description=delivery_type.description,
            order_index=delivery_type.order_index,
        )
        db.add(db_delivery_type)
        db.commit()
        db.refresh(db_delivery_type)
        return db_delivery_type
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate delivery type (name or order_index)"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# UPDATE existing delivery type
def update_delivery_type(db: Session, delivery_type_id: int, delivery_type: DeliveryTypeUpdate):
    """
    Update an existing delivery type.
    
    Args:
        db: Database session
        delivery_type_id: ID of the delivery type to update
        delivery_type: DeliveryTypeUpdate object containing the new data
        
    Returns:
        Updated DeliveryType object
        
    Raises:
        HTTPException: If the ID is invalid, the delivery type is not found, 
                      or a duplicate name is provided
    """
    # Validate ID
    if delivery_type_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {delivery_type_id} - must be positive"
        )
    
    # Check if there are any fields to update
    update_data = {}
    if delivery_type.denumire is not None:
        update_data["denumire"] = delivery_type.denumire
    if delivery_type.description is not None:
        update_data["description"] = delivery_type.description
    if delivery_type.order_index is not None:
        update_data["order_index"] = delivery_type.order_index
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    try:
        # Check if delivery type exists
        db_delivery_type = db.query(DeliveryType).filter(DeliveryType.id == delivery_type_id).first()
        if db_delivery_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery type with ID {delivery_type_id} not found"
            )
        
        # Check for duplicate name if updating name
        if "denumire" in update_data:
            existing = db.query(DeliveryType).filter(
                DeliveryType.denumire == update_data["denumire"],
                DeliveryType.id != delivery_type_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A delivery type with the name '{update_data['denumire']}' already exists"
                )
        # Check for duplicate order_index if updating order_index
        if "order_index" in update_data:
            existing_idx = db.query(DeliveryType).filter(
                DeliveryType.order_index == update_data["order_index"],
                DeliveryType.id != delivery_type_id
            ).first()
            if existing_idx:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"order_index '{update_data['order_index']}' is already used by another delivery type"
                )
        
        # Apply updates
        for key, value in update_data.items():
            setattr(db_delivery_type, key, value)
        
        db.commit()
        db.refresh(db_delivery_type)
        return db_delivery_type
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate delivery type name"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# DELETE delivery type
def delete_delivery_type(db: Session, delivery_type_id: int):
    """
    Delete a delivery type.
    
    Args:
        db: Database session
        delivery_type_id: ID of the delivery type to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        HTTPException: If the ID is invalid or a database error occurs
    """
    # Validate ID
    if delivery_type_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {delivery_type_id} - must be positive"
        )
    
    try:
        # Check if delivery type exists
        db_delivery_type = db.query(DeliveryType).filter(DeliveryType.id == delivery_type_id).first()
        if db_delivery_type is None:
            return False
        
        db.delete(db_delivery_type)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
