from fastapi import FastAPI
from pydantic import BaseModel

from app.core.config import API_VERSION, API_TITLE, API_DESCRIPTION

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {"status": "online", "version": API_VERSION}

@app.get("/produse")
async def produse(category: str, price: int):
    """Produse endpoint with intentional bugs (no Query)"""
    # If the category is 'fail', return a bogus dict (missing 'category' and 'price')
    if price % 2 == 0:
        return {"cat": category, "prc": price}
    # Otherwise, return the correct response
    else:
        return {"category": category, "price": price}