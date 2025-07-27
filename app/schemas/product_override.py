from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FieldNameEnum(str, Enum):
    """Enum for field names that can be overridden"""
    PRICE = "price"
    DESCRIPTION = "description"
    STOCK = "stock"
    AVAILABILITY = "availability"


class ProductOverrideBase(BaseModel):
    """Base schema for product override"""
    produse_id: int = Field(..., gt=0, description="ID of the product to override")
    field_name: FieldNameEnum = Field(..., description="Field to override")
    old_value: Optional[str] = Field(None, description="Original value (for reference)")
    new_value: str = Field(..., description="New override value")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the override")
    is_active: bool = Field(True, description="Whether the override is currently active")


class ProductOverrideCreate(ProductOverrideBase):
    """Schema for creating a product override"""
    pass


class ProductOverrideUpdate(BaseModel):
    """Schema for updating a product override"""
    new_value: Optional[str] = Field(None, description="New override value")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the override")
    is_active: Optional[bool] = Field(None, description="Whether the override is currently active")


class ProductOverride(ProductOverrideBase):
    """Schema for returning product override data"""
    id: int = Field(..., gt=0, description="Override ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ProductOverrideResponse(BaseModel):
    """Schema for returning product override with product details"""
    id: int = Field(..., gt=0, description="Override ID")
    produse_id: int = Field(..., gt=0, description="Product ID")
    field_name: FieldNameEnum = Field(..., description="Field being overridden")
    old_value: Optional[str] = Field(None, description="Original value")
    new_value: str = Field(..., description="Override value")
    notes: Optional[str] = Field(None, description="Optional notes")
    is_active: bool = Field(..., description="Whether override is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True) 