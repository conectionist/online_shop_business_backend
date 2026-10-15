"""Core configuration for the application"""
import os
import sys
import logging
from typing import List
from urllib.parse import urlparse

# Configure logging based on LOG_LEVEL env (defaults to INFO)
_log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
logging.basicConfig(level=_log_level)
logging.getLogger(__name__).setLevel(_log_level)
logger = logging.getLogger(__name__)

# API version information
API_VERSION = "6.4.0"
API_TITLE = "Online Shop API"
API_DESCRIPTION = "API for online shop business"

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


def _parse_comma_separated_secrets(raw_value: str) -> List[str]:
    """Parse comma-separated secret values while ignoring empty entries."""
    return [item.strip() for item in raw_value.split(",") if item.strip()]


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

# Environment and security-related configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip() or "development"

# Production must use explicit host(s) for host-header protection; do not allow "*"
if ENVIRONMENT == "production":
    if not allowed_hosts_str or not allowed_hosts_str.strip():
        logger.error(
            "CRITICAL: Production requires ALLOWED_HOSTS to be set to explicit host(s) "
            "(e.g. your API domain). Host-header protection cannot be disabled in production."
        )
        sys.exit(1)
    if allowed_hosts_str.strip() == "*" or ALLOWED_HOSTS == ["*"]:
        logger.error(
            "CRITICAL: Production requires ALLOWED_HOSTS to be set to explicit host(s), not '*'. "
            "Set ALLOWED_HOSTS to your API host(s), e.g. api.example.com"
        )
        sys.exit(1)

# Cookie configuration for authentication tokens
COOKIE_SECURE_DEFAULT = "true" if ENVIRONMENT == "production" else "false"
COOKIE_SECURE = get_optional_env_var(
    "COOKIE_SECURE",
    COOKIE_SECURE_DEFAULT,
    "Whether auth cookies should be marked as Secure (HTTPS only)."
).lower() in ("true", "1", "yes")

COOKIE_SAMESITE = get_optional_env_var(
    "COOKIE_SAMESITE",
    "lax",
    "SameSite policy for auth cookies (lax or strict)."
).lower()

if COOKIE_SAMESITE not in ("lax", "strict"):
    logger.error(
        "CRITICAL: COOKIE_SAMESITE must be 'lax' or 'strict', got '%s'. "
        "'none' is not allowed as it disables CSRF protection.",
        COOKIE_SAMESITE,
    )
    sys.exit(1)

COOKIE_DOMAIN = get_optional_env_var(
    "COOKIE_DOMAIN",
    "",
    "Domain attribute for auth cookies. Empty string lets the framework default to the current host."
).strip()

COOKIE_PATH = get_optional_env_var(
    "COOKIE_PATH",
    "/",
    "Path attribute for auth cookies."
).strip() or "/"

# Frontend URL (used by clients, links in notifications, the Merchant feed, etc.)
_frontend_url_raw = os.getenv("FRONTEND_URL", "").strip()
FRONTEND_URL = _frontend_url_raw if _frontend_url_raw else "http://localhost:3000"

# Public origin of this API (e.g. https://api.example.com), for absolute links such as
# the Merchant feed's image URLs. Empty means "use the request's origin", which is only
# right when no proxy sits in front of the API (dev/test).
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")

# Production links are read by Google and customers, so they must be real public URLs
if ENVIRONMENT == "production":
    for _url_var, _url_value in (("FRONTEND_URL", _frontend_url_raw), ("PUBLIC_API_URL", PUBLIC_API_URL)):
        if not _url_value or urlparse(_url_value).hostname in ("localhost", "127.0.0.1"):
            logger.error(
                "CRITICAL: Production requires %s to be set to its public URL (e.g. https://example.com), "
                "not empty or localhost.",
                _url_var,
            )
            sys.exit(1)

# Cross-Origin Resource Policy (CORP)
# Values: "same-origin", "same-site", "cross-origin"
_corp_policy_raw = os.getenv("CORP_POLICY", "").strip()
if _corp_policy_raw:
    _corp_policy = _corp_policy_raw.lower()
else:
    _corp_policy = "same-site"
if _corp_policy not in ("same-origin", "same-site", "cross-origin"):
    logger.warning(
        "Invalid CORP_POLICY=%s. Falling back to 'same-site'.",
        _corp_policy_raw,
    )
    _corp_policy = "same-site"
CORP_POLICY = _corp_policy

