from typing import Optional, Annotated

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ModalitatePlataBase(BaseModel):
    """Base schema for payment method attributes"""
    name: Annotated[str, Field(
        description="The internal name of the payment method", 
        min_length=1, 
        max_length=20,
        examples=["card", "cash", "transfer"]
    )]
    
    description: Annotated[str, Field(
        description="The display description of the payment method", 
        min_length=1, 
        max_length=100,
        examples=["Card", "Numerar la livrare", "Transfer Bancar"]
    )]
    
    @field_validator('name', 'description')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class ModalitatePlataCreate(ModalitatePlataBase):
    """Schema for creating a new payment method"""
    pass


class ModalitatePlataUpdate(BaseModel):
    """Schema for updating an existing payment method"""
    name: Optional[str] = Field(
        None, 
        description="The internal name of the payment method", 
        min_length=1, 
        max_length=20
    )
    
    description: Optional[str] = Field(
        None, 
        description="The display description of the payment method", 
        min_length=1, 
        max_length=100
    )
    
    @field_validator('name', 'description')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class ModalitatePlata(ModalitatePlataBase):
    """Schema for returning payment method data"""
    id: Annotated[int, Field(gt=0, description="The unique identifier for the payment method")]
    
    model_config = ConfigDict(from_attributes=True)  # Modern Pydantic v2 approach
