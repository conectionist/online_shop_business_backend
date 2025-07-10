from fastapi import APIRouter

from app.api.endpoints import unitati, modalitati_plata, delivery_types, delivery_schedules, business_details, categories, system_config

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(unitati.router, prefix="/unitati", tags=["unitati"])
api_router.include_router(
    modalitati_plata.router, 
    prefix="/modalitati-plata", 
    tags=["modalitati-plata"]
)
api_router.include_router(
    delivery_types.router,
    prefix="/tipuri-livrare",
    tags=["tipuri-livrare"]
)
api_router.include_router(
    delivery_schedules.router,
    prefix="/orare-livrari",
    tags=["orare-livrari"]
)
api_router.include_router(
    business_details.router,
    prefix="/detalii-business",
    tags=["detalii-business"]
)
api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["categories"]
)
api_router.include_router(
    system_config.router,
    prefix="/system",
    tags=["system-config"]
)