# JWT Configuration - Critical security settings
JWT_SECRET_KEY = get_required_env_var(
    "JWT_SECRET_KEY", 
    "This is required for JWT token security. Set a secure secret key in your environment."
)
JWT_ALGORITHM = get_optional_env_var("JWT_ALGORITHM", "HS256", "JWT algorithm to use")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(get_optional_env_var("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30", "Access token expiration in minutes"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(get_optional_env_var("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7", "Refresh token expiration in days"))

# Derived cookie lifetimes (in seconds)
ACCESS_TOKEN_COOKIE_MAX_AGE = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_TOKEN_COOKIE_MAX_AGE = JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

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
# Disable OpenAPI docs by default in production for security, enable in dev/test
_default_openapi_docs = "false" if ENVIRONMENT == "production" else "true"
ENABLE_OPENAPI_DOCS = get_optional_env_var(
    "ENABLE_OPENAPI_DOCS",
    _default_openapi_docs,
    "Enable/disable OpenAPI documentation endpoints"
).lower() in ("true", "1", "yes")

# Metrics endpoint and Prometheus counters
ENABLE_METRICS = get_optional_env_var(
    "ENABLE_METRICS",
    "true",
    "Enable/disable Prometheus metrics endpoint and metric collection"
).lower() in ("true", "1", "yes")

_default_metrics_auth_required = "true" if ENVIRONMENT == "production" else "false"
METRICS_AUTH_REQUIRED = get_optional_env_var(
    "METRICS_AUTH_REQUIRED",
    _default_metrics_auth_required,
    "Require Bearer authentication for /metrics endpoint"
).lower() in ("true", "1", "yes")
METRICS_BEARER_TOKENS = _parse_comma_separated_secrets(
    get_optional_env_var(
        "METRICS_BEARER_TOKENS",
        "",
        "Comma-separated Bearer tokens accepted by /metrics endpoint",
    )
)

if METRICS_AUTH_REQUIRED and not METRICS_BEARER_TOKENS:
    logger.error(
        "CRITICAL: METRICS_AUTH_REQUIRED is enabled but METRICS_BEARER_TOKENS is empty."
    )
    sys.exit(1)

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

# Feature flags / guards
ALLOW_PUBLIC_PUSH_SUBSCRIBE = get_optional_env_var(
    "ALLOW_PUBLIC_PUSH_SUBSCRIBE",
    "false",
    "Allow unauthenticated public push subscriptions"
).lower() in ("true", "1", "yes")

# Redis Configuration
REDIS_HOST = get_optional_env_var("REDIS_HOST", "redis", "Redis hostname")
REDIS_PORT = int(get_optional_env_var("REDIS_PORT", "6379", "Redis port"))
REDIS_DB = int(get_optional_env_var("REDIS_DB", "0", "Redis database number"))
REDIS_USERNAME = get_optional_env_var("REDIS_USERNAME", "", "Redis ACL username").strip()
REDIS_PASSWORD = get_optional_env_var("REDIS_PASSWORD", "", "Redis ACL password").strip()

if ENVIRONMENT == "production":
    if not REDIS_USERNAME:
        logger.error(
            "CRITICAL: Production requires REDIS_USERNAME to be set for authenticated Redis access."
        )
        sys.exit(1)
    if not REDIS_PASSWORD:
        logger.error(
            "CRITICAL: Production requires REDIS_PASSWORD to be set for authenticated Redis access."
        )
        sys.exit(1)

# Image upload: max file size in MB (product/category images)
MAX_IMAGE_SIZE_MB = int(get_optional_env_var("MAX_IMAGE_SIZE_MB", "15", "Max image upload size in MB"))

# Order creation rate limit (per-IP, slowapi). Limit string = ORDER_RATE_LIMIT_MAX/ORDER_RATE_LIMIT_WINDOW (no space).
ORDER_RATE_LIMIT_MAX = int(get_optional_env_var("ORDER_RATE_LIMIT_MAX", "10", "Max orders per IP per window"))
ORDER_RATE_LIMIT_WINDOW = get_optional_env_var(
    "ORDER_RATE_LIMIT_WINDOW", "24hour", "Rate limit window: second, minute, hour, day, or Nhour, Nday, etc. (no space)"
).strip()
ORDER_RATE_LIMIT_STRING = f"{ORDER_RATE_LIMIT_MAX}/{ORDER_RATE_LIMIT_WINDOW}"

# Admin login brute-force protection (per-IP, slowapi).
# Limit string = LOGIN_RATE_LIMIT_MAX/LOGIN_RATE_LIMIT_WINDOW (no space).
# Defaults:
# - Production: conservative (5 attempts / 5 minutes)
# - Non-production (dev/test): very high ceiling to avoid interfering with tests
_default_login_limit_max = "5" if ENVIRONMENT == "production" else "1000"
_default_login_window = "5minute"
LOGIN_RATE_LIMIT_MAX = int(get_optional_env_var(
    "LOGIN_RATE_LIMIT_MAX",
    _default_login_limit_max,
    "Max admin login attempts per IP per window"
))
LOGIN_RATE_LIMIT_WINDOW = get_optional_env_var(
    "LOGIN_RATE_LIMIT_WINDOW",
    _default_login_window,
    "Login rate limit window: second, minute, hour, day, or Nhour, Nday, etc. (no space)"
).strip()
LOGIN_RATE_LIMIT_STRING = f"{LOGIN_RATE_LIMIT_MAX}/{LOGIN_RATE_LIMIT_WINDOW}"

# For compatibility with the rest of the application
class Settings:
    def __init__(self):
        # API Settings
        self.API_VERSION = API_VERSION
        self.API_TITLE = API_TITLE
        self.API_DESCRIPTION = API_DESCRIPTION
        self.CORS_ORIGINS = CORS_ORIGINS
        self.ALLOWED_HOSTS = ALLOWED_HOSTS
        self.ENVIRONMENT = ENVIRONMENT
        self.FRONTEND_URL = FRONTEND_URL
        self.PUBLIC_API_URL = PUBLIC_API_URL
        self.CORP_POLICY = CORP_POLICY
        
        # JWT Settings
        self.JWT_SECRET_KEY = JWT_SECRET_KEY
        self.JWT_ALGORITHM = JWT_ALGORITHM
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = JWT_REFRESH_TOKEN_EXPIRE_DAYS

        # Cookie / auth settings
        self.COOKIE_SECURE = COOKIE_SECURE
        self.COOKIE_SAMESITE = COOKIE_SAMESITE
        self.COOKIE_DOMAIN = COOKIE_DOMAIN
        self.COOKIE_PATH = COOKIE_PATH
        self.ACCESS_TOKEN_COOKIE_MAX_AGE = ACCESS_TOKEN_COOKIE_MAX_AGE
        self.REFRESH_TOKEN_COOKIE_MAX_AGE = REFRESH_TOKEN_COOKIE_MAX_AGE
        
        # Admin Settings
        self.ADMIN_USERNAME = ADMIN_USERNAME
        self.ADMIN_PASSWORD = ADMIN_PASSWORD
        
        # OpenAPI Settings
        self.ENABLE_OPENAPI_DOCS = ENABLE_OPENAPI_DOCS
        self.ENABLE_METRICS = ENABLE_METRICS
        self.METRICS_AUTH_REQUIRED = METRICS_AUTH_REQUIRED
        self.METRICS_BEARER_TOKENS = METRICS_BEARER_TOKENS

        # Web Push (VAPID) Settings
        self.VAPID_PUBLIC_KEY = VAPID_PUBLIC_KEY
        self.VAPID_PRIVATE_KEY = VAPID_PRIVATE_KEY
        self.VAPID_SUBJECT = VAPID_SUBJECT

        # Feature flags
        self.ALLOW_PUBLIC_PUSH_SUBSCRIBE = ALLOW_PUBLIC_PUSH_SUBSCRIBE

        # Redis
        self.REDIS_HOST = REDIS_HOST
        self.REDIS_PORT = REDIS_PORT
        self.REDIS_DB = REDIS_DB
        self.REDIS_USERNAME = REDIS_USERNAME
        self.REDIS_PASSWORD = REDIS_PASSWORD

        # Image upload
        self.MAX_IMAGE_SIZE_MB = MAX_IMAGE_SIZE_MB

        # Order creation rate limit (per-IP)
        self.ORDER_RATE_LIMIT_MAX = ORDER_RATE_LIMIT_MAX
        self.ORDER_RATE_LIMIT_WINDOW = ORDER_RATE_LIMIT_WINDOW
        self.ORDER_RATE_LIMIT_STRING = ORDER_RATE_LIMIT_STRING

        # Admin login brute-force protection
        self.LOGIN_RATE_LIMIT_MAX = LOGIN_RATE_LIMIT_MAX
        self.LOGIN_RATE_LIMIT_WINDOW = LOGIN_RATE_LIMIT_WINDOW
        self.LOGIN_RATE_LIMIT_STRING = LOGIN_RATE_LIMIT_STRING

settings = Settings()
