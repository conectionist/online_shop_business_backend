from typing import Optional, Annotated, Dict
from datetime import datetime
import os

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field


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
    pass


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
    
    @computed_field
    @property
    def image_versions(self) -> Dict[str, str]:
        """Generate paths for different image versions based on the image directory"""
        if not self.image_path:
            # Return placeholder image path from system config
            # The client should use the system config endpoint to get the actual placeholder path
            return {
                "original": "/api/v1/static/placeholders/category_placeholder.jpg",
                "medium": "/api/v1/static/placeholders/category_placeholder.jpg",
                "thumbnail": "/api/v1/static/placeholders/category_placeholder.jpg"
            }
        
        # Extract the image ID from the path
        image_id = os.path.basename(self.image_path)
        
        # Detect the actual file extension by checking what files exist
        # This handles cases where images are uploaded in different formats
        upload_dir = os.path.join("/app/uploads", self.image_path)
        ext = ".jpg"  # Default fallback
        
        # Check for common image extensions
        for test_ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            test_file = os.path.join(upload_dir, f"{image_id}{test_ext}")
            if os.path.exists(test_file):
                ext = test_ext
                break
        
        # Return paths for all versions
        return {
            "original": os.path.join(self.image_path, f"{image_id}{ext}"),
            "medium": os.path.join(self.image_path, f"{image_id}-medium{ext}"),
            "thumbnail": os.path.join(self.image_path, f"{image_id}-thumbnail{ext}")
        }
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # Format datetime as ISO 8601 with Z suffix (UTC) to comply with RFC 3339
            datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    )
