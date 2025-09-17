"""
Dependencies for FastAPI endpoints.

This module contains reusable dependencies that can be used across
different API endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Custom security scheme that returns 401 instead of 403
class CustomHTTPBearer(HTTPBearer):
    def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> HTTPAuthorizationCredentials:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials

# Create custom security instance
custom_security = CustomHTTPBearer() 