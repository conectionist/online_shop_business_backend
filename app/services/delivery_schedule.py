from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.delivery_schedule import DeliverySchedule
from app.schemas.delivery_schedule import DeliveryScheduleCreate, DeliveryScheduleUpdate


# GET all delivery schedules with pagination
def get_delivery_schedules(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve all delivery schedules with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of DeliverySchedule objects
    """
    try:
        return db.query(DeliverySchedule).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# GET delivery schedule by ID
def get_delivery_schedule_by_id(db: Session, delivery_schedule_id: int):
    """
    Retrieve a specific delivery schedule by its ID.
    
    Args:
        db: Database session
        delivery_schedule_id: ID of the delivery schedule to retrieve
        
    Returns:
        DeliverySchedule object if found
        
    Raises:
        HTTPException: If the ID is invalid or the delivery schedule is not found
    """
    if delivery_schedule_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {delivery_schedule_id} - must be positive"
        )
    
    try:
        delivery_schedule = db.query(DeliverySchedule).filter(DeliverySchedule.id == delivery_schedule_id).first()
        if delivery_schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery schedule with ID {delivery_schedule_id} not found"
            )
        return delivery_schedule
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# CREATE new delivery schedule
def create_delivery_schedule(db: Session, delivery_schedule: DeliveryScheduleCreate):
    """
    Create a new delivery schedule.
    
    Args:
        db: Database session
        delivery_schedule: DeliveryScheduleCreate object containing the data
        
    Returns:
        Created DeliverySchedule object
        
    Raises:
        HTTPException: If validation fails
    """
    # Validate inputs
    if not delivery_schedule.orar_livrari or delivery_schedule.orar_livrari.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Delivery schedule information cannot be empty"
        )
    
    try:
        db_delivery_schedule = DeliverySchedule(orar_livrari=delivery_schedule.orar_livrari)
        db.add(db_delivery_schedule)
        db.commit()
        db.refresh(db_delivery_schedule)
        return db_delivery_schedule
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# UPDATE existing delivery schedule
def update_delivery_schedule(db: Session, delivery_schedule_id: int, delivery_schedule: DeliveryScheduleUpdate):
    """
    Update an existing delivery schedule.
    
    Args:
        db: Database session
        delivery_schedule_id: ID of the delivery schedule to update
        delivery_schedule: DeliveryScheduleUpdate object containing the new data
        
    Returns:
        Updated DeliverySchedule object
        
    Raises:
        HTTPException: If the ID is invalid or the delivery schedule is not found
    """
    # Validate ID
    if delivery_schedule_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {delivery_schedule_id} - must be positive"
        )
    
    # Check if there are any fields to update
    update_data = {}
    if delivery_schedule.orar_livrari is not None:
        update_data["orar_livrari"] = delivery_schedule.orar_livrari
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    try:
        # Check if delivery schedule exists
        db_delivery_schedule = db.query(DeliverySchedule).filter(DeliverySchedule.id == delivery_schedule_id).first()
        if db_delivery_schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery schedule with ID {delivery_schedule_id} not found"
            )
        
        # Apply updates
        for key, value in update_data.items():
            setattr(db_delivery_schedule, key, value)
        
        db.commit()
        db.refresh(db_delivery_schedule)
        return db_delivery_schedule
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# DELETE delivery schedule
def delete_delivery_schedule(db: Session, delivery_schedule_id: int):
    """
    Delete a delivery schedule.
    
    Args:
        db: Database session
        delivery_schedule_id: ID of the delivery schedule to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        HTTPException: If the ID is invalid or a database error occurs
    """
    # Validate ID
    if delivery_schedule_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {delivery_schedule_id} - must be positive"
        )
    
    try:
        # Check if delivery schedule exists
        db_delivery_schedule = db.query(DeliverySchedule).filter(DeliverySchedule.id == delivery_schedule_id).first()
        if db_delivery_schedule is None:
            return False
        
        db.delete(db_delivery_schedule)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
