from typing import Literal, Optional

from pydantic import BaseModel, Field


class UnitPricingAmount(BaseModel):
    value: float = Field(description="Amount, e.g. 600 or 0.75", examples=[600])
    unit: Literal["g", "kg", "ml", "l"] = Field(examples=["g"])


class OfferUnitPricing(BaseModel):
    """How much one item holds (measure) and the base it is priced per (base)."""

    measure: UnitPricingAmount
    base: UnitPricingAmount


class ProductOffer(BaseModel):
    """A product's offer as the Google Merchant feed lists it."""

    product_id: int
    price: int = Field(description="Price in whole lei", examples=[16])
    currency: Literal["RON"]
    availability: Literal["in_stock", "out_of_stock"]
    unit_pricing: Optional[OfferUnitPricing] = Field(
        None, description="Set only for products sold by weight or volume"
    )
