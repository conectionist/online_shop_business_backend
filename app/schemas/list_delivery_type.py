from pydantic import BaseModel, ConfigDict, Field


class ListDeliveryTypeBase(BaseModel):
    """Base schema for list-delivery type relationship"""
    liste_id: int = Field(..., gt=0, description="ID of the list")
    tipuri_livrare_id: int = Field(..., gt=0, description="ID of the delivery type")


class ListDeliveryTypeCreate(ListDeliveryTypeBase):
    """Schema for creating a list-delivery type relationship"""
    pass


class ListDeliveryType(ListDeliveryTypeBase):
    """Schema for returning list-delivery type relationship data"""
    
    model_config = ConfigDict(from_attributes=True)


class ListDeliveryTypeResponse(BaseModel):
    """Schema for returning delivery type data in a list context"""
    id: int = Field(..., gt=0, description="Delivery type ID")
    denumire: str = Field(..., description="Delivery type name")
    
    model_config = ConfigDict(from_attributes=True) 