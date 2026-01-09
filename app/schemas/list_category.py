from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ListCategoryCreate(BaseModel):
    """Schema for creating a list-category relationship"""
    position: Optional[int] = Field(None, ge=0, description="Position of the category in the list. If not provided, will be added at the end")
    
    @validator('position')
    def validate_position(cls, v):
        if v is not None and v < 0:
            raise ValueError('Position must be non-negative')
        return v


class ListCategoryUpdate(BaseModel):
    """Schema for updating a list-category relationship"""
    position: int = Field(..., ge=0, description="New position for the category in the list")
    
    @validator('position')
    def validate_position(cls, v):
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v


class ListCategoryResponse(BaseModel):
    """Schema for list-category relationship response"""
    list_id: int = Field(..., description="ID of the list")
    category_id: int = Field(..., description="ID of the category")
    position: int = Field(..., description="Position of the category in the list")
    
    class Config:
        from_attributes = True


class CategoryInListResponse(BaseModel):
    """Schema for category data when returned as part of a list"""
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    image_path: Optional[str] = Field(None, description="Category image path")
    position: int = Field(..., description="Position of the category in the list")
    created_at: datetime = Field(..., description="Category creation timestamp")
    updated_at: datetime = Field(..., description="Category last update timestamp")
    
    class Config:
        from_attributes = True


class ListCategoryBulkCreate(BaseModel):
    """Schema for bulk creating list-category relationships"""
    category_ids: list[int] = Field(..., min_items=1, description="List of category IDs to add")
    start_position: Optional[int] = Field(None, ge=0, description="Starting position for the first category. If not provided, will be added at the end")
    
    @validator('category_ids')
    def validate_category_ids(cls, v):
        if not v:
            raise ValueError('At least one category ID must be provided')
        if len(set(v)) != len(v):
            raise ValueError('Category IDs must be unique')
        return v
    
    @validator('start_position')
    def validate_start_position(cls, v):
        if v is not None and v < 0:
            raise ValueError('Start position must be non-negative')
        return v


class ListCategoryBulkUpdate(BaseModel):
    """Schema for bulk updating list-category positions"""
    category_positions: dict[int, int] = Field(..., description="Mapping of category_id to new position")
    
    @validator('category_positions')
    def validate_category_positions(cls, v):
        if not v:
            raise ValueError('At least one category position must be provided')
        
        # Check that all positions are non-negative
        for category_id, position in v.items():
            if position < 0:
                raise ValueError(f'Position for category {category_id} must be non-negative')
        
        # Check that positions are unique
        positions = list(v.values())
        if len(set(positions)) != len(positions):
            raise ValueError('All positions must be unique')
        
        return v 