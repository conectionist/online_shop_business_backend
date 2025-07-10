from typing import List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.unitati import Unitati
from app.schemas.unitati import UnitCreate, UnitUpdate


def get_units(db: Session, skip: int = 0, limit: int = 100) -> List[Unitati]:
    """Get all units with pagination"""
    try:
        return db.query(Unitati).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        # Log error here if you have logging configured
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_unit_by_id(db: Session, unit_id: int) -> Optional[Unitati]:
    """Get a specific unit by ID"""
    if unit_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit ID must be a positive integer"
        )
    
    try:
        return db.query(Unitati).filter(Unitati.id == unit_id).first()
    except SQLAlchemyError as e:
        # Log error here if you have logging configured
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def get_unit_by_denumire(db: Session, denumire: str) -> Optional[Unitati]:
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


def create_unit(db: Session, unit: UnitCreate) -> Unitati:
    """Create a new unit"""
    if not unit.denumire or unit.denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit name cannot be empty"
        )
        
    # Check if a unit with this name already exists
    existing = get_unit_by_denumire(db, unit.denumire)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A unit with the name '{unit.denumire}' already exists"
        )
        
    try:
        db_unit = Unitati(denumire=unit.denumire)
        db.add(db_unit)
        db.commit()
        db.refresh(db_unit)
        return db_unit
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A unit with the name '{unit.denumire}' already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def update_unit(db: Session, unit_id: int, unit: UnitUpdate) -> Optional[Unitati]:
    """Update an existing unit"""
    if unit_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit ID must be a positive integer"
        )
    
    # Check if there's something to update
    if unit.denumire is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No update data provided"
        )
        
    if unit.denumire and unit.denumire.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit name cannot be empty"
        )
    
    db_unit = get_unit_by_id(db, unit_id)
    if db_unit is None:
        return None
    
    # If a new name is provided, check it doesn't clash with another unit
    if unit.denumire and unit.denumire != db_unit.denumire:
        existing = get_unit_by_denumire(db, unit.denumire)
        if existing and existing.id != unit_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A unit with the name '{unit.denumire}' already exists"
            )
        
    try:
        # Update attributes if they are provided
        if unit.denumire is not None:
            db_unit.denumire = unit.denumire
            
        db.commit()
        db.refresh(db_unit)
        return db_unit
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A unit with the name '{unit.denumire}' already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


def delete_unit(db: Session, unit_id: int) -> bool:
    """Delete a unit by ID"""
    if unit_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit ID must be a positive integer"
        )
        
    db_unit = get_unit_by_id(db, unit_id)
    if db_unit is None:
        return False
    
    try:
        db.delete(db_unit)
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
