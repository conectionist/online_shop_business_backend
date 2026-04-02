from typing import Optional, Annotated, Dict
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

from app.core.image_versions import resolve_image_versions

class CategoryBase(BaseModel):
    """Base schema for category attributes"""
    
    name: Annotated[str, Field(
        description="The name of the category",
        min_length=1,
        max_length=200,
        examples=["Fruits", "Vegetables", "Dairy"]
    )]
    
    image_path: Optional[str] = Field(
        None,
        description="Path to the category image directory",
        min_length=1,
        max_length=256,
        examples=["categories/f47ac10b-58cc-4372-a567-0e02b2c3d479"]
    )
    
    @field_validator('name', 'image_path')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    order_index: int = Field(
        ..., ge=1, le=127,
        description="Manual ordering index (1-127), unique"
    )


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category"""
    
    name: Optional[str] = Field(
        None,
        description="The name of the category",
        min_length=1,
        max_length=200
    )
    
    image_path: Optional[str] = Field(
        None,
        description="Path to the category image directory (None for placeholder image)",
        max_length=256
    )
    
    order_index: Optional[int] = Field(
        None, ge=1, le=127,
        description="Manual ordering index (1-127), unique"
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
    order_index: int = Field(ge=1, le=127, description="Manual ordering index (1-127), unique")
    created_at: Annotated[datetime, Field(description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(description="Last update timestamp")]
    
    @computed_field
    @property
    def image_versions(self) -> Dict[str, str]:
        """Generate paths for different image versions based on the image directory"""
        return resolve_image_versions(
            self.image_path,
            placeholder_url="/api/v1/static/placeholders/category_placeholder.jpg",
        )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # Format datetime as ISO 8601 with Z suffix (UTC) to comply with RFC 3339
            datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    )
