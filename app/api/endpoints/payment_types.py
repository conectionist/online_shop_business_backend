import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from fastapi.responses import JSONResponse
from app.core.cache import build_cache_key, get_cached_response, set_cached_response
from app.schemas.payment_type import PaymentType
from app.services.payment_type import (
    get_payment_type_by_id,
    get_payment_types,
)

router = APIRouter()


@router.get("/", response_model=List[PaymentType], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_payment_types(
    db: Session = Depends(get_db),
):
    """Get all payment types (public endpoint for dropdowns)"""
    cache_key = build_cache_key("payment_types_list")
    cached = get_cached_response(cache_key)
    if cached is not None:
        try:
            payload = json.loads(cached)
            validated_payload = [PaymentType.model_validate(item).model_dump() for item in payload]
            return JSONResponse(content=validated_payload, headers={"X-Cache": "HIT"})
        except Exception:
            pass

    try:
        payment_types = get_payment_types(db)
        payload = [PaymentType.model_validate(pt, from_attributes=True).model_dump() for pt in payment_types]
        set_cached_response(cache_key, payload)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{payment_type_id}", response_model=PaymentType, responses={
    200: {"description": "Successful response"},
    404: {"description": "Payment type not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_payment_type(
    payment_type_id: int = Path(..., ge=0, description="The ID of the payment type to retrieve"),
    db: Session = Depends(get_db),
):
    """Get a specific payment type by ID"""
    cache_key = build_cache_key("payment_types_detail", payment_type_id=payment_type_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        try:
            payload = json.loads(cached)
            validated_payload = PaymentType.model_validate(payload).model_dump()
            return JSONResponse(content=validated_payload, headers={"X-Cache": "HIT"})
        except Exception:
            pass

    try:
        db_payment_type = get_payment_type_by_id(db, payment_type_id=payment_type_id)
        if db_payment_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment type not found"
            )
        serialized = PaymentType.model_validate(db_payment_type, from_attributes=True).model_dump()
        set_cached_response(cache_key, serialized)
        return serialized
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

