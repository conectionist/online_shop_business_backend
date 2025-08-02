"""Admin schemas for authentication"""

from typing import Optional
from pydantic import BaseModel, Field


class AdminBase(BaseModel):
    """Base admin schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Admin username")


class AdminCreate(AdminBase):
    """Schema for creating a new admin user"""
    password: str = Field(..., min_length=8, description="Admin password (min 8 characters)")


class AdminUpdate(BaseModel):
    """Schema for updating an admin user"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Admin username")
    password: Optional[str] = Field(None, min_length=8, description="Admin password (min 8 characters)")


class AdminLogin(BaseModel):
    """Schema for admin login"""
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")


class AdminResponse(AdminBase):
    """Schema for admin response (excludes password)"""
    id: int

    class Config:
        from_attributes = True


class Admin(AdminResponse):
    """Admin schema for compatibility"""
    pass


class AdminToken(BaseModel):
    """Schema for admin token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    admin: AdminResponse


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds 