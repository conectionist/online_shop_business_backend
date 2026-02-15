import os
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlparse
from pydantic import BaseModel
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import logging

# Initialize debugpy if DEBUG=1
if os.getenv("DEBUG", "0") == "1":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("🔧 Debugpy listening on 0.0.0.0:5678")
    # Uncomment the next line if you want the app to wait for a debugger to attach
    # debugpy.wait_for_client()

from app.core.config import API_VERSION, API_TITLE, API_DESCRIPTION, settings
from app.core.database import get_db, SessionLocal
from app.core.rate_limit import limiter
from app.api.api import api_router
from app.api.endpoints.system_config import mount_static_files
from app.core.admin_init import initialize_default_admin
from app.services.push_notifications import prune_inactive_subscriptions

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs" if settings.ENABLE_OPENAPI_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_OPENAPI_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_OPENAPI_DOCS else None
)

# Rate limiting (slowapi): per-IP order creation limit
app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 with a clear detail when order creation rate limit is exceeded."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many orders from this IP. Please try again later."},
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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

# Cross-Origin Resource Policy (CORP)
class CORPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cross-Origin-Resource-Policy"] = settings.CORP_POLICY
        return response

app.add_middleware(CORPMiddleware)

# CSRF Origin validation for cookie-based auth.
# Browsers always send the Origin header on cross-origin requests; if the
# header is present and doesn't match our allowed origins we reject the
# request.  Requests without an Origin header (curl, Postman, server-to-server)
# are allowed through.
class OriginValidationMiddleware(BaseHTTPMiddleware):
    UNSAFE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    async def dispatch(self, request: Request, call_next):
        if request.method in self.UNSAFE_METHODS:
            origin = request.headers.get("origin")
            if not origin:
                # Fall back to Referer for clients that send it instead
                referer = request.headers.get("referer")
                if referer:
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None

            if origin:
                allowed = {o.rstrip("/") for o in settings.CORS_ORIGINS}
                if origin.rstrip("/") not in allowed:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Origin not allowed"},
                    )

        return await call_next(request)

app.add_middleware(OriginValidationMiddleware)

# Set up logger for HTTP exceptions
logger = logging.getLogger(__name__)

# Global exception handler for HTTPException to log error details
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Log HTTP exceptions with detailed information including status code and error message.
    This helps debug 4xx errors that would otherwise only show status codes in access logs.
    """
    # Log the error with context
    log_level = logging.WARNING if 400 <= exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        f"HTTP {exc.status_code} error on {request.method} {request.url.path}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "detail": exc.detail,
        }
    )
    
    # Return the standard FastAPI error response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
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
        # Initialize default admin user
        # Note: Database tables are created by Alembic migrations in docker-entrypoint.sh
        initialize_default_admin()
    except Exception as e:
        # Log the error but don't prevent the app from starting
        # This allows the app to start even if admin creation fails
        logger.error(f"Failed to initialize application: {str(e)}")
    
    # Clean up expired sessions
    try:
        from app.services.auth import cleanup_expired_sessions
        
        db = SessionLocal()
        try:
            deleted_count = cleanup_expired_sessions(db, days_to_keep=30)
            db.commit()
            logger.info(f"Startup: Cleaned up {deleted_count} expired sessions")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Startup: Failed to clean up expired sessions: {e}")

    # Start background prune task (non-blocking)
    async def prune_loop():
        while True:
            try:
                db = SessionLocal()
                deleted = prune_inactive_subscriptions(db, older_than_days=7)
                logger.info("Prune loop run complete deleted=%s", deleted)
            except Exception as ex:
                logger.error("Prune loop error: %s", str(ex))
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            # sleep ~24h
            await asyncio.sleep(60 * 60 * 24)

    asyncio.create_task(prune_loop())


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/")
async def root():
    """Root endpoint - returns 404"""
    raise HTTPException(status_code=404, detail="Not Found")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return {"status": "online", "version": API_VERSION}
