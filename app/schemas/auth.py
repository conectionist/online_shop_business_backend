"""Authentication schemas for login and token management"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=1, max_length=50, description="Admin username")
    password: str = Field(..., min_length=1, description="Admin password")


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")


class LoginResponse(BaseModel):
    """Schema for successful login response"""
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    admin: dict = Field(..., description="Admin user information")


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class AdminInfo(BaseModel):
    """Schema for admin information in responses"""
    id: int = Field(..., description="Admin ID")
    username: str = Field(..., description="Admin username")

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")


class PasswordChangeResponse(BaseModel):
    """Schema for password change response"""
    message: str = Field(..., description="Success message")


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str = Field(..., description="Error message") 