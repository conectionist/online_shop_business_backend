from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.cache import invalidate_for_list
from app.services.auth import get_current_admin_from_cookie
from app.models.admin import Admin
from app.services.list_category import (
    get_list_categories_ordered,
    add_category_to_list,
    update_category_position,
    remove_category_from_list
)
from app.schemas.list_category import (
    ListCategoryCreate,
    ListCategoryUpdate,
    ListCategoryResponse,
    CategoryInListResponse
)

class AddCategoryRequest(BaseModel):
    position: Optional[int] = Field(None, ge=0, description="Position of the category in the list. If not provided, will be added at the end")

class UpdateCategoryPositionRequest(BaseModel):
    new_position: int = Field(..., ge=0, description="New position for the category in the list")

router = APIRouter()


@router.get("/{list_id}/categories", responses={
    200: {"description": "List of categories in the list, ordered by position"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def get_list_categories_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list to get categories for"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get all categories in a list, ordered by their position.
    
    Returns a list of all categories that are associated with the specified list,
    ordered by their position in the list.
    """
    try:
        return get_list_categories_ordered(db=db, list_id=list_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/{list_id}/categories/{category_id}", response_model=dict, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Category added to list successfully"},
    400: {"description": "Bad request, e.g., category already in list"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def add_category_to_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    category_id: int = Path(..., gt=0, description="The ID of the category to add to the list"),
    request: AddCategoryRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Add a category to a list.
    
    Adds the specified category to the list at the specified position.
    If the category is already in the list, returns a 400 error.
    If position is not provided, the category will be added at the end.
    """
    try:
        relationship = add_category_to_list(
            db=db, 
            list_id=list_id, 
            category_id=category_id, 
            position=request.position
        )
        invalidate_for_list(list_id)
        return {
            "message": f"Category {category_id} added to list {list_id} successfully",
            "list_id": list_id,
            "category_id": category_id,
            "position": relationship.position
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{list_id}/categories/{category_id}/position", response_model=dict, responses={
    200: {"description": "Category position updated successfully"},
    400: {"description": "Bad request, e.g., invalid position"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_category_position_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    category_id: int = Path(..., gt=0, description="The ID of the category to update"),
    request: UpdateCategoryPositionRequest = Body(...),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Update the position of a category within a list.
    
    Moves the specified category to the new position and shifts other categories accordingly.
    """
    try:
        updated_relationship = update_category_position(
            db=db, 
            list_id=list_id, 
            category_id=category_id, 
            new_position=request.new_position
        )
        invalidate_for_list(list_id)
        return {
            "message": f"Category {category_id} position updated successfully",
            "list_id": list_id,
            "category_id": category_id,
            "new_position": updated_relationship.position
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{list_id}/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Category removed from list successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or category not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def remove_category_from_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    category_id: int = Path(..., gt=0, description="The ID of the category to remove from the list"),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Remove a category from a list.
    
    Removes the specified category from the list and shifts the positions
    of remaining categories accordingly.
    """
    try:
        removed = remove_category_from_list(db=db, list_id=list_id, category_id=category_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} is not in list {list_id}"
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