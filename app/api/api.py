from fastapi import APIRouter

from app.api.endpoints import unitati, modalitati_plata

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(unitati.router, prefix="/unitati", tags=["unitati"])
api_router.include_router(
    modalitati_plata.router, 
    prefix="/modalitati-plata", 
    tags=["modalitati-plata"]
)
