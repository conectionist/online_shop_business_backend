from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_db
from app.core.cache import (
    build_cache_key, get_cached_response, set_cached_response,
    acquire_computation_lock, release_computation_lock, wait_for_cache,
    invalidate_for_list,
)
from app.services.auth import get_current_admin_from_cookie
from app.models.admin import Admin
from app.schemas.product import Product as ProductSchema
from app.services.list_product import (
    get_list_products,
    add_product_to_list,
    remove_product_from_list,
    replace_list_products,
    add_products_to_list,
    update_product_availability,
)

class AddProductRequest(BaseModel):
    stoc_produs: Optional[int] = Field(None, ge=0, description="Available stock for this product in this list")


class UpdateAvailabilityRequest(BaseModel):
    stoc_produs: Optional[int] = Field(None, ge=0, description="Availability/stock for this product in this list (null or >=0)")

    @field_validator("stoc_produs")
    @classmethod
    def validate_stoc_produs(cls, v):
        # Accept None or any integer >= 0 (pydantic ge=0 enforces non-negative when not None)
        return v

router = APIRouter()


@router.get("/{list_id}/products", responses={
    200: {"description": "List of products in the list"},
    404: {"description": "List not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def get_list_products_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list to get products for"),
    db: Session = Depends(get_db)
):
    """
    Get all products in a list.
    
    Returns a list of all products that are associated with the specified list.
    """
    cache_key = build_cache_key("list_products", list_id=list_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="application/json", headers={"X-Cache": "HIT"})

    lock_acquired = acquire_computation_lock(cache_key)
    if not lock_acquired:
        cached = wait_for_cache(cache_key)
        if cached is not None:
            return Response(content=cached, media_type="application/json", headers={"X-Cache": "HIT"})

    try:
        result = get_list_products(db=db, list_id=list_id)
        set_cached_response(cache_key, result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        if lock_acquired:
            release_computation_lock(cache_key)


@router.post("/{list_id}/products/{product_id}", response_model=dict, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Product added to list successfully"},
    400: {"description": "Bad request, e.g., product already in list"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or product not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def add_product_to_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_id: int = Path(..., gt=0, description="The ID of the product to add to the list"),
    request: AddProductRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Add a product to a list.
    
    Adds the specified product to the list. If the product is already in the list,
    returns a 400 error.
    """
    try:
        relationship = add_product_to_list(db=db, list_id=list_id, product_id=product_id, stoc_produs=request.stoc_produs)
        invalidate_for_list(list_id)
        return {
            "message": f"Product {product_id} added to list {list_id} successfully",
            "list_id": list_id,
            "product_id": product_id,
            "stoc_produs": request.stoc_produs
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{list_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Product removed from list successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or product not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def remove_product_from_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_id: int = Path(..., gt=0, description="The ID of the product to remove from the list"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Remove a product from a list.
    
    Removes the specified product from the list. If the product is not in the list,
    returns a 404 error.
    """
    try:
        removed = remove_product_from_list(db=db, list_id=list_id, product_id=product_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} is not in list {list_id}"
            )
        invalidate_for_list(list_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/{list_id}/products", response_model=List[ProductSchema], responses={
    200: {"description": "List products replaced successfully"},
    400: {"description": "Bad request, e.g., invalid product IDs"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List not found or products not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def replace_list_products_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_ids: List[int] = ...,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Replace all products in a list.
    
    Replaces all products in the list with the specified product IDs.
    This operation removes all existing products from the list and adds the new ones.
    """
    try:
        result = replace_list_products(db=db, list_id=list_id, product_ids=product_ids)
        invalidate_for_list(list_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{list_id}/products", response_model=List[ProductSchema], responses={
    200: {"description": "Products added to list successfully"},
    400: {"description": "Bad request, e.g., invalid product IDs"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List not found or products not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def add_products_to_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_ids: List[int] = ...,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Add multiple products to a list.
    
    Adds the specified products to the list without removing existing ones.
    If a product is already in the list, it will be skipped.
    Returns only the products that were actually added.
    """
    try:
        result = add_products_to_list(db=db, list_id=list_id, product_ids=product_ids)
        invalidate_for_list(list_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        ) 


@router.patch("/{list_id}/products/{product_id}", response_model=dict, responses={
    200: {"description": "Availability updated"},
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized - Authentication required"},
    403: {"description": "Forbidden - Not enough privileges"},
    404: {"description": "List or product-in-list not found"},
    422: {"description": "Validation error (stoc_produs must be null or >=0)"},
    500: {"description": "Internal server error"},
})
def update_list_product_availability_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_id: int = Path(..., gt=0, description="The ID of the product in the list"),
    request: UpdateAvailabilityRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db),
):
    try:
        relationship = update_product_availability(
            db=db,
            list_id=list_id,
            product_id=product_id,
            stoc_produs=request.stoc_produs,
        )
        invalidate_for_list(list_id)
        # Minimal, idempotent response; does not alter other fields
        return {
            "list_id": list_id,
            "product_id": product_id,
            "stoc_produs": relationship.stoc_produs,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )