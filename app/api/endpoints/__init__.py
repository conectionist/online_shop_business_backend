# Make the endpoints directory a Python package

from app.api.endpoints.unitati import router as unitati_router  # noqa: F401
from app.api.endpoints.modalitati_plata import router as modalitati_plata_router  # noqa: F401
