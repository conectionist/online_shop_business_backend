from typing import Optional, Annotated
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    """Base schema for category attributes"""
    
    name: Annotated[str, Field(
        description="The name of the category",
        min_length=1,
        max_length=45,
        examples=["Fruits", "Vegetables", "Dairy"]
    )]
    
    image_path: Annotated[str, Field(
        description="Path to the category image",
        min_length=1,
        max_length=256,
        examples=["/images/categories/fruits.jpg"]
    )]
    
    @field_validator('name', 'image_path')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category"""
    
    name: Optional[str] = Field(
        None,
        description="The name of the category",
        min_length=1,
        max_length=45
    )
    
    image_path: Optional[str] = Field(
        None,
        description="Path to the category image",
        min_length=1,
        max_length=256
    )
    
    is_deleted: Optional[bool] = Field(
        None,
        description="Soft delete flag"
    )
    
    @field_validator('name', 'image_path')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class Category(CategoryBase):
    """Schema for returning category data"""
    
    id: Annotated[int, Field(gt=0, description="The unique identifier for the category")]
    created_at: Annotated[datetime, Field(description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(description="Last update timestamp")]
    is_deleted: bool
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # Format datetime as ISO 8601 with Z suffix (UTC) to comply with RFC 3339
            datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    )
