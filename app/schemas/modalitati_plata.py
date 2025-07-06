from typing import Optional, Annotated

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ModalitatePlataBase(BaseModel):
    """Base schema for payment method attributes"""
    denumire: Annotated[str, Field(
        description="The name of the payment method", 
        min_length=1, 
        max_length=45,
        examples=["Card", "Numerar la livrare", "Transfer Bancar"]
    )]
    
    @field_validator('denumire')
    @classmethod
    def validate_denumire(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("denumire cannot be empty or just whitespace")
        return v


class ModalitatePlataCreate(ModalitatePlataBase):
    """Schema for creating a new payment method"""
    pass


class ModalitatePlataUpdate(BaseModel):
    """Schema for updating an existing payment method"""
    denumire: Optional[str] = Field(
        None, 
        description="The name of the payment method", 
        min_length=1, 
        max_length=45
    )


class ModalitatePlata(ModalitatePlataBase):
    """Schema for returning payment method data"""
    id: Annotated[int, Field(gt=0, description="The unique identifier for the payment method")]
    
    model_config = ConfigDict(from_attributes=True)  # Modern Pydantic v2 approach
