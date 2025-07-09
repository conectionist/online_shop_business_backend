from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


class DeliveryScheduleBase(BaseModel):
    """Base schema for delivery schedules with common fields."""
    
    orar_livrari: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Delivery schedule information",
        examples=["Monday-Friday: 9:00-18:00, Saturday: 10:00-14:00"]
    )
    
    @field_validator('orar_livrari')
    def orar_livrari_must_not_be_empty_or_whitespace(cls, v):
        if v.strip() == "":
            raise ValueError("Delivery schedule must not be empty or whitespace only")
        return v.strip()


class DeliveryScheduleCreate(DeliveryScheduleBase):
    """Schema for creating a new delivery schedule."""
    pass


class DeliveryScheduleUpdate(BaseModel):
    """Schema for updating an existing delivery schedule."""
    
    orar_livrari: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=1000,
        description="Delivery schedule information"
    )
    
    @field_validator('orar_livrari')
    def orar_livrari_must_not_be_empty_or_whitespace(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Delivery schedule must not be empty or whitespace only")
        return v.strip() if v is not None else v


class DeliverySchedule(DeliveryScheduleBase):
    """Schema for delivery schedule responses including the ID."""
    
    id: int = Field(gt=0, description="The delivery schedule ID")
    
    model_config = ConfigDict(from_attributes=True)
