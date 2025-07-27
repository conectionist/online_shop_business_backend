from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import Product as ProductSchema
from app.services.list_product import (
    get_list_products,
    add_product_to_list,
    remove_product_from_list,
    replace_list_products,
)

router = APIRouter()


@router.get("/{list_id}/products", response_model=List[ProductSchema], responses={
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
    try:
        return get_list_products(db=db, list_id=list_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/{list_id}/products/{product_id}", response_model=dict, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Product added to list successfully"},
    400: {"description": "Bad request, e.g., product already in list"},
    404: {"description": "List or product not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def add_product_to_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_id: int = Path(..., gt=0, description="The ID of the product to add to the list"),
    db: Session = Depends(get_db)
):
    """
    Add a product to a list.
    
    Adds the specified product to the list. If the product is already in the list,
    returns a 400 error.
    """
    try:
        relationship = add_product_to_list(db=db, list_id=list_id, product_id=product_id)
        return {
            "message": f"Product {product_id} added to list {list_id} successfully",
            "list_id": list_id,
            "product_id": product_id
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
    404: {"description": "List or product not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def remove_product_from_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_id: int = Path(..., gt=0, description="The ID of the product to remove from the list"),
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
    404: {"description": "List not found or products not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def replace_list_products_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_ids: List[int] = ...,
    db: Session = Depends(get_db)
):
    """
    Replace all products in a list.
    
    Replaces all products in the list with the specified product IDs.
    This operation removes all existing products from the list and adds the new ones.
    """
    try:
        return replace_list_products(db=db, list_id=list_id, product_ids=product_ids)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        ) 