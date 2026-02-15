"""Pydantic schemas for session management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionInfo(BaseModel):
    """Schema for session information in API responses."""
    
    id: int = Field(..., description="Session ID")
    session_name: str = Field(..., description="User-friendly session name")
    device_type: str = Field(..., description="Device type: desktop, mobile, tablet, unknown")
    browser_name: str = Field(..., description="Browser name")
    os_name: str = Field(..., description="Operating system name")
    ip_address: Optional[str] = Field(None, description="IP address")
    location_city: Optional[str] = Field(None, description="Approximate city")
    location_country: Optional[str] = Field(None, description="ISO country code")
    created_at: datetime = Field(..., description="Session creation time")
    last_used_at: Optional[datetime] = Field(None, description="Last activity time")
    expires_at: datetime = Field(..., description="Session expiration time")
    is_current: bool = Field(..., description="Whether this is the current session")
    
    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for listing all sessions."""
    
    sessions: list[SessionInfo] = Field(..., description="List of active sessions")
    total: int = Field(..., description="Total number of active sessions")


class SessionRevokeResponse(BaseModel):
    """Schema for session revocation response."""
    
    message: str = Field(..., description="Success message")
    session_id: int = Field(..., description="ID of revoked session")
