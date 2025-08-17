import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

# Initialize debugpy if DEBUG=1
if os.getenv("DEBUG", "0") == "1":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("🔧 Debugpy listening on 0.0.0.0:5678")
    # Uncomment the next line if you want the app to wait for a debugger to attach
    # debugpy.wait_for_client()

from app.core.config import API_VERSION, API_TITLE, API_DESCRIPTION, settings
from app.core.database import get_db, Base, engine
from app.api.api import api_router
from app.api.endpoints.system_config import mount_static_files
from app.core.admin_init import initialize_default_admin

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Add TrustedHostMiddleware to handle proxy headers
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Mount static files for placeholders
mount_static_files(app)

# Initialize default admin user on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Initialize default admin user
        initialize_default_admin()
    except Exception as e:
        # Log the error but don't prevent the app from starting
        # This allows the app to start even if admin creation fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize application: {str(e)}")


class HealthResponse(BaseModel):
    status: str
    version: str


class DbTestResponse(BaseModel):
    status: str
    unit_count: int


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {"status": "online", "version": API_VERSION}


@app.get("/db-test", response_model=DbTestResponse)
async def db_test(db: Session = Depends(get_db)):
    """Test database connection"""
    try:
        # Execute a simple query to check the database connection
        result = db.execute(text("SELECT COUNT(*) FROM unitati"))
        unit_count = result.scalar()
        return {"status": "connected", "unit_count": unit_count}
    except Exception as e:
        return {"status": f"error: {str(e)}", "unit_count": 0}

