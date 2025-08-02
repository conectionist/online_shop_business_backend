"""
Dependencies for FastAPI endpoints.

This module contains reusable dependencies that can be used across
different API endpoints.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import get_current_admin
from app.models.admin import Admin


# Re-export the get_current_admin dependency for easy import
def get_authenticated_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """
    Dependency to get the currently authenticated admin.
    
    This is a wrapper around get_current_admin that provides
    a cleaner import path for other modules.
    
    Args:
        current_admin: The authenticated admin from get_current_admin
        
    Returns:
        Admin: The authenticated admin object
        
    Raises:
        HTTPException: If authentication fails
    """
    return current_admin


# Export the original function as well for backward compatibility
__all__ = ["get_authenticated_admin", "get_current_admin"] 