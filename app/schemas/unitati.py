from typing import Optional

from pydantic import BaseModel, Field


class UnitatBase(BaseModel):
    """Base schema for unit attributes"""
    denumire: str = Field(..., description="The name of the unit", min_length=1, max_length=45)


class UnitatCreate(UnitatBase):
    """Schema for creating a new unit"""
    pass


class UnitatUpdate(BaseModel):
    """Schema for updating an existing unit"""
    denumire: Optional[str] = Field(None, description="The name of the unit", min_length=1, max_length=45)


class Unitat(UnitatBase):
    """Schema for returning unit data"""
    id: int
    
    class Config:
        from_attributes = True  # Previously orm_mode in older Pydantic versions
