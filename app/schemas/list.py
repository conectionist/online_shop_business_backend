from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import date, datetime


class ListBase(BaseModel):
    """Base schema with common fields for Lists"""
    data: date = Field(..., description="Date of the list")
    is_current: bool = Field(..., description="Flag indicating if this is the current list")
    is_published: Optional[bool] = Field(None, description="Flag indicating if the list is published")
    mesaj_introducere: Optional[str] = Field(
        None, 
        max_length=100,
        description="Introduction message for the list"
    )
    alte_detalii: Optional[str] = Field(
        None, 
        max_length=500,
        description="Additional details for the list"
    )
    numar_whatsapp: Optional[str] = Field(
        None, 
        max_length=15,
        pattern=r'^\+?[0-9]{10,15}$',
        description="WhatsApp number for contact"
    )
    orare_livrari_id: int = Field(..., gt=0, description="ID of the associated delivery schedule")
    
    @field_validator('numar_whatsapp')
    def validate_whatsapp_number(cls, v):
        if v is not None and v.strip() == "":
            return None
        return v


class ListCreate(ListBase):
    """Schema for creating a new list"""
    pass


class ListUpdate(BaseModel):
    """Schema for updating an existing list"""
    data: Optional[date] = None
    is_current: Optional[bool] = None
    is_published: Optional[bool] = None
    mesaj_introducere: Optional[str] = Field(
        None, 
        max_length=100,
    )
    alte_detalii: Optional[str] = Field(
        None, 
        max_length=500,
    )
    numar_whatsapp: Optional[str] = Field(
        None, 
        max_length=15,
        pattern=r'^\+?[0-9]{10,15}$',
    )
    orare_livrari_id: Optional[int] = Field(None, gt=0)
    is_deleted: Optional[bool] = None
    
    @field_validator('numar_whatsapp')
    def validate_whatsapp_number(cls, v):
        if v is not None and v.strip() == "":
            return None
        return v


class List(ListBase):
    """Schema for list responses that includes the ID and timestamps"""
    id: int = Field(..., gt=0, description="Unique identifier for the list")
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class ListWithOrderedContent(List):
    """Schema for list responses that includes ordered categories and products"""
    categories: Optional[List[dict]] = Field(None, description="Ordered categories in this list")
    products_ordered: Optional[List[dict]] = Field(None, description="Products grouped by category and ordered")
    
    model_config = ConfigDict(from_attributes=True)
