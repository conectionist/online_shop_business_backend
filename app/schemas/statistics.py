"""Pydantic schemas for the admin statistics endpoints.

All monetary values are whole RON and cover product sales only
(delivery fees are not stored per order, so they are excluded).
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class StatsPeriod(BaseModel):
    """The resolved period the statistics were computed for."""

    start_date: Optional[date] = Field(None, description="Delivery date of the first list in the period")
    end_date: Optional[date] = Field(None, description="Delivery date of the last list in the period")
    list_count: int = Field(..., description="Number of lists (with orders) in the period")
    previous_start_date: Optional[date] = Field(None, description="Start of the comparison period")
    previous_end_date: Optional[date] = Field(None, description="End of the comparison period")
    previous_list_count: int = Field(0, description="Number of lists in the comparison period")


class StatsSummary(BaseModel):
    """Headline KPIs for a period."""

    revenue: int = Field(..., description="Product revenue in RON")
    orders: int = Field(..., description="Number of non-deleted orders")
    average_order_value: float = Field(..., description="Revenue / orders")
    items_sold: int = Field(..., description="Sum of ordered quantities")
    unique_customers: int = Field(..., description="Distinct customers (phone, falling back to name)")
    returning_customers: int = Field(..., description="Customers who ordered in at least two lists so far")
    repeat_customer_rate: float = Field(..., description="returning_customers / unique_customers (0-1)")
    cancelled_orders: int = Field(..., description="Soft-deleted orders")
    cancelled_rate: float = Field(..., description="cancelled / (orders + cancelled) (0-1)")


class ListStatsPoint(BaseModel):
    """Per-list (delivery round) figures, used for trend charts."""

    list_id: int
    data: date = Field(..., description="List delivery date")
    orders: int
    revenue: int
    average_order_value: float
    customers: int
    new_customers: int = Field(..., description="Customers whose first ever order is in this list")
    returning_customers: int


class BreakdownSlice(BaseModel):
    """One slice of a categorical split (delivery type, payment method)."""

    id: int
    name: str
    orders: int
    revenue: int


class HeatmapCell(BaseModel):
    """Order count for a weekday/hour bucket, in Romanian local time."""

    weekday: int = Field(..., ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    hour: int = Field(..., ge=0, le=23)
    orders: int


class StatsOverview(BaseModel):
    period: StatsPeriod
    summary: StatsSummary
    previous_summary: Optional[StatsSummary] = None
    lists: List[ListStatsPoint]
    delivery_types: List[BreakdownSlice]
    payment_methods: List[BreakdownSlice]
    heatmap: List[HeatmapCell]


class ProductStat(BaseModel):
    product_id: int
    name: str
    category_name: Optional[str] = None
    unit: Optional[str] = None
    quantity: int
    revenue: int
    orders: int = Field(..., description="Number of orders containing the product")


class CategoryStat(BaseModel):
    category_id: int
    name: str
    quantity: int
    revenue: int


class UnsoldProduct(BaseModel):
    product_id: int
    name: str
    category_name: Optional[str] = None
    times_offered: int = Field(..., description="Number of lists in the period that offered the product")


class ProductStatsResponse(BaseModel):
    period: StatsPeriod
    top_by_quantity: List[ProductStat]
    top_by_revenue: List[ProductStat]
    categories: List[CategoryStat]
    unsold_products: List[UnsoldProduct]


class CustomerStat(BaseModel):
    name: str
    phone_number: Optional[str] = None
    orders: int
    lists: int = Field(..., description="Number of distinct lists ordered from")
    revenue: int
    last_order_date: datetime


class CustomerStatsResponse(BaseModel):
    period: StatsPeriod
    top_customers: List[CustomerStat] = Field(..., description="Top customers by revenue")
    top_customers_by_orders: List[CustomerStat] = Field(..., description="Top customers by number of orders")


class StockItem(BaseModel):
    product_id: int
    name: str
    unit: Optional[str] = None
    stock: int
    ordered: int
    remaining: int
    sell_through: float = Field(..., description="ordered / stock (0-1, may exceed 1)")


class CurrentListInfo(BaseModel):
    id: int
    data: date
    expiration_date: Optional[datetime] = None
    is_published: bool


class PreviousListInfo(BaseModel):
    id: int
    data: date
    orders: int
    revenue: int


class CurrentListStats(BaseModel):
    list: Optional[CurrentListInfo] = None
    orders: int = 0
    revenue: int = 0
    customers: int = 0
    items_sold: int = 0
    previous: Optional[PreviousListInfo] = None
    stock: List[StockItem] = []
    sold_out_count: int = 0
    low_stock_count: int = Field(0, description="Products at >= 80% sell-through but not sold out")
