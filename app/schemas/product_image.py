from typing import Dict, Annotated
import os

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProductImageBase(BaseModel):
    """Base schema for product image attributes"""
    path: Annotated[str, Field(
        description="Path to the product image",
        max_length=256,
        examples=["products/f47ac10b-58cc-4372-a567-0e02b2c3d479"]
    )]
    position: Annotated[int, Field(
        description="Position of the image in the gallery (0=primary)",
        ge=0,
        default=0,
        examples=[0, 1, 2]
    )]


class ProductImageCreate(ProductImageBase):
    """Schema for creating a new product image"""
    pass


class ProductImageUpdate(BaseModel):
    """Schema for updating a product image"""
    position: Annotated[int, Field(
        description="New position for the image in the gallery",
        ge=0,
        examples=[0, 1, 2]
    )]


class ProductImage(ProductImageBase):
    """Schema for returning product image data"""
    id: Annotated[int, Field(gt=0, description="The unique identifier for the image")]
    produse_id: Annotated[int, Field(gt=0, description="The ID of the product this image belongs to")]
    
    @computed_field
    def is_primary(self) -> bool:
        """Whether this is the primary image (position=0)"""
        return self.position == 0
    
    @computed_field
    def image_versions(self) -> Dict[str, str]:
        """Generate paths for different versions of this image"""
        if not self.path:
            # Return placeholder image path from system config
            return {
                "original": "/api/v1/static/placeholders/product_placeholder.jpg",
                "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
                "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
            }
        
        # Extract the image ID from the path (last part of the path)
        image_id = os.path.basename(self.path)
        
        # Return paths for all versions
        return {
            "original": f"{self.path}/{image_id}.jpg",
            "medium": f"{self.path}/{image_id}-medium.jpg",
            "thumbnail": f"{self.path}/{image_id}-thumbnail.jpg"
        }
    
    model_config = ConfigDict(
        from_attributes=True
    )
