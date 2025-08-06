from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ListProductOrderedCreate(BaseModel):
    """Schema for creating a list-product ordered relationship"""
    position: Optional[int] = Field(None, ge=0, description="Position of the product within its category. If not provided, will be added at the end")
    stoc_produs: Optional[int] = Field(None, ge=0, description="Available stock for this product in this list")
    
    @validator('position')
    def validate_position(cls, v):
        if v is not None and v < 0:
            raise ValueError('Position must be non-negative')
        return v
    
    @validator('stoc_produs')
    def validate_stoc_produs(cls, v):
        if v is not None and v < 0:
            raise ValueError('Stock must be non-negative')
        return v


class ListProductOrderedUpdate(BaseModel):
    """Schema for updating a list-product ordered relationship"""
    position: Optional[int] = Field(None, ge=0, description="New position of the product within its category")
    stoc_produs: Optional[int] = Field(None, ge=0, description="New stock value for this product in this list")
    
    @validator('position')
    def validate_position(cls, v):
        if v is not None and v < 0:
            raise ValueError('Position must be non-negative')
        return v
    
    @validator('stoc_produs')
    def validate_stoc_produs(cls, v):
        if v is not None and v < 0:
            raise ValueError('Stock must be non-negative')
        return v


class ListProductOrderedResponse(BaseModel):
    """Schema for list-product ordered relationship response"""
    list_id: int = Field(..., description="ID of the list")
    product_id: int = Field(..., description="ID of the product")
    category_id: int = Field(..., description="ID of the category")
    position: int = Field(..., description="Position of the product within its category")
    stoc_produs: Optional[int] = Field(None, description="Available stock for this product in this list")
    
    class Config:
        from_attributes = True


class ProductInListResponse(BaseModel):
    """Schema for product data when returned as part of a list"""
    id: int = Field(..., description="Product ID")
    nume: str = Field(..., description="Product name")
    cantitate: float = Field(..., description="Product quantity")
    pret: float = Field(..., description="Product price")
    description: Optional[str] = Field(None, description="Product description")
    category_id: int = Field(..., description="Product category ID")
    unitati_id: int = Field(..., description="Product units ID")
    position: int = Field(..., description="Position of the product within its category")
    stoc_produs: Optional[int] = Field(None, description="Available stock for this product in this list")
    created_at: datetime = Field(..., description="Product creation timestamp")
    updated_at: datetime = Field(..., description="Product last update timestamp")
    is_deleted: bool = Field(..., description="Whether the product is soft-deleted")
    images: List[dict] = Field(default_factory=list, description="Product images with versions")
    
    class Config:
        from_attributes = True


class CategoryWithProductsResponse(BaseModel):
    """Schema for category with its products when returned as part of a list"""
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    position: int = Field(..., description="Position of the category in the list")
    products: List[ProductInListResponse] = Field(..., description="Products in this category, ordered by position")
    
    class Config:
        from_attributes = True


class ListProductsOrderedResponse(BaseModel):
    """Schema for complete list with products grouped by category and ordered"""
    list_id: int = Field(..., description="ID of the list")
    categories: List[CategoryWithProductsResponse] = Field(..., description="Categories with their products, ordered by position")
    
    class Config:
        from_attributes = True


class MoveProductRequest(BaseModel):
    """Schema for moving a product between categories"""
    new_category_id: int = Field(..., gt=0, description="ID of the category to move the product to")
    new_position: Optional[int] = Field(None, ge=0, description="New position within the target category. If not provided, will be added at the end")
    
    @validator('new_category_id')
    def validate_new_category_id(cls, v):
        if v <= 0:
            raise ValueError('Category ID must be positive')
        return v
    
    @validator('new_position')
    def validate_new_position(cls, v):
        if v is not None and v < 0:
            raise ValueError('Position must be non-negative')
        return v


class ListProductOrderedBulkCreate(BaseModel):
    """Schema for bulk creating list-product ordered relationships"""
    products: List[dict] = Field(..., min_items=1, description="List of product data with category_id, product_id, position, and stoc_produs")
    
    @validator('products')
    def validate_products(cls, v):
        if not v:
            raise ValueError('At least one product must be provided')
        
        for product in v:
            required_fields = ['product_id', 'category_id']
            for field in required_fields:
                if field not in product:
                    raise ValueError(f'Product missing required field: {field}')
            
            if product.get('position') is not None and product['position'] < 0:
                raise ValueError(f'Position for product {product["product_id"]} must be non-negative')
            
            if product.get('stoc_produs') is not None and product['stoc_produs'] < 0:
                raise ValueError(f'Stock for product {product["product_id"]} must be non-negative')
        
        return v


class ListProductOrderedBulkUpdate(BaseModel):
    """Schema for bulk updating list-product ordered positions"""
    product_positions: dict[int, int] = Field(..., description="Mapping of product_id to new position within its category")
    
    @validator('product_positions')
    def validate_product_positions(cls, v):
        if not v:
            raise ValueError('At least one product position must be provided')
        
        # Check that all positions are non-negative
        for product_id, position in v.items():
            if position < 0:
                raise ValueError(f'Position for product {product_id} must be non-negative')
        
        return v 