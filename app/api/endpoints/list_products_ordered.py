from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.auth import get_current_admin
from app.models.admin import Admin
from app.services.list_product_ordered import (
    get_list_products_by_category,
    add_product_to_category,
    update_product_position,
    move_product_between_categories,
    remove_product_from_list,
    bulk_update_positions
)
from app.schemas.list_product_ordered import (
    ListProductOrderedCreate,
    ListProductOrderedUpdate,
    ListProductOrderedResponse,
    ProductInListResponse,
    CategoryWithProductsResponse,
    ListProductsOrderedResponse,
    MoveProductRequest,
    BulkUpdatePositionsRequest
)

class AddProductRequest(BaseModel):
    position: Optional[int] = Field(None, ge=0, description="Position of the product within the category. If not provided, will be added at the end")
    stoc_produs: Optional[int] = Field(None, ge=0, description="Available stock for this product in this list")

class UpdateProductPositionRequest(BaseModel):
    new_position: int = Field(..., ge=0, description="New position for the product within its category")

class MoveProductRequest(BaseModel):
    new_category_id: int = Field(..., gt=0, description="ID of the category to move the product to")
    new_position: Optional[int] = Field(None, ge=0, description="New position within the target category. If not provided, will be added at the end")

router = APIRouter()


@router.get("/{list_id}/products/ordered", responses={
    200: {"description": "List of products grouped by category and ordered by position"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def get_list_products_ordered_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list to get products for"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all products in a list, grouped by category and ordered by position.
    
    Returns a structured response with categories and their products,
    all ordered by their respective positions.
    """
    try:
        return get_list_products_by_category(db=db, list_id=list_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/{list_id}/categories/{category_id}/products/{product_id}", response_model=dict, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Product added to category successfully"},
    400: {"description": "Bad request, e.g., product already in list"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List, category, or product not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def add_product_to_category_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    category_id: int = Path(..., gt=0, description="The ID of the category"),
    product_id: int = Path(..., gt=0, description="The ID of the product to add"),
    request: AddProductRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Add a product to a specific category within a list.
    
    Adds the specified product to the category at the specified position.
    If the product is already in the list, returns a 400 error.
    If position is not provided, the product will be added at the end of the category.
    """
    try:
        relationship = add_product_to_category(
            db=db, 
            list_id=list_id, 
            category_id=category_id,
            product_id=product_id, 
            position=request.position,
            stoc_produs=request.stoc_produs
        )
        return {
            "message": f"Product {product_id} added to category {category_id} in list {list_id} successfully",
            "list_id": list_id,
            "category_id": category_id,
            "product_id": product_id,
            "position": relationship.position,
            "stoc_produs": relationship.stoc_produs
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{list_id}/products/{product_id}/position", response_model=dict, responses={
    200: {"description": "Product position updated successfully"},
    400: {"description": "Bad request, e.g., invalid position"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or product not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_product_position_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_id: int = Path(..., gt=0, description="The ID of the product to update"),
    request: UpdateProductPositionRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update the position of a product within its category in a list.
    
    Moves the specified product to the new position within its category
    and shifts other products in the same category accordingly.
    """
    try:
        updated_relationship = update_product_position(
            db=db, 
            list_id=list_id, 
            product_id=product_id, 
            new_position=request.new_position
        )
        return {
            "message": f"Product {product_id} position updated successfully",
            "list_id": list_id,
            "product_id": product_id,
            "category_id": updated_relationship.category_id,
            "new_position": updated_relationship.position
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{list_id}/products/{product_id}/move", response_model=dict, responses={
    200: {"description": "Product moved between categories successfully"},
    400: {"description": "Bad request, e.g., invalid category or position"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List, product, or target category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def move_product_between_categories_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    product_id: int = Path(..., gt=0, description="The ID of the product to move"),
    request: MoveProductRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Move a product from its current category to a new category within the same list.
    
    Moves the specified product to the new category at the specified position.
    If position is not provided, the product will be added at the end of the target category.
    """
    try:
        updated_relationship = move_product_between_categories(
            db=db, 
            list_id=list_id, 
            product_id=product_id, 
            new_category_id=request.new_category_id,
            position=request.new_position
        )
        return {
            "message": f"Product {product_id} moved to category {request.new_category_id} successfully",
            "list_id": list_id,
            "product_id": product_id,
            "old_category_id": updated_relationship.category_id,
            "new_category_id": request.new_category_id,
            "new_position": updated_relationship.position
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
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Remove a product from a list.
    
    Removes the specified product from the list and shifts the positions
    of remaining products in the same category accordingly.
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


@router.put("/{list_id}/positions", response_model=dict, responses={
    200: {"description": "Bulk position update completed successfully"},
    400: {"description": "Bad request, e.g., invalid data structure"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List, category, or product not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def bulk_update_positions_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    request: BulkUpdatePositionsRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Bulk update positions of categories and products in a list.
    
    Replaces the entire structure of the list with the provided ordering.
    Categories are ordered by their position in the array.
    Products within each category are ordered by their position in the products array.
    
    Example request:
    {
        "positions": [
            {
                "category_id": 2,
                "products": [1, 3, 0, 2]
            },
            {
                "category_id": 3,
                "products": [1, 0]
            },
            {
                "category_id": 1,
                "products": [33, 55]
            }
        ]
    }
    """
    try:
        # Convert the request to the format expected by the service
        positions_data = [pos.dict() for pos in request.positions]
        
        result = bulk_update_positions(
            db=db, 
            list_id=list_id, 
            positions_data=positions_data
        )
        
        return {
            "message": f"Bulk position update completed successfully for list {list_id}",
            "list_id": list_id,
            "updated_structure": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        ) 