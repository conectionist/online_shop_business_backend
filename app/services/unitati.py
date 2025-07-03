from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.unitati import Unitati
from app.schemas.unitati import UnitatCreate, UnitatUpdate


def get_unitati(db: Session, skip: int = 0, limit: int = 100) -> List[Unitati]:
    """Get all units with pagination"""
    return db.query(Unitati).offset(skip).limit(limit).all()


def get_unitat_by_id(db: Session, unitat_id: int) -> Optional[Unitati]:
    """Get a specific unit by ID"""
    return db.query(Unitati).filter(Unitati.id == unitat_id).first()


def get_unitat_by_denumire(db: Session, denumire: str) -> Optional[Unitati]:
    """Get a specific unit by name"""
    return db.query(Unitati).filter(Unitati.denumire == denumire).first()


def create_unitat(db: Session, unitat: UnitatCreate) -> Unitati:
    """Create a new unit"""
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


def update_unitat(db: Session, unitat_id: int, unitat: UnitatUpdate) -> Optional[Unitati]:
    """Update an existing unit"""
    db_unitat = get_unitat_by_id(db, unitat_id)
    if db_unitat is None:
        return None
        
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


def delete_unitat(db: Session, unitat_id: int) -> bool:
    """Delete a unit by ID"""
    db_unitat = get_unitat_by_id(db, unitat_id)
    if db_unitat is None:
        return False
        
    db.delete(db_unitat)
    db.commit()
    return True
