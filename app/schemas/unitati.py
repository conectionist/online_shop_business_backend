from typing import Optional, Annotated

from pydantic import BaseModel, Field, ConfigDict, field_validator


class UnitatBase(BaseModel):
    """Base schema for unit attributes"""
    denumire: Annotated[str, Field(
        description="The name of the unit", 
        min_length=1, 
        max_length=45,
        examples=["buc", "kg", "l"]
    )]
    
    @field_validator('denumire')
    @classmethod
    def validate_denumire(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("denumire cannot be empty or just whitespace")
        return v


class UnitatCreate(UnitatBase):
    """Schema for creating a new unit"""
    pass


class UnitatUpdate(BaseModel):
    """Schema for updating an existing unit"""
    denumire: Optional[str] = Field(None, description="The name of the unit", min_length=1, max_length=45)


class Unitat(UnitatBase):
    """Schema for returning unit data"""
    id: Annotated[int, Field(gt=0, description="The unique identifier for the unit")]
    
    model_config = ConfigDict(from_attributes=True)  # Modern Pydantic v2 approach
