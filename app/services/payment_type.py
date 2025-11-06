from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.payment_type import PaymentType
from app.schemas.payment_type import PaymentType as PaymentTypeSchema


def get_payment_types(db: Session) -> List[PaymentType]:
    """Get all payment types"""
    try:
        return db.query(PaymentType).order_by(PaymentType.id).all()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_payment_type_by_id(db: Session, payment_type_id: int) -> Optional[PaymentType]:
    """Get a specific payment type by ID"""
    if payment_type_id < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment type ID must be a non-negative integer"
        )
    
    try:
        return db.query(PaymentType).filter(PaymentType.id == payment_type_id).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_payment_type_by_name(db: Session, name: str) -> Optional[PaymentType]:
    """Get a specific payment type by name enum"""
    if not name or name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment type name cannot be empty"
        )
        
    try:
        return db.query(PaymentType).filter(PaymentType.name == name).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

