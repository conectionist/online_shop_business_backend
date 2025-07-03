from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.unitati import Unitat, UnitatCreate, UnitatUpdate
from app.services.unitati import (
    create_unitat,
    delete_unitat,
    get_unitat_by_id,
    get_unitati,
    update_unitat,
)

router = APIRouter()


@router.get("/", response_model=List[Unitat])
def read_unitati(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all units with pagination support"""
    unitati = get_unitati(db, skip=skip, limit=limit)
    return unitati


@router.post("/", response_model=Unitat, status_code=status.HTTP_201_CREATED)
def create_unitati(unitat: UnitatCreate, db: Session = Depends(get_db)):
    """Create a new unit"""
    return create_unitat(db=db, unitat=unitat)


@router.get("/{unitat_id}", response_model=Unitat)
def read_unitat(unitat_id: int, db: Session = Depends(get_db)):
    """Get a specific unit by ID"""
    db_unitat = get_unitat_by_id(db, unitat_id=unitat_id)
    if db_unitat is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    return db_unitat


@router.put("/{unitat_id}", response_model=Unitat)
def update_unitati(unitat_id: int, unitat: UnitatUpdate, db: Session = Depends(get_db)):
    """Update an existing unit"""
    db_unitat = update_unitat(db=db, unitat_id=unitat_id, unitat=unitat)
    if db_unitat is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    return db_unitat


@router.delete("/{unitat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unitati(unitat_id: int, db: Session = Depends(get_db)):
    """Delete a unit"""
    result = delete_unitat(db=db, unitat_id=unitat_id)
    if not result:
        raise HTTPException(status_code=404, detail="Unit not found")
    return None
