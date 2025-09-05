from typing import Optional, Annotated, List, Literal
from datetime import datetime
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator


def validate_phone_number_format(phone: str) -> str:
    """
    Validate phone number format and return cleaned version.
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        Cleaned phone number string
        
    Raises:
        ValueError: If phone number format is invalid
    """
    phone = phone.strip()
    
    # Empty string should be rejected
    if phone == "":
        raise ValueError("phone_number cannot be empty")
    
    # Check length (max 20 characters as per database field)
    if len(phone) > 20:
        raise ValueError("phone_number cannot exceed 20 characters")
    
    # Check format: 7-20 digits, optional + prefix
    if not re.match(r'^\+?[0-9]\d{6,19}$', phone):
        raise ValueError("phone_number must be a valid phone number (7-20 digits, optional + prefix)")
    
    return phone


class OrderItemBase(BaseModel):
    """Base schema for order item attributes bound to comenzi_au_produse"""

    produse_id: Annotated[int, Field(gt=0, description="ID of the product")]
    pret_produs: Annotated[int, Field(ge=0, description="Unit price in cents at order time")]
    cantitate_produs: Annotated[int, Field(gt=0, description="Ordered quantity (positive integer)")]
    unitati_id: Annotated[int, Field(gt=0, description="Unit of measurement ID")]


class OrderItem(OrderItemBase):
    """Schema for returning order item data"""

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Schema for creating a new order"""

    nume_client: Annotated[str, Field(min_length=1, max_length=50, description="Customer name")]
    phone_number: Optional[str] = Field(None, max_length=20, description="Optional customer phone number")
    data_plasarii: Annotated[datetime, Field(description="Order placement datetime")]
    liste_id: Annotated[int, Field(gt=0, description="Related list ID")]
    delivery_type_id: Annotated[int, Field(gt=0, description="Delivery type ID (required)")]
    payment_method_id: Annotated[int, Field(gt=0, description="Payment method ID (required)")]
    delivery_address: Optional[str] = Field(None, max_length=150, description="Optional delivery address for home delivery")
    order_notes: Optional[str] = Field(None, max_length=500, description="Optional order notes")
    items: Optional[List[OrderItemBase]] = Field(default=None, description="Optional order items to create together with the order")

    @field_validator('nume_client')
    @classmethod
    def validate_nume_client(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("nume_client cannot be empty or whitespace")
        return v.strip()

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_phone_number_format(v)
        return v


class OrderUpdate(BaseModel):
    """Schema for updating an existing order (limited fields)"""

    nume_client: Optional[str] = Field(default=None, min_length=1, max_length=50, description="Customer name")
    phone_number: Optional[str] = Field(default=None, max_length=20, description="Optional customer phone number")
    delivery_type_id: Optional[int] = Field(default=None, gt=0, description="Delivery type ID")
    payment_method_id: Optional[int] = Field(default=None, gt=0, description="Payment method ID")
    delivery_address: Optional[str] = Field(default=None, max_length=150, description="Optional delivery address for home delivery")
    order_notes: Optional[str] = Field(default=None, max_length=500, description="Optional order notes")

    @field_validator('nume_client')
    @classmethod
    def validate_nume_client_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            raise ValueError("nume_client cannot be empty or whitespace")
        return v.strip() if v is not None else v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_phone_number_format(v)
        return v


class Order(BaseModel):
    """Schema for returning order data with items"""

    id: Annotated[int, Field(gt=0, description="Order ID")]
    nume_client: Annotated[str, Field(description="Customer name")]
    phone_number: Optional[str] = Field(None, description="Optional customer phone number")
    data_plasarii: Annotated[datetime, Field(description="Order placement datetime")]
    liste_id: Annotated[int, Field(gt=0, description="Related list ID")]
    delivery_type_id: Annotated[int, Field(gt=0, description="Delivery type ID")]
    payment_method_id: Annotated[int, Field(gt=0, description="Payment method ID")]
    delivery_address: Optional[str] = Field(None, description="Optional delivery address for home delivery")
    order_notes: Optional[str] = Field(None, description="Optional order notes")
    created_at: Annotated[datetime, Field(description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(description="Last update timestamp")]
    items: List[OrderItem] = Field(default_factory=list, description="Order items")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # Format datetime as ISO 8601 with Z suffix (UTC) to comply with RFC 3339
            datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    )


class OrderFilterParams(BaseModel):
    """Filter & pagination params for listing orders"""

    nume_client: Optional[str] = Field(default=None, description="Filter by customer name (substring match)")
    liste_id: Optional[int] = Field(default=None, gt=0, description="Filter by list ID")
    delivery_type_id: Optional[int] = Field(default=None, gt=0, description="Filter by delivery type ID")
    payment_method_id: Optional[int] = Field(default=None, gt=0, description="Filter by payment method ID")
    data_plasarii_start: Optional[datetime] = Field(default=None, description="Start of placement datetime range (inclusive)")
    data_plasarii_end: Optional[datetime] = Field(default=None, description="End of placement datetime range (inclusive)")

    skip: Annotated[int, Field(ge=0, description="Number of records to skip")]=0
    limit: Annotated[int, Field(ge=1, le=1000, description="Maximum number of records to return")]=100

    sort_by: Literal['data_plasarii', 'nume_client', 'liste_id', 'delivery_type_id', 'payment_method_id'] = 'data_plasarii'
    sort_order: Literal['asc', 'desc'] = 'desc'


