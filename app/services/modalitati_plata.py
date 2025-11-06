from typing import List, Optional, Union, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.modalitati_plata import ModalitatiPlata
from app.models.payment_type import PaymentType as PaymentTypeModel
from app.schemas.modalitati_plata import ModalitatePlataCreate, ModalitatePlataUpdate
from app.core.constants import PaymentType


def _get_required_fields_schema(payment_type_id: int) -> Optional[Dict[str, Any]]:
    """Get display schema for business payment information based on payment type ID
    
    Returns a dictionary with field definitions that client apps can use
    to display business payment information to customers (e.g., "Send payment to
    this Revolut number" or "Send payment to this IBAN").
    
    Note: This schema describes BUSINESS payment details (where they receive money),
    NOT customer input fields. The "validation" field contains hints for client-side
    validation when admins are creating/editing payment methods. These are NOT standard
    HTML5 validation types. Client apps should implement their own validation logic
    based on these hints. The "type" field uses standard HTML5 input types.
    
    Args:
        payment_type_id: The payment type ID
        
    Returns:
        Dictionary with field definitions for displaying business payment info, or None if no fields
    """
    if payment_type_id == PaymentType.REVOLUT:
        return {
            "phone_number": {
                "label": "Număr de telefon",
                "type": "tel",
                "required": True,
                "validation": "phone",
                "description": "Număr de telefon Revolut al afacerii (unde se primesc plățile)"
            }
        }
    elif payment_type_id == PaymentType.BANK_TRANSFER:
        return {
            "iban": {
                "label": "IBAN",
                "type": "text",
                "required": True,
                "validation": "iban",
                "description": "IBAN-ul contului bancar al afacerii (unde se primesc plățile)"
            },
            "recipient_name": {
                "label": "Nume destinatar",
                "type": "text",
                "required": True,
                "validation": "text",
                "description": "Numele titularului contului bancar al afacerii"
            }
        }
    # For custom, cash, physical_card, online_card - no required fields
    return None


def _validate_required_data(payment_type_id: int, required_data: Optional[Dict[str, Any]]) -> None:
    """Validate required_data matches payment type requirements
    
    Args:
        payment_type_id: The payment type ID
        required_data: The required_data dictionary to validate
        
    Raises:
        HTTPException: If validation fails
    """
    if payment_type_id == PaymentType.REVOLUT:
        if not required_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="required_data must contain 'phone_number' for Revolut payment type"
            )
        if "phone_number" not in required_data or not required_data.get("phone_number"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="required_data must contain a non-empty 'phone_number' for Revolut payment type"
            )
    elif payment_type_id == PaymentType.BANK_TRANSFER:
        if not required_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="required_data must contain 'iban' and 'recipient_name' for bank transfer payment type"
            )
        if "iban" not in required_data or not required_data.get("iban"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="required_data must contain a non-empty 'iban' for bank transfer payment type"
            )
        if "recipient_name" not in required_data or not required_data.get("recipient_name"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="required_data must contain a non-empty 'recipient_name' for bank transfer payment type"
            )
    elif payment_type_id in (PaymentType.CUSTOM, PaymentType.CASH, PaymentType.PHYSICAL_CARD, PaymentType.ONLINE_CARD):
        # These types should have no required_data or empty dict
        if required_data and required_data != {}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"required_data must be null or empty for payment type {payment_type_id}"
            )


def get_modalitati_plata(db: Session, skip: int = 0, limit: int = 100) -> List[ModalitatiPlata]:
    """Get all payment methods with pagination"""
    try:
        return db.query(ModalitatiPlata).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_modalitate_plata_by_id(db: Session, modalitate_id: int) -> Optional[ModalitatiPlata]:
    """Get a specific payment method by ID"""
    if modalitate_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment method ID must be a positive integer"
        )
    
    try:
        return db.query(ModalitatiPlata).filter(ModalitatiPlata.id == modalitate_id).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_modalitate_plata_by_name(db: Session, name: str) -> Optional[ModalitatiPlata]:
    """Get a specific payment method by internal name"""
    if not name or name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment method name cannot be empty"
        )
        
    try:
        return db.query(ModalitatiPlata).filter(ModalitatiPlata.name == name).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def create_modalitate_plata(db: Session, modalitate: ModalitatePlataCreate) -> ModalitatiPlata:
    """Create a new payment method"""
    if not modalitate.name or modalitate.name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment method name cannot be empty"
        )
        
    # Check if a payment method with this name already exists
    existing = get_modalitate_plata_by_name(db, modalitate.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A payment method with the name '{modalitate.name}' already exists"
        )
    
    # Validate payment_type_id exists
    payment_type = db.query(PaymentTypeModel).filter(PaymentTypeModel.id == modalitate.payment_type_id).first()
    if not payment_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment type with ID {modalitate.payment_type_id} does not exist"
        )
    
    # Validate required_data matches payment type requirements
    _validate_required_data(modalitate.payment_type_id, modalitate.required_data)
        
    try:
        db_modalitate = ModalitatiPlata(
            name=modalitate.name,
            description=modalitate.description,
            payment_type_id=modalitate.payment_type_id,
            required_data=modalitate.required_data
        )
        db.add(db_modalitate)
        db.commit()
        db.refresh(db_modalitate)
        return db_modalitate
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A payment method with the name '{modalitate.name}' already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def update_modalitate_plata(
    db: Session, 
    modalitate_id: int, 
    modalitate: ModalitatePlataUpdate
) -> Optional[ModalitatiPlata]:
    """Update an existing payment method"""
    if modalitate_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment method ID must be a positive integer"
        )
    
    try:
        db_modalitate = get_modalitate_plata_by_id(db, modalitate_id)
        if not db_modalitate:
            return None
            
        update_data = modalitate.model_dump(exclude_unset=True)
        
        # Check if there are any fields to update
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # If name is being updated, check for duplicates
        if "name" in update_data and update_data["name"]:
            existing = get_modalitate_plata_by_name(db, update_data["name"])
            if existing and existing.id != modalitate_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A payment method with the name '{update_data['name']}' already exists"
                )
        
        # Get the payment_type_id to validate (use updated value if provided, otherwise current value)
        payment_type_id_to_validate = update_data.get("payment_type_id", db_modalitate.payment_type_id)
        
        # Validate payment_type_id exists if being updated
        if "payment_type_id" in update_data:
            payment_type = db.query(PaymentTypeModel).filter(PaymentTypeModel.id == payment_type_id_to_validate).first()
            if not payment_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment type with ID {payment_type_id_to_validate} does not exist"
                )
        
        # Get the required_data to validate (use updated value if provided, otherwise current value)
        required_data_to_validate = update_data.get("required_data", db_modalitate.required_data)
        
        # Validate required_data matches payment type requirements
        _validate_required_data(payment_type_id_to_validate, required_data_to_validate)
        
        for field, value in update_data.items():
            setattr(db_modalitate, field, value)
            
        db.add(db_modalitate)
        db.commit()
        db.refresh(db_modalitate)
        return db_modalitate
        
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment method with this name already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def delete_modalitate_plata(db: Session, modalitate_id: int) -> bool:
    """Delete a payment method by ID"""
    if modalitate_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment method ID must be a positive integer"
        )
    
    try:
        db_modalitate = get_modalitate_plata_by_id(db, modalitate_id)
        if not db_modalitate:
            return False
            
        db.delete(db_modalitate)
        db.commit()
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete this payment method as it is being used by business details"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
