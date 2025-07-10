from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import os
from pathlib import Path

router = APIRouter()

# Define the base path for placeholders
PLACEHOLDER_DIR = Path("/app/config/placeholders")

# Define the base URL path for accessing placeholders
PLACEHOLDER_URL_BASE = "/api/v1/static/placeholders"

class SystemConfigResponse(BaseModel):
    category_placeholder: str
    product_placeholder: str

@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """
    Get system configuration including paths to placeholder images.
    
    Returns a JSON object with paths to various system resources.
    """
    return {
        "category_placeholder": f"{PLACEHOLDER_URL_BASE}/category_placeholder.jpg",
        "product_placeholder": f"{PLACEHOLDER_URL_BASE}/product_placeholder.jpg"
    }

# Add a static file serving endpoint for the placeholders
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

# This function should be called from main.py to mount the static files
def mount_static_files(app: FastAPI):
    """
    Mount the static files directory for serving placeholder images.
    This function should be called from main.py after creating the FastAPI app.
    """
    # The physical directory where files are stored
    directory = "/app/config/placeholders"
    
    # The URL path where they will be served
    url_path = "/api/v1/static/placeholders"
    
    # Mount the directory to the URL path
    app.mount(url_path, StaticFiles(directory=directory), name="placeholders")

