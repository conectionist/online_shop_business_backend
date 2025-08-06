from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from app.core.database import get_db
from app.services.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.list import List as ListSchema, ListCreate, ListUpdate
from app.services.list import (
    create_list,
    delete_list,
    get_list_by_id,
    get_lists,
    update_list,
)

router = APIRouter()


@router.get("/", response_model=List[ListSchema], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_lists(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    include_deleted: bool = Query(False, description="Whether to include soft-deleted records"),
    db: Session = Depends(get_db)
):
    """Get all lists with pagination"""
    return get_lists(db=db, skip=skip, limit=limit, include_deleted=include_deleted)


@router.get("/{list_id}", response_model=ListSchema, responses={
    200: {"description": "Successful response"},
    404: {"description": "List not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_list(
    list_id: int,
    include_deleted: bool = Query(False, description="Whether to include soft-deleted records"),
    db: Session = Depends(get_db)
):
    """Get a list by ID"""
    return get_list_by_id(db=db, list_id=list_id, include_deleted=include_deleted)


@router.post("/", response_model=ListSchema, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "List created successfully"},
    400: {"description": "Bad request, e.g., constraint violation"},
    401: {"description": "Unauthorized - Authentication required"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_list_endpoint(
    list_data: ListCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new list"""
    return create_list(db=db, list_data=list_data)


@router.put("/{list_id}", response_model=ListSchema, responses={
    200: {"description": "List updated successfully"},
    404: {"description": "List not found"},
    400: {"description": "Bad request, e.g., constraint violation or no valid fields"},
    401: {"description": "Unauthorized - Authentication required"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list to update"),
    list_data: ListUpdate = ...,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an existing list (PUT - full replacement)"""
    return update_list(db=db, list_id=list_id, list_data=list_data)


@router.patch("/{list_id}", response_model=ListSchema, responses={
    200: {"description": "List updated successfully"},
    400: {"description": "Bad request, e.g., no valid fields to update"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def patch_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list to update"),
    list_data: ListUpdate = ...,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Partially update an existing list (PATCH - only update provided fields)"""
    return update_list(db=db, list_id=list_id, list_data=list_data)


@router.delete("/{list_id}", response_model=Dict[str, str], responses={
    200: {"description": "List deleted successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_list_endpoint(
    list_id: int,
    soft_delete: bool = Query(True, description="If True, perform soft delete; otherwise, hard delete"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a list"""
    return delete_list(db=db, list_id=list_id, soft_delete=soft_delete)
