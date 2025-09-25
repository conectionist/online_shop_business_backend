from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.business_details import BusinessDetails
from app.schemas.business_details import BusinessDetailsCreate, BusinessDetailsUpdate
from app.utils.macro_processor import process_macros


# GET all business details with pagination
def get_business_details(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve all business details records with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of BusinessDetails objects
    """
    try:
        records = db.query(BusinessDetails).offset(skip).limit(limit).all()
        # For each record, expose raw value and process macros in-place for the main field
        for rec in records:
            try:
                if hasattr(rec, 'list_not_available_msg'):
                    rec.list_not_available_msg_raw = rec.list_not_available_msg
                    if rec.list_not_available_msg:
                        rec.list_not_available_msg = process_macros(rec.list_not_available_msg)
            except Exception:
                # Fail-safe: if processing fails, leave the original text
                pass
        return records
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# GET business details by ID
def get_business_details_by_id(db: Session, business_details_id: int):
    """
    Retrieve a specific business details record by its ID.
    
    Args:
        db: Database session
        business_details_id: ID of the business details to retrieve
        
    Returns:
        BusinessDetails object if found
        
    Raises:
        HTTPException: If the ID is invalid or the business details is not found
    """
    if business_details_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {business_details_id} - must be positive"
        )
    
    try:
        business_details = db.query(BusinessDetails).filter(BusinessDetails.id == business_details_id).first()
        if business_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business details with ID {business_details_id} not found"
            )
        # Expose raw and process macros in-place for response
        try:
            business_details.list_not_available_msg_raw = business_details.list_not_available_msg
            if business_details.list_not_available_msg:
                business_details.list_not_available_msg = process_macros(business_details.list_not_available_msg)
        except Exception:
            pass
        return business_details
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# CREATE new business details
def create_business_details(db: Session, business_details: BusinessDetailsCreate):
    """
    Create a new business details record.
    
    Args:
        db: Database session
        business_details: BusinessDetailsCreate object containing the data
        
    Returns:
        Created BusinessDetails object
        
    Raises:
        HTTPException: If a database error occurs or if a record already exists
    """
    try:
        # Check if any business details record already exists
        existing_count = db.query(BusinessDetails).count()
        
        if existing_count > 0:
            # Business details is a singleton entity, so we should not create multiple records
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Business details record already exists. Use PUT to update the existing record."
            )
            
        # Create new record
        db_business_details = BusinessDetails(
            adresa=business_details.adresa,
            telefon=business_details.telefon,
            logo_path=business_details.logo_path,
            motto=business_details.motto,
            list_not_available_msg=business_details.list_not_available_msg,
            alte_detalii=business_details.alte_detalii,
            delivery_tax=business_details.delivery_tax,
            # Optional merchant identity fields
            business_name=business_details.business_name,
            registration_number=business_details.registration_number,
            CUI=business_details.CUI,
            email=business_details.email,
            operating_hours=business_details.operating_hours,
            representative=business_details.representative
        )
        db.add(db_business_details)
        db.commit()
        db.refresh(db_business_details)
        return db_business_details
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict error: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# UPDATE existing business details
def update_business_details(db: Session, business_details_id: int, business_details: BusinessDetailsUpdate):
    """
    Update an existing business details record.
    
    Args:
        db: Database session
        business_details_id: ID of the business details to update
        business_details: BusinessDetailsUpdate object containing the new data
        
    Returns:
        Updated BusinessDetails object
        
    Raises:
        HTTPException: If the ID is invalid, the business details is not found,
                      or a database error occurs
    """
    # Validate ID
    if business_details_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {business_details_id} - must be positive"
        )
    
    # Prepare update data
    # Extract only provided fields; Pydantic v2 prefers model_dump
    try:
        update_data = business_details.model_dump(exclude_unset=True)
    except Exception:
        update_data = business_details.dict(exclude_unset=True)

    # Normalize any blank strings to None (defensive; validators already handle most cases)
    for key, value in list(update_data.items()):
        if isinstance(value, str) and value.strip() == "":
            update_data[key] = None
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    try:
        # Check if business details exists
        db_business_details = db.query(BusinessDetails).filter(BusinessDetails.id == business_details_id).first()
        if db_business_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business details with ID {business_details_id} not found"
            )
        
        # Apply updates
        for key, value in update_data.items():
            setattr(db_business_details, key, value)
        
        db.commit()
        db.refresh(db_business_details)
        return db_business_details
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


# DELETE business details
def delete_business_details(db: Session, business_details_id: int):
    """
    Delete a business details record.
    
    Args:
        db: Database session
        business_details_id: ID of the business details to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        HTTPException: If the ID is invalid or a database error occurs
    """
    # Validate ID
    if business_details_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {business_details_id} - must be positive"
        )
    
    try:
        # Check if business details exists
        db_business_details = db.query(BusinessDetails).filter(BusinessDetails.id == business_details_id).first()
        if db_business_details is None:
            return False
        
        db.delete(db_business_details)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
