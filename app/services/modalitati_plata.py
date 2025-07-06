from typing import List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.modalitati_plata import ModalitatiPlata
from app.schemas.modalitati_plata import ModalitatePlataCreate, ModalitatePlataUpdate


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


def get_modalitate_plata_by_denumire(db: Session, denumire: str) -> Optional[ModalitatiPlata]:
    """Get a specific payment method by name"""
    if not denumire or denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment method name cannot be empty"
        )
        
    try:
        return db.query(ModalitatiPlata).filter(ModalitatiPlata.denumire == denumire).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def create_modalitate_plata(db: Session, modalitate: ModalitatePlataCreate) -> ModalitatiPlata:
    """Create a new payment method"""
    if not modalitate.denumire or modalitate.denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment method name cannot be empty"
        )
        
    # Check if a payment method with this name already exists
    existing = get_modalitate_plata_by_denumire(db, modalitate.denumire)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A payment method with the name '{modalitate.denumire}' already exists"
        )
        
    try:
        db_modalitate = ModalitatiPlata(denumire=modalitate.denumire)
        db.add(db_modalitate)
        db.commit()
        db.refresh(db_modalitate)
        return db_modalitate
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A payment method with the name '{modalitate.denumire}' already exists"
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
        
        # If denumire is being updated, check for duplicates
        if "denumire" in update_data and update_data["denumire"]:
            existing = get_modalitate_plata_by_denumire(db, update_data["denumire"])
            if existing and existing.id != modalitate_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A payment method with the name '{update_data['denumire']}' already exists"
                )
        
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
            status_code=status.HTTP_400_BAD_REQUEST,
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
