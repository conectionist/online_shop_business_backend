import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.product_feed import build_feed_items, render_feed_xml

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/google.xml", response_class=Response, responses={
    200: {
        "description": "Google Merchant Center product feed (RSS 2.0)",
        "content": {"application/xml": {}},
    },
    500: {"description": "Internal server error"}
})
def get_google_product_feed(request: Request, db: Session = Depends(get_db)):
    """
    Product feed for Google Merchant Center (PUBLIC - no auth required).

    Lists every non-deleted product that has an image, with price, availability and,
    for products sold by weight or volume, unit pricing. Products in the current
    published list are in stock; all others are out of stock.
    """
    try:
        # Behind a proxy the request origin is the upstream (e.g. http://api:8000), so
        # production sets PUBLIC_API_URL; the fallback is only right without a proxy
        api_base_url = settings.PUBLIC_API_URL or str(request.base_url).rstrip("/")
        items = build_feed_items(db, frontend_url=settings.FRONTEND_URL, api_base_url=api_base_url)
        return Response(
            content=render_feed_xml(items, frontend_url=settings.FRONTEND_URL),
            media_type="application/xml",
        )
    except Exception:
        # Public endpoint: log the details, don't send them to the caller
        logger.exception("Failed to build the Google product feed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while building the product feed"
        )
