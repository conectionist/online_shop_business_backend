from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


class DeliveryTypeBase(BaseModel):
    """Base schema for delivery types with common fields."""
    
    denumire: str = Field(
        ...,
        min_length=1,
        max_length=45,
        description="Delivery type name",
        examples=["Ridicare de la sediu"]
    )
    
    @field_validator('denumire')
    def denumire_must_not_be_empty_or_whitespace(cls, v):
        if v.strip() == "":
            raise ValueError("Delivery type name must not be empty or whitespace only")
        return v.strip()


class DeliveryTypeCreate(DeliveryTypeBase):
    """Schema for creating a new delivery type."""
    pass


class DeliveryTypeUpdate(BaseModel):
    """Schema for updating an existing delivery type."""
    
    denumire: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=45,
        description="Delivery type name"
    )
    
    @field_validator('denumire')
    def denumire_must_not_be_empty_or_whitespace(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Delivery type name must not be empty or whitespace only")
        return v.strip() if v is not None else v


class DeliveryType(DeliveryTypeBase):
    """Schema for delivery type responses including the ID."""
    
    id: int = Field(gt=0, description="The delivery type ID")
    
    model_config = ConfigDict(from_attributes=True)
