from fastapi import APIRouter

from app.api.endpoints import unitati

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(unitati.router, prefix="/unitati", tags=["unitati"])
