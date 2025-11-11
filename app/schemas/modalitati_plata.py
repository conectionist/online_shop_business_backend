from typing import Optional, Annotated, Dict, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ModalitatePlataBase(BaseModel):
    """Base schema for payment method attributes"""
    name: Annotated[str, Field(
        description="The internal name of the payment method", 
        min_length=1, 
        max_length=20,
        examples=["card", "cash", "transfer"]
    )]
    
    description: Annotated[str, Field(
        description="The display description of the payment method", 
        min_length=1, 
        max_length=100,
        examples=["Card", "Numerar la livrare", "Transfer Bancar"]
    )]
    
    payment_type_id: Annotated[int, Field(
        description="The payment type ID (0=custom, 1=cash, 2=physical_card, 3=online_card, 4=revolut, 5=bank_transfer)",
        ge=0,
        examples=[0, 1, 4]
    )]
    
    required_data: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON data containing business payment details (where payments are received). For revolut: phone_number (business's Revolut number). For bank_transfer: iban and recipient_name (business's bank account details)."
    )
    
    @field_validator('name', 'description')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class ModalitatePlataCreate(ModalitatePlataBase):
    """Schema for creating a new payment method"""
    pass


class ModalitatePlataUpdate(BaseModel):
    """Schema for updating an existing payment method"""
    name: Optional[str] = Field(
        None, 
        description="The internal name of the payment method", 
        min_length=1, 
        max_length=20
    )
    
    description: Optional[str] = Field(
        None, 
        description="The display description of the payment method", 
        min_length=1, 
        max_length=100
    )
    
    payment_type_id: Optional[int] = Field(
        None,
        description="The payment type ID (0=custom, 1=cash, 2=physical_card, 3=online_card, 4=revolut, 5=bank_transfer)",
        ge=0
    )
    
    required_data: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON data containing required information based on payment type"
    )
    
    @field_validator('name', 'description')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip() if v is not None else v


class ModalitatePlata(ModalitatePlataBase):
    """Schema for returning payment method data"""
    id: Annotated[int, Field(gt=0, description="The unique identifier for the payment method")]
    
    required_fields_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Schema definition for business payment information fields (for client apps to display payment details to customers, e.g., 'Send payment to this Revolut number')"
    )
    
    model_config = ConfigDict(from_attributes=True)  # Modern Pydantic v2 approach
