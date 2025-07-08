from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import API_VERSION, API_TITLE, API_DESCRIPTION
from app.core.database import get_db
from app.api.api import api_router

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


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

