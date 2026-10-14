from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin import Admin
from app.schemas.statistics import (
    CurrentListStats,
    CustomerStatsResponse,
    ProductStatsResponse,
    StatsOverview,
)
from app.services.auth import get_current_admin_from_cookie
from app.services.statistics import (
    get_current_list_stats,
    get_customer_stats,
    get_overview,
    get_product_stats,
)


router = APIRouter()

# Period selection shared by the period-based endpoints: a range of list delivery
# dates; without a start date the period is all time. The comparison period is the
# same number of lists right before it, when there are that many.
START_DATE = Query(None, description="First list delivery date (inclusive)")
END_DATE = Query(None, description="Last list delivery date (inclusive)")


@router.get("/overview", response_model=StatsOverview, responses={
    400: {"description": "Invalid period parameters"},
    401: {"description": "Not authenticated"},
})
def read_overview(
    start_date: Optional[date] = START_DATE,
    end_date: Optional[date] = END_DATE,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
):
    """Headline KPIs (with the previous period for comparison), per-list trend,
    delivery/payment splits and the weekday x hour order heatmap."""
    return get_overview(db, start_date=start_date, end_date=end_date)


@router.get("/products", response_model=ProductStatsResponse, responses={
    400: {"description": "Invalid period parameters"},
    401: {"description": "Not authenticated"},
})
def read_product_stats(
    start_date: Optional[date] = START_DATE,
    end_date: Optional[date] = END_DATE,
    limit: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
):
    """Top products by quantity and revenue, revenue per category, products that
    were offered in the period but never ordered, and how often products sold out."""
    return get_product_stats(db, start_date=start_date, end_date=end_date, limit=limit)


@router.get("/customers", response_model=CustomerStatsResponse, responses={
    400: {"description": "Invalid period parameters"},
    401: {"description": "Not authenticated"},
})
def read_customer_stats(
    start_date: Optional[date] = START_DATE,
    end_date: Optional[date] = END_DATE,
    limit: int = Query(10, ge=1, le=100, description="Number of top customers to return"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
):
    """Top customers for the period, by revenue and by number of orders."""
    return get_customer_stats(db, start_date=start_date, end_date=end_date, limit=limit)


@router.get("/current-list", response_model=CurrentListStats, responses={
    401: {"description": "Not authenticated"},
})
def read_current_list_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin_from_cookie),
):
    """Live figures for the current (published) list, including the products that sold out."""
    return get_current_list_stats(db)
