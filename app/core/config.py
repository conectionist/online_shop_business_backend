"""Core configuration for the application"""
import os
from typing import List

# API version information
API_VERSION = "0.10.0"
API_TITLE = "Online Shop API"
API_DESCRIPTION = "API for online shop business"

# CORS Configuration
# Get CORS_ORIGINS from environment variable or use defaults
cors_origins_str = os.getenv("CORS_ORIGINS", "")
if cors_origins_str:
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]

# For compatibility with the rest of the application
class Settings:
    API_VERSION = API_VERSION
    API_TITLE = API_TITLE
    API_DESCRIPTION = API_DESCRIPTION
    CORS_ORIGINS = CORS_ORIGINS

settings = Settings()
