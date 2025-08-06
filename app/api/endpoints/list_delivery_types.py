from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.delivery_type import DeliveryType as DeliveryTypeSchema
from app.services.list_delivery_type import (
    get_list_delivery_types,
    add_delivery_type_to_list,
    remove_delivery_type_from_list,
    replace_list_delivery_types,
)

router = APIRouter()


@router.get("/{list_id}/delivery-types", response_model=List[DeliveryTypeSchema], responses={
    200: {"description": "List of delivery types for the list"},
    404: {"description": "List not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def get_list_delivery_types_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list to get delivery types for"),
    db: Session = Depends(get_db)
):
    """
    Get all delivery types for a list.
    
    Returns a list of all delivery types that are associated with the specified list.
    """
    try:
        return get_list_delivery_types(db=db, list_id=list_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/{list_id}/delivery-types/{delivery_type_id}", response_model=dict, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Delivery type added to list successfully"},
    400: {"description": "Bad request, e.g., delivery type already in list"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or delivery type not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def add_delivery_type_to_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    delivery_type_id: int = Path(..., gt=0, description="The ID of the delivery type to add to the list"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Add a delivery type to a list.
    
    Adds the specified delivery type to the list. If the delivery type is already in the list,
    returns a 400 error.
    """
    try:
        relationship = add_delivery_type_to_list(db=db, list_id=list_id, delivery_type_id=delivery_type_id)
        return {
            "message": f"Delivery type {delivery_type_id} added to list {list_id} successfully",
            "list_id": list_id,
            "delivery_type_id": delivery_type_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/{list_id}/delivery-types/{delivery_type_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Delivery type removed from list successfully"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List or delivery type not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def remove_delivery_type_from_list_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    delivery_type_id: int = Path(..., gt=0, description="The ID of the delivery type to remove from the list"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Remove a delivery type from a list.
    
    Removes the specified delivery type from the list. If the delivery type is not in the list,
    returns a 404 error.
    """
    try:
        removed = remove_delivery_type_from_list(db=db, list_id=list_id, delivery_type_id=delivery_type_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery type {delivery_type_id} is not in list {list_id}"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/{list_id}/delivery-types", response_model=List[DeliveryTypeSchema], responses={
    200: {"description": "List delivery types replaced successfully"},
    400: {"description": "Bad request, e.g., invalid delivery type IDs"},
    401: {"description": "Unauthorized - Authentication required"},
    404: {"description": "List not found or delivery types not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def replace_list_delivery_types_endpoint(
    list_id: int = Path(..., gt=0, description="The ID of the list"),
    delivery_type_ids: List[int] = ...,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Replace all delivery types in a list.
    
    Replaces all delivery types in the list with the specified delivery type IDs.
    This operation removes all existing delivery types from the list and adds the new ones.
    """
    try:
        return replace_list_delivery_types(db=db, list_id=list_id, delivery_type_ids=delivery_type_ids)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        ) 