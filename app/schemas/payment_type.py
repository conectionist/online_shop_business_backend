from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class PaymentTypeBase(BaseModel):
    """Base schema for payment type attributes"""
    name: Annotated[str, Field(
        description="The enum name of the payment type",
        min_length=1,
        max_length=50,
        examples=["cash", "revolut", "bank_transfer"]
    )]
    
    friendly_name: Annotated[str, Field(
        description="The display-friendly name of the payment type",
        min_length=1,
        max_length=100,
        examples=["Cash", "Revolut Transfer", "Bank Transfer"]
    )]


class PaymentType(PaymentTypeBase):
    """Schema for returning payment type data"""
    id: Annotated[int, Field(ge=0, description="The unique identifier for the payment type")]
    
    model_config = ConfigDict(from_attributes=True)

