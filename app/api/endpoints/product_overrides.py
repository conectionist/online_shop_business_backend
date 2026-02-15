from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import get_current_admin_from_cookie
from app.models.admin import Admin
from app.schemas.product_override import (
    ProductOverride,
    ProductOverrideCreate,
    ProductOverrideUpdate,
    ProductOverrideResponse,
    FieldNameEnum
)
from app.services.product_override import (
    get_product_overrides,
    get_product_override,
    create_product_override,
    update_product_override,
    delete_product_override,
    get_product_with_overrides
)

router = APIRouter()


@router.get("/", response_model=List[ProductOverrideResponse], tags=["Product Overrides"])
def get_overrides(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get all product overrides with optional filtering.
    
    - **product_id**: Filter by specific product ID
    - **is_active**: Filter by active status (True/False)
    """
    overrides = get_product_overrides(db, product_id=product_id, is_active=is_active)
    return overrides


@router.get("/fields", response_model=List[str], tags=["Product Overrides"])
def get_available_fields():
    """
    Get list of available fields that can be overridden.
    """
    return [field.value for field in FieldNameEnum]


@router.get("/{override_id}", response_model=ProductOverrideResponse, tags=["Product Overrides"])
def get_override(
    override_id: int = Path(..., gt=0, description="ID of the override to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a specific product override by ID.
    
    - **override_id**: The ID of the override to retrieve
    """
    override = get_product_override(db, override_id)
    return override


@router.post("/", response_model=ProductOverrideResponse, status_code=status.HTTP_201_CREATED, tags=["Product Overrides"], responses={
    201: {"description": "Product override created successfully"},
    400: {"description": "Bad request, e.g., invalid data"},
    401: {"description": "Unauthorized - Authentication required"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_override(
    override_data: ProductOverrideCreate,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Create a new product override.
    
    - **produse_id**: ID of the product to override
    - **field_name**: Field to override (price, description, availability)
    - **new_value**: New value for the field
    - **old_value**: Original value (optional, for reference)
    - **notes**: Optional notes about the override
    - **is_active**: Whether the override is active (default: True)
    """
    override = create_product_override(db, override_data)
    return override


@router.put("/{override_id}", response_model=ProductOverrideResponse, tags=["Product Overrides"], responses={
    200: {"description": "Product override updated successfully"},
    400: {"description": "Bad request, e.g., invalid data"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Product override not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_override(
    override_id: int = Path(..., gt=0, description="ID of the override to update"),
    override_data: ProductOverrideUpdate = None,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Update an existing product override.
    
    - **override_id**: The ID of the override to update
    - **new_value**: New override value (optional)
    - **notes**: Optional notes about the override
    - **is_active**: Whether the override is active (optional)
    """
    if override_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body is required"
        )
    
    override = update_product_override(db, override_id, override_data)
    return override


@router.delete("/{override_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Product Overrides"], responses={
    204: {"description": "Product override deleted successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "Product override not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_override(
    override_id: int = Path(..., gt=0, description="ID of the override to delete"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Delete a product override.
    
    - **override_id**: The ID of the override to delete
    """
    delete_product_override(db, override_id)
    return None


@router.get("/product/{product_id}/with-overrides", tags=["Product Overrides"])
def get_product_overrides_data(
    product_id: int = Path(..., gt=0, description="ID of the product to get with overrides"),
    db: Session = Depends(get_db)
):
    """
    Get a product with all its active overrides.
    
    - **product_id**: The ID of the product to retrieve with overrides
    """
    product_data = get_product_with_overrides(db, product_id)
    return product_data 