from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


class BusinessDetailsBase(BaseModel):
    """Base schema for business details with common fields."""
    
    adresa: Optional[str] = Field(
        None,
        max_length=200,
        description="Business address"
    )
    
    telefon: Optional[str] = Field(
        None,
        max_length=20,
        description="Business phone number"
    )
    
    logo_path: Optional[str] = Field(
        None,
        max_length=256,
        description="Path to business logo image"
    )
    
    motto: Optional[str] = Field(
        None,
        max_length=256,
        description="Business motto or slogan"
    )
    
    list_not_available_msg: Optional[str] = Field(
        None,
        max_length=1000,
        description="Message displayed when product list is not available"
    )
    
    alte_detalii: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional business details"
    )
    
    delivery_tax: Optional[int] = Field(
        None,
        ge=0,
        description="Delivery tax in RON"
    )
    
    # Optional merchant identity fields
    business_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Official company name"
    )
    registration_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Trade Registry number (e.g., J22/1234/2020)"
    )
    CUI: Optional[str] = Field(
        None,
        max_length=16,
        description="Fiscal identification code (e.g., RO12345678)"
    )
    email: Optional[str] = Field(
        None,
        max_length=100,
        description="Official business email"
    )
    operating_hours: Optional[str] = Field(
        None,
        max_length=150,
        description="Operating hours displayed as free text"
    )
    representative: Optional[str] = Field(
        None,
        max_length=100,
        description="Legal representative name and position"
    )
    
    @field_validator('adresa', 'telefon', 'logo_path', 'motto', 'list_not_available_msg', 'alte_detalii',
                     'business_name', 'registration_number', 'CUI', 'email', 'operating_hours', 'representative')
    def strip_and_empty_to_none(cls, v):
        """Strip whitespace; normalize empty strings to None."""
        if v is None:
            return v
        v = v.strip()
        return v if v != '' else None

    @field_validator('registration_number')
    def validate_registration_number(cls, v):
        if v is None:
            return v
        import re
        pattern = r'^[JF][0-9]{2}/[0-9]{1,6}/[0-9]{4}$'
        if not re.match(pattern, v):
            raise ValueError('registration_number must match ^[JF][0-9]{2}/[0-9]{1,6}/[0-9]{4}$')
        return v

    @field_validator('CUI')
    def validate_cui(cls, v):
        if v is None:
            return v
        import re
        pattern = r'^(RO)?[0-9]{2,10}$'
        if not re.match(pattern, v):
            raise ValueError('CUI must match ^(RO)?[0-9]{2,10}$')
        return v

    @field_validator('email')
    def validate_email_format(cls, v):
        if v is None:
            return v
        import re
        # Simple email regex - more lenient than EmailStr
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v


class BusinessDetailsCreate(BusinessDetailsBase):
    """Schema for creating a new business details record."""
    pass


class BusinessDetailsUpdate(BusinessDetailsBase):
    """Schema for updating an existing business details record."""
    pass


class BusinessDetails(BusinessDetailsBase):
    """Schema for business details responses including the ID."""
    
    id: int = Field(gt=0, description="The business details ID")
    # Raw, unprocessed value of list_not_available_msg (read-only)
    list_not_available_msg_raw: Optional[str] = Field(
        None,
        description="Raw, unprocessed list_not_available_msg"
    )
    
    model_config = ConfigDict(from_attributes=True)
