from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


class BusinessDetailsBase(BaseModel):
    """Base schema for business details with common fields."""
    
    adresa: Optional[str] = Field(
        None,
        max_length=200,
        description="Business address"
    )
    
    telefon: Optional[str] = Field(
        None,
        max_length=20,
        description="Business phone number"
    )
    
    logo_path: Optional[str] = Field(
        None,
        max_length=256,
        description="Path to business logo image"
    )
    
    motto: Optional[str] = Field(
        None,
        max_length=256,
        description="Business motto or slogan"
    )
    
    list_not_available_msg: Optional[str] = Field(
        None,
        max_length=200,
        description="Message displayed when product list is not available"
    )
    
    alte_detalii: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional business details"
    )
    
    @field_validator('adresa', 'telefon', 'logo_path', 'motto', 'list_not_available_msg', 'alte_detalii')
    def strip_if_not_none(cls, v):
        """Strip whitespace from string fields if they're not None."""
        return v.strip() if v is not None else v


class BusinessDetailsCreate(BusinessDetailsBase):
    """Schema for creating a new business details record."""
    pass


class BusinessDetailsUpdate(BusinessDetailsBase):
    """Schema for updating an existing business details record."""
    pass


class BusinessDetails(BusinessDetailsBase):
    """Schema for business details responses including the ID."""
    
    id: int = Field(gt=0, description="The business details ID")
    
    model_config = ConfigDict(from_attributes=True)
