from typing import List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.unitati import Unitati
from app.schemas.unitati import UnitatCreate, UnitatUpdate


def get_unitati(db: Session, skip: int = 0, limit: int = 100) -> List[Unitati]:
    """Get all units with pagination"""
    try:
        return db.query(Unitati).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        # Log error here if you have logging configured
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_unitat_by_id(db: Session, unitat_id: int) -> Optional[Unitati]:
    """Get a specific unit by ID"""
    if unitat_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit ID must be a positive integer"
        )
    
    try:
        return db.query(Unitati).filter(Unitati.id == unitat_id).first()
    except SQLAlchemyError as e:
        # Log error here if you have logging configured
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_unitat_by_denumire(db: Session, denumire: str) -> Optional[Unitati]:
    """Get a specific unit by name"""
    if not denumire or denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit name cannot be empty"
        )
        
    try:
        return db.query(Unitati).filter(Unitati.denumire == denumire).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def create_unitat(db: Session, unitat: UnitatCreate) -> Unitati:
    """Create a new unit"""
    if not unitat.denumire or unitat.denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit name cannot be empty"
        )
        
    # Check if a unit with this name already exists
    existing = get_unitat_by_denumire(db, unitat.denumire)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A unit with the name '{unitat.denumire}' already exists"
        )
        
    try:
        db_unitat = Unitati(denumire=unitat.denumire)
        db.add(db_unitat)
        db.commit()
        db.refresh(db_unitat)
        return db_unitat
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A unit with the name '{unitat.denumire}' already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def update_unitat(db: Session, unitat_id: int, unitat: UnitatUpdate) -> Optional[Unitati]:
    """Update an existing unit"""
    if unitat_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit ID must be a positive integer"
        )
    
    # Check if there's something to update
    if unitat.denumire is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No update data provided"
        )
        
    if unitat.denumire and unitat.denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit name cannot be empty"
        )
    
    db_unitat = get_unitat_by_id(db, unitat_id)
    if db_unitat is None:
        return None
    
    # If a new name is provided, check it doesn't clash with another unit
    if unitat.denumire and unitat.denumire != db_unitat.denumire:
        existing = get_unitat_by_denumire(db, unitat.denumire)
        if existing and existing.id != unitat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A unit with the name '{unitat.denumire}' already exists"
            )
        
    try:
        # Update attributes if they are provided
        if unitat.denumire is not None:
            db_unitat.denumire = unitat.denumire
            
        db.commit()
        db.refresh(db_unitat)
        return db_unitat
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A unit with the name '{unitat.denumire}' already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def delete_unitat(db: Session, unitat_id: int) -> bool:
    """Delete a unit by ID"""
    if unitat_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit ID must be a positive integer"
        )
        
    db_unitat = get_unitat_by_id(db, unitat_id)
    if db_unitat is None:
        return False
    
    try:
        db.delete(db_unitat)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete unit because it is in use by at least one product."
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
