"""Core configuration for the application"""
import os
import sys
import logging
from typing import List

# Configure logging based on LOG_LEVEL env (defaults to INFO)
_log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
logging.basicConfig(level=_log_level)
logging.getLogger(__name__).setLevel(_log_level)
logger = logging.getLogger(__name__)

# API version information
API_VERSION = "3.4.0"
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
        "https://localhost:3000",
        "http://localhost:8000",
        "https://localhost:8000"
    ]

# Trusted Hosts configuration for FastAPI TrustedHostMiddleware
# Accept comma-separated host patterns (e.g. "example.com,*.example.com,localhost,127.0.0.1,*")
allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "*")
if allowed_hosts_str:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(",") if host.strip()]
else:
    # Fallback to wildcard to preserve previous behavior that included "*"
    ALLOWED_HOSTS = ["*"]

# JWT Configuration - Fail fast if not configured
def get_required_env_var(var_name: str, description: str) -> str:
    """Get a required environment variable or exit gracefully if missing"""
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        error_msg = f"CRITICAL ERROR: Required environment variable '{var_name}' is not set or is empty. {description}"
        logger.error(error_msg)
        logger.error("Application cannot start without this configuration. Please check your environment variables.")
        sys.exit(1)
    return value


def get_optional_env_var(var_name: str, default: str, description: str) -> str:
    """Get an optional environment variable with a default"""
    return os.getenv(var_name, default)

# JWT Configuration - Critical security settings
JWT_SECRET_KEY = get_required_env_var(
    "JWT_SECRET_KEY", 
    "This is required for JWT token security. Set a secure secret key in your environment."
)
JWT_ALGORITHM = get_optional_env_var("JWT_ALGORITHM", "HS256", "JWT algorithm to use")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(get_optional_env_var("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30", "Access token expiration in minutes"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(get_optional_env_var("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7", "Refresh token expiration in days"))

# Admin Configuration - Critical for initial admin creation
ADMIN_USERNAME = get_required_env_var(
    "ADMIN_USERNAME",
    "This is required for initial admin user creation. Set the default admin username in your environment."
)
ADMIN_PASSWORD = get_required_env_var(
    "ADMIN_PASSWORD", 
    "This is required for initial admin user creation. Set the default admin password in your environment."
)

# OpenAPI Documentation Configuration
# Disable OpenAPI docs in production for security, enable in dev/test
ENABLE_OPENAPI_DOCS = get_optional_env_var("ENABLE_OPENAPI_DOCS", "true", "Enable/disable OpenAPI documentation endpoints").lower() in ("true", "1", "yes")

# Web Push (VAPID) Configuration - optional for now; required when sending notifications
VAPID_PUBLIC_KEY = get_optional_env_var(
    "VAPID_PUBLIC_KEY",
    "",
    "Public VAPID key used by clients to subscribe"
)
VAPID_PRIVATE_KEY = get_optional_env_var(
    "VAPID_PRIVATE_KEY",
    "",
    "Private VAPID key used to sign push messages"
)
VAPID_SUBJECT = get_optional_env_var(
    "VAPID_SUBJECT",
    "mailto:admin@example.com",
    "Contact subject for VAPID (mailto or URL)"
)

# For compatibility with the rest of the application
class Settings:
    def __init__(self):
        # API Settings
        self.API_VERSION = API_VERSION
        self.API_TITLE = API_TITLE
        self.API_DESCRIPTION = API_DESCRIPTION
        self.CORS_ORIGINS = CORS_ORIGINS
        self.ALLOWED_HOSTS = ALLOWED_HOSTS
        
        # JWT Settings
        self.JWT_SECRET_KEY = JWT_SECRET_KEY
        self.JWT_ALGORITHM = JWT_ALGORITHM
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = JWT_REFRESH_TOKEN_EXPIRE_DAYS
        
        # Admin Settings
        self.ADMIN_USERNAME = ADMIN_USERNAME
        self.ADMIN_PASSWORD = ADMIN_PASSWORD
        
        # OpenAPI Settings
        self.ENABLE_OPENAPI_DOCS = ENABLE_OPENAPI_DOCS

        # Web Push (VAPID) Settings
        self.VAPID_PUBLIC_KEY = VAPID_PUBLIC_KEY
        self.VAPID_PRIVATE_KEY = VAPID_PRIVATE_KEY
        self.VAPID_SUBJECT = VAPID_SUBJECT

settings = Settings()
