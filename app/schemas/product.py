from typing import Optional, Annotated, Dict
from datetime import datetime
import os

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field


class ProductBase(BaseModel):
    """Base schema for product attributes"""
    
    nume: Annotated[str, Field(
        description="The name of the product",
        min_length=1,
        max_length=45,
        examples=["Apple", "Milk", "Bread"]
    )]
    
    cantitate: Annotated[int, Field(
        description="The quantity per unit",
        gt=0,
        examples=[1, 6, 12]
    )]
    
    pret: Annotated[int, Field(
        description="The price in cents",
        gt=0,
        examples=[499, 1250, 799]
    )]
    
    description: Optional[str] = Field(
        None,
        description="Product description",
        max_length=1500,
        examples=["Fresh apples from local farms"]
    )
    
    primary_image_path: Optional[str] = Field(
        None,
        description="Path to the product's primary image",
        max_length=256,
        examples=["products/f47ac10b-58cc-4372-a567-0e02b2c3d479"]
    )
    
    category_id: Annotated[int, Field(
        description="ID of the category this product belongs to",
        gt=0,
        examples=[1, 2, 3]
    )]
    
    unitati_id: Annotated[int, Field(
        description="ID of the unit of measurement",
        gt=0,
        examples=[1, 2, 3]
    )]
    
    stock: Optional[int] = Field(
        None,
        description="Available stock quantity",
        ge=0,
        examples=[10, 50, 100]
    )
    
    @field_validator('nume', 'description', 'primary_image_path')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    
    nume: Optional[str] = Field(
        None,
        description="The name of the product",
        min_length=1,
        max_length=45
    )
    
    cantitate: Optional[int] = Field(
        None,
        description="The quantity per unit",
        gt=0
    )
    
    pret: Optional[int] = Field(
        None,
        description="The price in cents",
        gt=0
    )
    
    description: Optional[str] = Field(
        None,
        description="Product description",
        max_length=1500
    )
    
    primary_image_path: Optional[str] = Field(
        None,
        description="Path to the product's primary image",
        max_length=256
    )
    
    category_id: Optional[int] = Field(
        None,
        description="ID of the category this product belongs to",
        gt=0
    )
    
    unitati_id: Optional[int] = Field(
        None,
        description="ID of the unit of measurement",
        gt=0
    )
    
    stock: Optional[int] = Field(
        None,
        description="Available stock quantity",
        ge=0
    )
    
    is_deleted: Optional[bool] = Field(
        None,
        description="Soft delete flag"
    )
    
    @field_validator('nume', 'description', 'primary_image_path')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class Product(ProductBase):
    """Schema for returning product data"""
    
    id: Annotated[int, Field(gt=0, description="The unique identifier for the product")]
    created_at: Annotated[datetime, Field(description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(description="Last update timestamp")]
    is_deleted: bool
    
    @computed_field
    @property
    def image_versions(self) -> Dict[str, str]:
        """Generate paths for different image versions based on the primary image"""
        if not self.primary_image_path:
            # Return placeholder image path from system config
            return {
                "original": "/api/v1/static/placeholders/product_placeholder.jpg",
                "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
                "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
            }
        
        # Extract the image ID from the path
        image_id = os.path.basename(self.primary_image_path)
        
        # Get file extension - we'll assume .jpg for now as a default
        ext = ".jpg"
        
        # Return paths for all versions
        return {
            "original": os.path.join(self.primary_image_path, f"{image_id}{ext}"),
            "medium": os.path.join(self.primary_image_path, f"{image_id}-medium{ext}"),
            "thumbnail": os.path.join(self.primary_image_path, f"{image_id}-thumbnail{ext}")
        }
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # Format datetime as ISO 8601 with Z suffix (UTC) to comply with RFC 3339
            datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    )
