from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.product_feed import build_feed_items, render_feed_xml

router = APIRouter()


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
        # Uvicorn runs with --proxy-headers, so this is the public API origin
        api_base_url = str(request.base_url).rstrip("/")
        items = build_feed_items(db, frontend_url=settings.FRONTEND_URL, api_base_url=api_base_url)
        return Response(
            content=render_feed_xml(items, frontend_url=settings.FRONTEND_URL),
            media_type="application/xml",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
