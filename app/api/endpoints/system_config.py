from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
import os
from pathlib import Path
from app.core.config import MAX_IMAGE_SIZE_MB
from app.core.constants import UNCATEGORIZED_CATEGORY_ID, UNCATEGORIZED_CATEGORY_NAME
from app.utils.macro_processor import _compute_next_delivery_date, _format_date_ro_long

router = APIRouter()

# Define the base path for placeholders
PLACEHOLDER_DIR = Path("/app/config/placeholders")

# Define the base URL path for accessing placeholders
PLACEHOLDER_URL_BASE = "/api/v1/static/placeholders"

class SystemConfigResponse(BaseModel):
    category_placeholder: str
    product_placeholder: str
    default_category_id: int
    default_category_name: str
    max_image_size_mb: int

class NextDeliveryDateResponse(BaseModel):
    next_delivery_date: str
    formatted_date_ro: str
    reference_date: str

@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """
    Get system configuration including paths to placeholder images and default category information.
    
    Returns a JSON object with paths to various system resources and default category details.
    """
    return {
        "category_placeholder": f"{PLACEHOLDER_URL_BASE}/category_placeholder.jpg",
        "product_placeholder": f"{PLACEHOLDER_URL_BASE}/product_placeholder.jpg",
        "default_category_id": UNCATEGORIZED_CATEGORY_ID,
        "default_category_name": UNCATEGORIZED_CATEGORY_NAME,
        "max_image_size_mb": MAX_IMAGE_SIZE_MB,
    }

@router.get("/next-delivery-date", response_model=NextDeliveryDateResponse)
async def get_next_delivery_date(
    reference_date: Optional[str] = Query(None, description="Reference date in ISO format (YYYY-MM-DD). If not provided, uses current date. Example: 2025-09-26")
):
    """
    Get the next delivery date (next Tuesday or Friday, whichever comes first).
    
    Returns the next delivery date in both ISO format and Romanian long format.
    If no reference date is provided, uses the current date as reference.
    
    **Example Response:**
    ```json
    {
        "next_delivery_date": "2025-09-30T00:00:00",
        "formatted_date_ro": "marți, 30 septembrie 2025",
        "reference_date": "2025-09-26T00:00:00"
    }
    ```
    """
    try:
        # Parse reference date or use current date
        if reference_date:
            ref_date = datetime.fromisoformat(reference_date)
        else:
            ref_date = datetime.now()
        
        # Compute next delivery date
        next_date = _compute_next_delivery_date(ref_date)
        formatted_date_ro = _format_date_ro_long(next_date)
        
        return {
            "next_delivery_date": next_date.isoformat(),
            "formatted_date_ro": formatted_date_ro,
            "reference_date": ref_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing next delivery date: {str(e)}")

# Add a static file serving endpoint for the placeholders
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

# This function should be called from main.py to mount the static files
def mount_static_files(app: FastAPI):
    """
    Mount the static files directory for serving placeholder images and uploads.
    This function should be called from main.py after creating the FastAPI app.
    """
    # Mount placeholders
    placeholder_directory = "/app/config/placeholders"
    placeholder_url_path = "/api/v1/static/placeholders"
    app.mount(placeholder_url_path, StaticFiles(directory=placeholder_directory), name="placeholders")
    
    # Mount uploads
    uploads_directory = "/app/uploads"
    uploads_url_path = "/api/v1/static/uploads"
    app.mount(uploads_url_path, StaticFiles(directory=uploads_directory), name="uploads")

