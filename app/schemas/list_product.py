from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ListProductBase(BaseModel):
    """Base schema for list-product relationship"""
    liste_id: int = Field(..., gt=0, description="ID of the list")
    produse_id: int = Field(..., gt=0, description="ID of the product")


class ListProductCreate(ListProductBase):
    """Schema for creating a list-product relationship"""
    pass


class ListProduct(ListProductBase):
    """Schema for returning list-product relationship data"""
    
    model_config = ConfigDict(from_attributes=True)


class ListProductResponse(BaseModel):
    """Schema for returning product data in a list context"""
    id: int = Field(..., gt=0, description="Product ID")
    nume: str = Field(..., description="Product name")
    cantitate: int = Field(..., gt=0, description="Product quantity")
    pret: int = Field(..., gt=0, description="Product price in cents")
    description: Optional[str] = Field(None, description="Product description")
    category_id: int = Field(..., gt=0, description="Category ID")
    unitati_id: int = Field(..., gt=0, description="Unit ID")
    stock: Optional[int] = Field(None, ge=0, description="Available stock")
    
    model_config = ConfigDict(from_attributes=True) 