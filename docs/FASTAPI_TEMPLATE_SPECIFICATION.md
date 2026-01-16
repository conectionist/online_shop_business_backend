# FastAPI API Server Template - Complete Specification

## Table of Contents
1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Technology Stack](#technology-stack)
4. [Configuration Management](#configuration-management)
5. [Database Setup](#database-setup)
6. [Application Architecture](#application-architecture)
7. [Authentication & Authorization](#authentication--authorization)
8. [Error Handling](#error-handling)
9. [Logging](#logging)
10. [API Design Patterns](#api-design-patterns)
11. [Testing Framework](#testing-framework)
12. [Docker & Containerization](#docker--containerization)
13. [CI/CD Pipeline](#cicd-pipeline)
14. [Security Best Practices](#security-best-practices)
15. [Code Organization Patterns](#code-organization-patterns)
16. [Development Workflow](#development-workflow)
17. [Convenience Scripts](#convenience-scripts)
18. [Development Guidelines](#development-guidelines)
19. [AI Rules](#ai-rules)
20. [Metrics & Observability](#metrics--observability)
21. [Deployment](#deployment)
22. [Minimal Functionality](#minimal-functionality)

---

## Overview

This document specifies a production-ready FastAPI template project that provides a solid foundation for building RESTful APIs. The template includes all essential infrastructure components (database, authentication, error handling, logging, testing, CI/CD) while maintaining minimal business logic. Developers can fork this template and focus on implementing their domain-specific functionality without reinventing common patterns.

### Key Principles
- **Separation of Concerns**: Clear boundaries between API, services, models, and schemas
- **DRY (Don't Repeat Yourself)**: Reusable patterns and utilities to minimize duplication
- **Fail Fast**: Configuration validation on startup
- **Security First**: Secure defaults and best practices built-in
- **Testability**: Comprehensive testing framework ready to use
- **Production Ready**: Docker, CI/CD, monitoring, and logging configured

---

## Project Structure

```
project_root/
├── .github/
│   └── workflows/
│       ├── api-tests.yml          # Automated test and build pipeline (on push/PR)
│       └── docker-build-manual.yml # Manual build pipeline (workflow_dispatch)
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api.py                 # Main API router
│   │   ├── dependencies.py       # Shared dependencies (auth, rate limiting, etc.)
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── health.py          # Health check endpoints
│   │       └── version.py         # Version endpoint (minimal functionality)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Application configuration (Pydantic Settings)
│   │   ├── database.py            # Database connection and session management
│   │   ├── security.py           # JWT, password hashing, token management
│   │   ├── exceptions.py         # Custom exceptions and handlers
│   │   ├── middleware.py          # Custom middleware (logging, request ID, etc.)
│   │   └── constants.py           # Application constants
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py                # Base model with common fields (id, timestamps, soft delete)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py              # Common response schemas
│   │   └── version.py             # Version response schema
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py                # Base service class with common CRUD operations
│   │   └── version.py             # Version service (minimal example)
│   └── utils/
│       ├── __init__.py
│       ├── logging.py             # Structured logging utilities
│       └── validators.py          # Common validation functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures (DB, client, etc.)
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_utils.py           # Base test utilities class
│   │   ├── test_auth_utils.py      # Authentication test utilities
│   │   ├── test_health.py          # Health check tests
│   │   └── test_version.py         # Version endpoint tests (example)
│   └── unit/
│       ├── __init__.py
│       └── test_services.py       # Unit tests for services
├── migrations/
│   ├── env.py                     # Alembic environment configuration
│   ├── env.py.template            # Template for env.py
│   ├── script.py.mako             # Alembic migration script template
│   └── versions/                  # Migration files
├── docker/
│   ├── Dockerfile                 # Production Dockerfile
│   ├── Dockerfile.test            # Test Dockerfile
│   └── docker-entrypoint.sh       # Container entrypoint script
├── .env.example                   # Example environment variables
├── .env.test                      # Test environment variables
├── .gitignore
├── docker-compose.yml             # Production docker-compose
├── docker-compose.test.yml        # Test docker-compose
├── docker-compose.monitoring.yml  # Optional monitoring services (Prometheus, Grafana, etc.)
├── monitoring/                    # Monitoring service configurations
│   ├── prometheus/
│   │   └── prometheus.yml         # Prometheus configuration
│   ├── grafana/
│   │   ├── provisioning/          # Grafana datasources and dashboards
│   │   └── dashboards/             # Grafana dashboard JSON files
│   ├── loki/
│   │   └── loki-config.yml        # Loki configuration
│   └── alloy/
│       └── config.river            # Grafana Alloy configuration (log shipper)
├── alembic.ini.template           # Alembic configuration template
├── logging.ini                    # Logging configuration
├── requirements.txt               # Production dependencies
├── requirements-test.txt          # Test dependencies
├── setup_env.sh                   # Environment setup script
├── scripts/                       # Convenience scripts directory
│   ├── run_api_integration_tests.sh  # Integration test runner script
│   └── rollback.sh                # Production rollback script
└── README.md                      # Project documentation
```

---

## Technology Stack

### Core Framework
- **FastAPI** (latest stable): Modern, fast web framework
- **Python** 3.11+: Type hints, modern Python features
- **Uvicorn**: ASGI server with workers support

> **⚠️ Important Note on Dependencies**: The version numbers specified in this document are examples. When implementing this template, developers should check for the latest stable versions of all dependencies (FastAPI, Uvicorn, SQLAlchemy, Pydantic, etc.) at the time of project creation. Use `pip list --outdated` or check the official package repositories to ensure you're using the most recent stable releases with security patches and bug fixes.

### Database
- **SQLAlchemy** 2.0+: ORM with async support ready
- **Alembic**: Database migrations
- **MySQL** 8.4+: Database (PostgreSQL support via configuration)

### Authentication & Security
- **PyJWT**: JWT token handling
- **passlib[argon2]**: Password hashing (Argon2 algorithm)
- **python-multipart**: File uploads support

### Validation & Serialization
- **Pydantic** 2.x: Data validation and settings management
- **pydantic-settings**: Type-safe configuration management

### Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client for testing
- **faker**: Test data generation

### Development & DevOps
- **Docker & Docker Compose**: Containerization
- **GitHub Actions**: CI/CD pipelines
- **debugpy**: Remote debugging support

### Optional (Can be added later)
- **Redis**: Caching and session storage
- **Celery**: Background job queue
- **Prometheus**: Metrics collection
- **Sentry**: Error tracking

---

## Configuration Management

### Pydantic Settings Pattern

**File: `app/core/config.py`**

Use `pydantic-settings` for type-safe, validated configuration with environment variable support.

> **✅ Environment Variable Support**: Pydantic Settings automatically reads from:
> - Environment variables (highest priority)
> - `.env` files (loaded automatically)
> - Default values in the class (lowest priority)
> 
> This means all configuration can be set via Docker Compose environment variables or `.env` files. The values in the class definition are just defaults/fallbacks. The `SettingsConfigDict` with `env_file=".env"` ensures that environment variables from Docker Compose, `.env` files, or system environment will override the defaults.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation and type safety."""
    
    # API Configuration
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "FastAPI Template"
    API_DESCRIPTION: str = "Production-ready FastAPI template"
    API_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 2
    
    # Database Configuration
    DB_HOST: str  # Can be set via env var or .env file
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    
        # Migration Control (optional)
    SKIP_MIGRATIONS: bool = False  # Set to true to disable auto-migrations in entrypoint
    
    # JWT Configuration
    JWT_SECRET_KEY: str  # Required, no default
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    TRUSTED_PROXIES: List[str] = ["127.0.0.1", "localhost"]
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: str = "/app/logs/app.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # OpenAPI Documentation
    ENABLE_OPENAPI_DOCS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Admin User (for initial setup)
    ADMIN_USERNAME: str  # Required
    ADMIN_PASSWORD: str  # Required
    
    # Feature Flags
    FEATURE_CACHE_ENABLED: bool = False
    
    # Metrics Configuration
    ENABLE_METRICS: bool = False  # Enable Prometheus metrics endpoint
    METRICS_PATH: str = "/metrics"  # Path for metrics endpoint
    METRICS_INCLUDE_SYSTEM: bool = False  # Include system metrics (CPU, memory)
    METRICS_INCLUDE_DB: bool = False  # Include database connection metrics
    
    # Sentry Configuration (optional)
    SENTRY_DSN: Optional[str] = None  # Sentry DSN for error tracking
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Global settings instance
settings = get_settings()
```

### Environment Variables

**File: `.env.example`**

```bash
# Environment
ENVIRONMENT=development
DEBUG=false

# API Configuration
API_VERSION=1.0.0
API_TITLE=FastAPI Template
API_DESCRIPTION=Production-ready FastAPI template

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=api_user
DB_PASSWORD=secure_password
DB_NAME=api_db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Security
ALLOWED_HOSTS=*
TRUSTED_PROXIES=127.0.0.1,localhost

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# OpenAPI
ENABLE_OPENAPI_DOCS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me-in-production

# Migration Control (optional)
# SKIP_MIGRATIONS=false  # Set to true to disable automatic migrations (run manually instead)

# Metrics (optional)
ENABLE_METRICS=false
METRICS_PATH=/metrics
METRICS_INCLUDE_SYSTEM=false
METRICS_INCLUDE_DB=false

# Sentry (optional)
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

---

## Database Setup

### Database Initialization and Migrations

#### Migration Strategy: Pure Migration 0 (Industry Standard)

The template uses **pure Alembic migrations** with no SQL schema files. This is the industry standard approach used by Django, Rails, Laravel, and most modern frameworks.

**Key Principles**:
- **Single source of truth**: All schema changes are in migration files
- **Complete history**: Every database change is tracked in version control
- **Model-driven**: Initial migration is generated from SQLAlchemy models using `alembic revision --autogenerate`
- **No SQL files**: No separate `schema.sql` file to maintain or keep in sync

#### How Migrations Work

**Fresh Deployment (New Database)**:
1. Container starts and waits for database to be ready
2. Alembic is initialized (if not already done)
3. All migrations are run sequentially: `alembic upgrade head`
   - Migration 0 creates all initial tables
   - Subsequent migrations apply incremental changes
4. Application starts

**Existing Deployment (Database with Data)**:
1. Container starts and waits for database to be ready
2. Alembic checks current database version (stored in `alembic_version` table)
3. Only new migrations (not yet applied) are run
4. Application starts

**Alembic Idempotency**:
- Alembic tracks which migrations have been applied
- Running `alembic upgrade head` multiple times is safe
- Already-applied migrations are skipped automatically

#### Recommended Approach: Automatic Migrations

**The template uses automatic migrations as the default and recommended approach.**

This means migrations run automatically when the container starts, before the application begins serving requests. This approach is:

✅ **Simple**: No additional deployment steps required  
✅ **Safe**: Alembic handles idempotency automatically  
✅ **Practical**: Works well for small to medium servers with a handful of clients  
✅ **Tested**: Can test migrations on staging/test instances before production (using manual GitHub Actions workflow)

**How it works**:
- Migrations run in `docker-entrypoint.sh` before starting the application
- If migrations fail, the container fails to start (fail-fast)
- This prevents the app from running with an incompatible database schema

**Best Practices for Automatic Migrations**:
1. **Test first**: Use the manual GitHub Actions workflow to test migrations on a staging instance
2. **Review migrations**: Always review generated migrations before committing
3. **Backup before production**: Take database backups before deploying migrations to production
4. **Monitor startup**: Watch container logs during deployment to catch migration issues early

#### Alternative Approach: Manual Migrations (Extra Safety)

For teams that want **maximum safety and control**, you can disable automatic migrations and run them manually:

**When to consider manual migrations**:
- Large-scale production systems with many clients
- Strict compliance/audit requirements
- Complex migrations that need careful coordination
- Multi-database environments requiring coordination

**How to use manual migrations**:
1. Set `SKIP_MIGRATIONS=true` in your environment variables
2. Run migrations as a separate step in your CI/CD pipeline before deploying containers
3. Use a dedicated migration job/container with limited permissions
4. Verify migrations succeed before deploying application containers

**Benefits of manual migrations**:
- **Security**: App container doesn't need migration permissions
- **Control**: Review and approve migrations before applying
- **Rollback**: Easier to rollback if migration fails
- **Audit**: Clear separation of deployment steps

**Note**: For small servers with a handful of clients, automatic migrations are usually sufficient and more practical. Manual migrations are an "extra mile" approach that may be overkill for simpler deployments.

### Database Connection

**File: `app/core/database.py`**

```python
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=10,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Connection event listeners for logging
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set connection-level settings if needed."""
    pass

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout."""
    if settings.DEBUG:
        logger.debug("Database connection checked out")

def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints.
    
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions (for use outside FastAPI).
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### Base Model

**File: `app/models/base.py`**

```python
from sqlalchemy import Column, Integer, TIMESTAMP, Boolean, text
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Any

from app.core.database import Base

class BaseModel(Base):
    """Base model with common fields for all entities."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )
    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        index=True
    )
    
    def soft_delete(self):
        """Mark entity as deleted (soft delete)."""
        self.is_deleted = True
    
    def restore(self):
        """Restore soft-deleted entity."""
        self.is_deleted = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

### Creating Migrations

#### Initial Migration (Migration 0)

The template should include a minimal initial migration as an example. When developers fork this template, they should generate their own initial migration from their SQLAlchemy models.

**To create the initial migration from your models**:

```bash
# 1. Ensure all your models are imported in migrations/env.py
#    (The template already does this with `from app.models import *`)

# 2. Generate the initial migration
alembic revision --autogenerate -m "initial"

# 3. Review the generated migration file in migrations/versions/
#    Alembic is good but not perfect - you may need to adjust:
#    - Missing indexes
#    - Custom constraints
#    - Data migrations (if needed)

# 4. Test the migration on a fresh database
alembic upgrade head

# 5. Verify the schema matches your models
#    Check that all tables, columns, indexes, and constraints are correct
```

**Example Initial Migration** (what Alembic generates):

```python
"""Initial schema

Revision ID: 000_initial
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '000_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Example: Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), 
                  nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), 
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), 
                  nullable=False),
        sa.Column('is_deleted', sa.Boolean(), 
                  server_default=sa.text('0'), 
                  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_is_deleted', 'users', ['is_deleted'])

def downgrade() -> None:
    op.drop_index('idx_users_is_deleted', table_name='users')
    op.drop_table('users')
```

#### Subsequent Migrations

After you've added or modified models, create new migrations:

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "add_user_table"

# Review the migration carefully
# - Check that it captures all your changes
# - Verify it won't cause data loss
# - Add any data migrations if needed (e.g., backfilling new columns)

# Test the migration
alembic upgrade head

# If you need to rollback (development only!)
alembic downgrade -1  # Go back one migration
```

**Important Notes**:
- Always review auto-generated migrations before committing
- Test migrations on a copy of production data if possible
- Never modify migrations that have already been applied to production
- Use the manual GitHub Actions workflow to test migrations on staging first

### Alembic Configuration

**File: `alembic.ini.template`**

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**File: `migrations/env.py.template`**

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import Base
from app.core.config import settings

# Import all models so Alembic can detect them
from app.models import *  # noqa

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## Application Architecture

### Main Application

**File: `app/main.py`**

```python
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.core.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware
)
from app.core.exceptions import (
    setup_exception_handlers,
    HTTPException,
    ValidationException,
    DatabaseException
)
from app.api.api import api_router
from app.core.logging import setup_logging

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.API_VERSION}")
    
    # Note: Database tables are created by Alembic migrations in docker-entrypoint.sh
    # Do NOT use Base.metadata.create_all() - always use migrations
    
    # Initialize default admin user
    try:
        from app.core.admin_init import initialize_default_admin
        initialize_default_admin()
    except Exception as e:
        logger.error(f"Failed to initialize admin: {e}")
        if settings.is_production:
            raise  # Fail fast in production
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs" if settings.ENABLE_OPENAPI_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_OPENAPI_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_OPENAPI_DOCS else None,
    lifespan=lifespan
)

# Add middleware (order matters!)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)

# Root endpoint
# Security Note: This endpoint is intentionally minimal to reduce information disclosure.
# It only returns a basic status without revealing version, environment, or other details
# that could be used for fingerprinting or targeted attacks.
@app.get("/")
async def root():
    """
    Root endpoint - minimal health check.
    
    Returns only a basic status to confirm the service is running.
    For detailed health checks, use /api/v1/health/ endpoints instead.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS if settings.is_production else 1,
        reload=settings.is_development,
        log_config="logging.ini"
    )
```

### API Router

**File: `app/api/api.py`**

```python
from fastapi import APIRouter

from app.api.endpoints import health, version

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)
api_router.include_router(
    version.router,
    prefix="/version",
    tags=["version"]
)
```

### Minimal Endpoint Example

**File: `app/api/endpoints/version.py`**

```python
from fastapi import APIRouter, Depends
from app.core.config import settings
from app.schemas.version import VersionResponse

router = APIRouter()

@router.get(
    "/",
    response_model=VersionResponse,
    summary="Get API version",
    description="Returns the current API version and build information",
    responses={
        200: {
            "description": "Version information",
            "content": {
                "application/json": {
                    "example": {
                        "version": "1.0.0",
                        "build_date": "2024-01-15T10:30:00Z",
                        "environment": "production"
                    }
                }
            }
        }
    }
)
async def get_version():
    """
    Get API version information.
    
    This is a minimal example endpoint demonstrating the template structure.
    """
    from datetime import datetime
    
    return VersionResponse(
        version=settings.API_VERSION,
        build_date=datetime.utcnow().isoformat() + "Z",
        environment=settings.ENVIRONMENT
    )
```

**File: `app/schemas/version.py`**

```python
from pydantic import BaseModel, Field
from datetime import datetime

class VersionResponse(BaseModel):
    """API version response schema."""
    
    version: str = Field(..., description="API version number")
    build_date: str = Field(..., description="Build timestamp (ISO 8601)")
    environment: str = Field(..., description="Current environment")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "version": "1.0.0",
                "build_date": "2024-01-15T10:30:00Z",
                "environment": "production"
            }
        }
    }
```

---

## Authentication & Authorization

### Security Utilities

**File: `app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings

# Password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash using Argon2."""
    return pwd_context.hash(password)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def is_token_expired(token: str) -> bool:
    """Check if token is expired."""
    try:
        payload = verify_token(token)
        exp = payload.get("exp")
        if exp is None:
            return True
        return datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc)
    except HTTPException:
        return True
```

### Authentication Dependencies

**File: `app/api/dependencies.py`**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token
from app.models.admin import Admin  # Example model

# Security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """
    Get current authenticated user from JWT token.
    
    This is a template - replace Admin with your actual user model.
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(Admin).filter(Admin.id == int(user_id)).first()
    if not user or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Optional: Role-based access control
async def require_role(required_role: str):
    """Dependency factory for role-based access control."""
    async def role_checker(
        current_user: Admin = Depends(get_current_user)
    ) -> Admin:
        # Implement role checking logic
        # if current_user.role != required_role:
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
```

---

## Error Handling

### Custom Exceptions

**File: `app/core/exceptions.py`**

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback

logger = logging.getLogger(__name__)

class BaseAPIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = None,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}

class ValidationException(BaseAPIException):
    """Validation error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )

class NotFoundException(BaseAPIException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )

class DatabaseException(BaseAPIException):
    """Database operation exception."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR"
        )

class AuthenticationException(BaseAPIException):
    """Authentication exception."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationException(BaseAPIException):
    """Authorization exception."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )

# Exception handlers
async def base_exception_handler(request: Request, exc: BaseAPIException):
    """Handle base API exceptions."""
    logger.error(
        f"API Error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={"errors": errors}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors}
            }
        }
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database exceptions."""
    logger.error(
        f"Database error on {request.method} {request.url.path}",
        exc_info=True,
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred"
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"Unexpected error on {request.method} {request.url.path}",
        exc_info=True,
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )

def setup_exception_handlers(app):
    """Register all exception handlers."""
    app.add_exception_handler(BaseAPIException, base_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
```

### Error Handling Middleware

**File: `app/core/middleware.py`**

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import uuid

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "error": str(e)
                }
            )
            raise

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Catch and format unhandled exceptions."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled exception: {e}",
                exc_info=True,
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "path": request.url.path,
                    "method": request.method
                }
            )
            raise
```

---

## Logging

### Structured Logging Setup

**File: `app/core/logging.py`**

```python
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "process_time"):
            log_data["process_time"] = record.process_time
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logs."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

def setup_logging():
    """Configure application logging."""
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Choose formatter
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # File handler (if log file is configured)
    handlers = [console_handler]
    
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
```

**File: `logging.ini`**

```ini
[loggers]
keys=root,uvicorn,uvicorn_error,uvicorn_access

[handlers]
keys=console,file

[formatters]
keys=standard,json

[logger_root]
level=INFO
handlers=console,file

[logger_uvicorn]
level=INFO
handlers=console,file
qualname=uvicorn
propagate=0

[logger_uvicorn_error]
level=INFO
handlers=console,file
qualname=uvicorn.error
propagate=0

[logger_uvicorn_access]
level=INFO
handlers=console,file
qualname=uvicorn.access
propagate=0

[handler_console]
class=StreamHandler
level=DEBUG
formatter=standard
args=(sys.stdout,)

[handler_file]
class=logging.handlers.RotatingFileHandler
level=DEBUG
formatter=standard
args=('/app/logs/app.log', 'a', 10485760, 5)

[formatter_standard]
format=%(asctime)s [%(levelname)s] %(name)s: %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[formatter_json]
format={"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}
datefmt=%Y-%m-%dT%H:%M:%S
```

---

## API Design Patterns

### Base Service Class

**File: `app/services/base.py`**

```python
from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
import logging

from app.core.database import Base
from app.core.exceptions import DatabaseException, NotFoundException

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = logging.getLogger(__name__)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service class with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], model_name: str):
        """
        Initialize base service.
        
        Args:
            model: SQLAlchemy model class
            model_name: Human-readable name for error messages
        """
        self.model = model
        self.model_name = model_name
    
    def get_by_id(
        self,
        db: Session,
        entity_id: int,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get entity by ID.
        
        Args:
            db: Database session
            entity_id: Entity ID
            include_deleted: Include soft-deleted entities
            
        Returns:
            Entity if found, None otherwise
        """
        self._validate_id(entity_id)
        
        query = db.query(self.model).filter(self.model.id == entity_id)
        
        if not include_deleted and hasattr(self.model, "is_deleted"):
            query = query.filter(self.model.is_deleted == False)
        
        return query.first()
    
    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        Get all entities with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Include soft-deleted entities
            
        Returns:
            List of entities
        """
        query = db.query(self.model)
        
        if not include_deleted and hasattr(self.model, "is_deleted"):
            query = query.filter(self.model.is_deleted == False)
        
        return query.offset(skip).limit(limit).all()
    
    def create(
        self,
        db: Session,
        obj_in: CreateSchemaType
    ) -> ModelType:
        """
        Create new entity.
        
        Args:
            db: Database session
            obj_in: Creation schema
            
        Returns:
            Created entity
            
        Raises:
            DatabaseException: If database operation fails
        """
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(obj_in, "model_dump"):
                obj_data = obj_in.model_dump()
            elif hasattr(obj_in, "dict"):
                obj_data = obj_in.dict()
            else:
                obj_data = obj_in
            
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating {self.model_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create {self.model_name}: integrity constraint violation"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating {self.model_name}: {e}")
            raise DatabaseException(f"Failed to create {self.model_name}")
    
    def update(
        self,
        db: Session,
        entity_id: int,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """
        Update entity.
        
        Args:
            db: Database session
            entity_id: Entity ID
            obj_in: Update schema
            
        Returns:
            Updated entity
            
        Raises:
            NotFoundException: If entity not found
            DatabaseException: If database operation fails
        """
        db_obj = self.get_by_id(db, entity_id)
        if not db_obj:
            raise NotFoundException(self.model_name, str(entity_id))
        
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, "dict"):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in
            
            # Update fields
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating {self.model_name}: {e}")
            raise DatabaseException(f"Failed to update {self.model_name}")
    
    def delete(
        self,
        db: Session,
        entity_id: int,
        hard: bool = False
    ) -> bool:
        """
        Delete entity (soft delete by default).
        
        Args:
            db: Database session
            entity_id: Entity ID
            hard: If True, perform hard delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseException: If database operation fails
        """
        db_obj = self.get_by_id(db, entity_id)
        if not db_obj:
            return False
        
        try:
            if hard:
                db.delete(db_obj)
            elif hasattr(db_obj, "soft_delete"):
                db_obj.soft_delete()
            else:
                db.delete(db_obj)
            
            db.commit()
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error deleting {self.model_name}: {e}")
            raise DatabaseException(f"Failed to delete {self.model_name}")
    
    def _validate_id(self, entity_id: int):
        """Validate entity ID."""
        if entity_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid {self.model_name} ID: must be positive"
            )
```

### Usage Example

**File: `app/services/version.py`**

```python
from app.services.base import BaseService
from app.schemas.version import VersionResponse
from app.core.config import settings

class VersionService(BaseService):
    """Service for version information."""
    
    def get_version_info(self) -> VersionResponse:
        """Get current version information."""
        from datetime import datetime
        
        return VersionResponse(
            version=settings.API_VERSION,
            build_date=datetime.utcnow().isoformat() + "Z",
            environment=settings.ENVIRONMENT
        )

version_service = VersionService(None, "Version")  # No model needed for this example
```

---

## Testing Framework

### Pytest Configuration

**File: `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### Test Fixtures

**File: `tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Test database (SQLite in-memory for speed)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for tests."""
    # Create test admin user and get token
    # This is a template - implement based on your auth setup
    login_data = {
        "username": "test_admin",
        "password": "test_password"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Base Test Utilities

**File: `tests/integration/test_utils.py`**

```python
import os
import requests
from typing import Optional, Tuple, Any
from integration.test_auth_utils import auth_utils

class EntityTestUtils:
    """Base utility class for testing entity CRUD operations."""
    
    def __init__(self, entity_name: str, endpoint_path: str):
        """
        Initialize test utilities.
        
        Args:
            entity_name: Display name for error messages
            endpoint_path: API endpoint path (e.g., "users")
        """
        self.entity_name = entity_name
        self.endpoint_path = endpoint_path
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.base_url = f"{self.api_base_url}/api/v1/{endpoint_path}"
    
    def create_entity(self, data: dict) -> Tuple[dict, int]:
        """
        Create a new entity.
        
        Args:
            data: Entity data
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json=data
        )
        
        assert response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Status: {response.status_code}, Response: {response.text}"
        )
        
        entity = response.json()
        return entity, entity["id"]
    
    def get_entity(self, entity_id: int, expected_status: int = 200) -> Optional[dict]:
        """Get entity by ID."""
        response = requests.get(f"{self.base_url}/{entity_id}")
        assert response.status_code == expected_status
        return response.json() if expected_status == 200 else None
    
    def update_entity(self, entity_id: int, data: dict) -> dict:
        """Update entity."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "PUT",
            f"{self.base_url}/{entity_id}",
            json=data
        )
        assert response.status_code == 200
        return response.json()
    
    def delete_entity(self, entity_id: int):
        """Delete entity."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/{entity_id}"
        )
        assert response.status_code == 204
    
    def test_crud_workflow(self, create_data: dict, update_data: dict):
        """Test full CRUD workflow."""
        # Create
        entity, entity_id = self.create_entity(create_data)
        
        # Read
        retrieved = self.get_entity(entity_id)
        assert retrieved == entity
        
        # Update
        updated = self.update_entity(entity_id, update_data)
        assert updated["id"] == entity_id
        
        # Delete
        self.delete_entity(entity_id)
        
        # Verify deletion
        self.get_entity(entity_id, expected_status=404)
```

**File: `tests/integration/test_auth_utils.py`**

```python
import os
import requests
from typing import Optional

class AuthUtils:
    """Authentication utilities for tests."""
    
    def __init__(self):
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def login(self, username: str = None, password: str = None):
        """Login and store tokens."""
        username = username or os.environ.get("TEST_ADMIN_USERNAME", "admin")
        password = password or os.environ.get("TEST_ADMIN_PASSWORD", "admin")
        
        response = requests.post(
            f"{self.api_base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
    
    def make_authenticated_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """Make authenticated request."""
        if not self.access_token:
            self.login()
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers
        
        return requests.request(method, url, **kwargs)

auth_utils = AuthUtils()
```

### Example Test

**File: `tests/integration/test_version.py`**

```python
import pytest
from fastapi.testclient import TestClient

def test_get_version(client: TestClient):
    """Test version endpoint."""
    response = client.get("/api/v1/version/")
    assert response.status_code == 200
    
    data = response.json()
    assert "version" in data
    assert "build_date" in data
    assert "environment" in data
    assert data["version"] == "1.0.0"

def test_version_response_format(client: TestClient):
    """Test version response format."""
    response = client.get("/api/v1/version/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data["version"], str)
    assert isinstance(data["build_date"], str)
    assert isinstance(data["environment"], str)
```

---

## Docker & Containerization

### Production Dockerfile

**File: `docker/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads

# Use entrypoint script
ENTRYPOINT ["./docker/docker-entrypoint.sh"]

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1
```

### Docker Entrypoint

**File: `docker/docker-entrypoint.sh`**

```bash
#!/bin/bash
set -e

echo "Starting FastAPI application..."

# Function to wait for database
wait_for_db() {
    echo "Waiting for database to be ready..."
    while ! python -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='${DB_HOST}',
        port=${DB_PORT},
        user='${DB_USER}',
        password='${DB_PASSWORD}',
        database='${DB_NAME}'
    )
    conn.close()
    print('Database is ready!')
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
"; do
        echo "Database not ready, waiting 5 seconds..."
        sleep 5
    done
}

# Function to initialize Alembic
init_alembic() {
    if [ ! -f "alembic.ini" ]; then
        echo "Initializing Alembic..."
        cp alembic.ini.template alembic.ini
        sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}|" alembic.ini
    fi
}

# Function to configure Alembic
configure_alembic() {
    echo "Configuring Alembic environment..."
    cp migrations/env.py.template migrations/env.py
}

# Function to run migrations
run_migrations() {
    if [ "${SKIP_MIGRATIONS}" = "true" ]; then
        echo "Skipping migrations (SKIP_MIGRATIONS=true)"
        return
    fi
    
    echo "Running database migrations..."
    
    # Alembic is idempotent - it will only run new migrations
    # For fresh databases, all migrations run
    # For existing databases, only new migrations are applied
    alembic upgrade head
    echo "Migrations completed successfully"
}

# Main execution
echo "Environment: ${ENVIRONMENT:-development}"
echo "Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Wait for database
wait_for_db

# Initialize Alembic if needed
init_alembic

# Configure Alembic
configure_alembic

# Run migrations (unless SKIP_MIGRATIONS is set)
run_migrations

# Start application
echo "Starting FastAPI application with ${WORKERS:-2} workers..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${WORKERS:-2} \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --log-config logging.ini
```

### Docker Compose

**File: `docker-compose.yml`**

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: fastapi_template_api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS:-*}
      - ENABLE_OPENAPI_DOCS=${ENABLE_OPENAPI_DOCS:-false}
      - SKIP_MIGRATIONS=${SKIP_MIGRATIONS:-false}  # Set to true to disable auto-migrations
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - backend
      - frontend

  db:
    image: mysql:8.4
    container_name: fastapi_template_db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${DB_NAME}
      - MYSQL_USER=${DB_USER}
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 5s
      retries: 10
      start_period: 30s
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  mysql_data:
    driver: local
```

### Test Docker Compose

**File: `docker-compose.test.yml`**

```yaml
version: '3.8'

services:
  api-test:
    build:
      context: .
      dockerfile: docker/Dockerfile.test
    environment:
      - ENVIRONMENT=test
      - DB_HOST=db-test
      - DB_PORT=3306
      - DB_USER=test_user
      - DB_PASSWORD=test_password
      - DB_NAME=test_db
      - JWT_SECRET_KEY=test-secret-key
      - ADMIN_USERNAME=test_admin
      - ADMIN_PASSWORD=test_password
    depends_on:
      - db-test
    volumes:
      - .:/app
    command: pytest tests/ -v

  db-test:
    image: mysql:8.4
    environment:
      - MYSQL_ROOT_PASSWORD=test_root_password
      - MYSQL_DATABASE=test_db
      - MYSQL_USER=test_user
      - MYSQL_PASSWORD=test_password
    volumes:
      - test_mysql_data:/var/lib/mysql

volumes:
  test_mysql_data:
```

---

## CI/CD Pipeline

The CI/CD pipeline consists of two workflows:

1. **Automated Pipeline** (`api-tests.yml`): Runs tests and builds Docker images automatically on push/PR
2. **Manual Pipeline** (`docker-build-manual.yml`): Allows developers to manually trigger builds from any branch

### Workflow Dependencies

The automated pipeline ensures that:
- **Tests must pass before Docker build**: The build job depends on the test job
- **Build only runs on success**: Docker image is only built and pushed if all tests pass
- **Proper error handling**: Failed tests prevent deployment

### GitHub Actions - Automated Tests and Build

**File: `.github/workflows/api-tests.yml`**

This workflow runs automatically on push to `main`/`develop` or on pull requests. It runs tests first, and only builds/pushes Docker images if tests pass.

```yaml
name: API Tests and Docker Build

on:
  push:
    branches: [ main, develop ]
    paths-ignore:
      - '**/*.md'
      - 'docs/**'
      - 'README*'
      - 'LICENSE*'
      - '.github/*.md'
  pull_request:
    branches: [ main, develop ]
    paths-ignore:
      - '**/*.md'
      - 'docs/**'
      - 'README*'
      - 'LICENSE*'
      - '.github/*.md'

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Job 1: Run tests
  run-api-tests:
    runs-on: ubuntu-latest
    
    services:
      docker:
        image: docker:dind
        options: --privileged
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker and Docker Compose
        run: |
          sudo apt-get update
          sudo apt-get install -y docker-compose
      
      - name: Set up QEMU for multi-arch
        uses: docker/setup-qemu-action@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Set up environment
        run: |
          mkdir -p test-reports
          chmod 777 test-reports
      
      - name: Run API Integration Tests
        run: |
          chmod +x ./run_api_integration_tests.sh
          ./run_api_integration_tests.sh
      
      - name: Upload test reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: api-test-reports
          path: test-reports/
  
  # Job 2: Build and push Docker image (only if tests pass)
  build-and-push:
    needs: run-api-tests  # ⚠️ CRITICAL: This ensures tests run first
    if: success()  # Only run if tests passed
    runs-on: ubuntu-latest
    
    services:
      docker:
        image: docker:dind
        options: --privileged
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up QEMU for multi-arch
        uses: docker/setup-qemu-action@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract app version
        id: version
        run: |
          API_VERSION=$(grep -o 'API_VERSION = "[^"]*"' app/core/config.py | cut -d'"' -f2)
          echo "version=$API_VERSION" >> $GITHUB_OUTPUT
          echo "API version: $API_VERSION"
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,format=short,prefix={{branch}}-,enable={{is_default_branch}}
            type=raw,value=latest,enable={{is_default_branch}}
            type=raw,value={{date 'YYYY-MM-DD-HH-mm'}},enable={{is_default_branch}}
            type=raw,value=${{ steps.version.outputs.version }},enable={{is_default_branch}}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          platforms: linux/amd64,linux/arm64
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Cleanup old images
        if: github.ref == 'refs/heads/main'
        run: |
          # Keep only the 5 most recent images (excluding latest and current version)
          # Implementation depends on your registry setup
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitHub Actions - Manual Build

**File: `.github/workflows/docker-build-manual.yml`**

This workflow allows developers to manually trigger a build from any branch. This is extremely useful for:
- Testing features in separate branches
- Building images for staging/test environments
- Debugging build issues
- Building from feature branches before merging

```yaml
name: Manual API Tests and Docker Build

on:
  workflow_dispatch: {}  # Manual trigger only

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  manual-build:
    runs-on: ubuntu-latest
    
    services:
      docker:
        image: docker:dind
        options: --privileged
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker and Docker Compose
        run: |
          sudo apt-get update
          sudo apt-get install -y docker-compose
      
      - name: Set up QEMU for multi-arch
        uses: docker/setup-qemu-action@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        with:
          install: true
      
      - name: Create Builder Instance
        run: |
          docker buildx create --use --name mybuilder
      
      - name: Set up environment
        run: |
          mkdir -p test-reports
          chmod 777 test-reports
      
      - name: Run API Integration Tests
        run: |
          chmod +x ./run_api_integration_tests.sh
          ./run_api_integration_tests.sh
      
      - name: Upload test reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: api-test-reports
          path: test-reports/
      
      - name: Login to GitHub Container Registry
        if: success()  # Only login if tests passed
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        if: success()
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=raw,value=manual
            type=raw,value={{date 'YYYY-MM-DD-HH-mm'}}
            type=sha,prefix=manual-
            type=ref,event=branch  # Include branch name in tag
      
      - name: Build and push Docker image (manual)
        if: success()  # Only build if tests passed
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          platforms: linux/amd64,linux/arm64
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**How to use the manual workflow**:
1. Push your changes to any branch (feature branch, develop, etc.)
2. Go to GitHub Actions tab in the repository
3. Select "Manual API Tests and Docker Build" workflow
4. Click "Run workflow"
5. Select the branch you want to build from
6. Click "Run workflow" button
7. The workflow will run tests and build the Docker image if tests pass

**Manual build tags**:
- `manual` - Always tagged for manual builds
- `manual-<sha>` - Includes commit SHA
- `YYYY-MM-DD-HH-mm` - Timestamp
- Branch name - If building from a branch

---

## Security Best Practices

### Rate Limiting

**File: `app/core/rate_limit.py`**

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import time

from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        client_ip = request.client.host
        now = time.time()
        
        # Clean old entries
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if now - timestamp < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(self.clients[client_ip])
        )
        
        return response
```

### Input Sanitization

**File: `app/utils/validators.py`**

```python
import re
from typing import Any
from html import escape

def sanitize_string(value: str, max_length: int = None) -> str:
    """Sanitize string input."""
    # Remove null bytes
    value = value.replace("\x00", "")
    
    # Trim whitespace
    value = value.strip()
    
    # HTML escape
    value = escape(value)
    
    # Length check
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))
```

---

## Code Organization Patterns

### Constants

**File: `app/core/constants.py`**

```python
# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File Uploads
MAX_FILE_SIZE_MB = 25
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

# Cache
CACHE_TTL_SECONDS = 300  # 5 minutes

# Rate Limiting
DEFAULT_RATE_LIMIT = 60  # requests per minute
```

### Health Check Endpoints

**File: `app/api/endpoints/health.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": settings.API_VERSION
    }

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check with database connectivity."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e)
        }, 503

@router.get("/live")
async def liveness_check():
    """Liveness check."""
    return {"status": "alive"}
```

---

## Development Workflow

### Setup Script

**File: `setup_env.sh`**

```bash
#!/bin/bash

echo "Setting up environment..."

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
    echo "Please edit .env with your configuration"
else
    echo ".env file already exists"
fi

# Generate JWT secret if not set
if ! grep -q "JWT_SECRET_KEY=" .env || grep -q "JWT_SECRET_KEY=$" .env; then
    SECRET=$(openssl rand -hex 32)
    if grep -q "JWT_SECRET_KEY=" .env; then
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$SECRET/" .env
    else
        echo "JWT_SECRET_KEY=$SECRET" >> .env
    fi
    echo "Generated JWT_SECRET_KEY"
fi

echo "Environment setup complete!"
```

### Requirements Files

**File: `requirements.txt`**

```
fastapi==0.115.14
uvicorn[standard]==0.35.0
pydantic==2.11.7
pydantic-settings==2.6.1
sqlalchemy==2.0.41
alembic==1.16.5
mysql-connector-python==9.3.0
PyMySQL==1.1.2
python-multipart==0.0.20
PyJWT==2.10.1
passlib[argon2]==1.7.4
prometheus-client==0.21.0  # Prometheus metrics (optional, enable via ENABLE_METRICS)
```

**File: `requirements-test.txt`**

```
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.27.2
faker==33.1.0
```

---

## Convenience Scripts

The template includes several convenience scripts to streamline common development and deployment tasks. These scripts automate repetitive operations and reduce the chance of errors.

### Integration Test Runner

**File: `scripts/run_api_integration_tests.sh`**

This script automates the entire integration test workflow, handling container lifecycle, database setup, and test execution.

**Features**:
- Automatically cleans up existing test containers
- Builds test containers
- Starts MySQL and waits for it to be ready
- Starts API server
- Runs integration tests
- Optionally keeps containers running for inspection
- Reports test results location

**Usage**:
```bash
# Run tests (default: cleans up containers after)
./scripts/run_api_integration_tests.sh

# Keep containers running for inspection
./scripts/run_api_integration_tests.sh --keep-containers
```

**Full Script**:

```bash
#!/bin/bash

# Set default values
REPORT_DIR="./test-reports/integration"
KEEP_CONTAINERS=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --keep-containers)
      KEEP_CONTAINERS=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Make sure the report directory exists
mkdir -p "$REPORT_DIR"

# Stop and remove any existing containers
echo "🧹 Cleaning up any existing test containers..."
docker compose -f docker-compose.test.yml --env-file .env.test down -v --remove-orphans

# Build and start the test containers
echo "🏗️ Building test containers..."
docker compose -f docker-compose.test.yml --env-file .env.test build

# Start the MySQL service
echo "🚀 Starting MySQL test environment..."
docker compose -f docker-compose.test.yml --env-file .env.test up -d mysql_test

echo "⏳ Waiting for MySQL to be ready..."
# Display a countdown
TOTAL_WAIT=15
for (( i=$TOTAL_WAIT; i>=1; i-- ))
do
  echo -ne "\r⌛ MySQL starting... Should be ready in about $i seconds"
  sleep 1
done
echo -ne "\r✅ MySQL should be ready now!                         \n"

# Start the API service
echo "🚀 Starting API test environment..."
docker compose -f docker-compose.test.yml --env-file .env.test up -d api_server_test

# Wait for API server to be ready
echo "⏳ Waiting for API server to be ready..."
sleep 2

# Run the tests
echo "🧪 Running API integration tests..."
docker compose -f docker-compose.test.yml --env-file .env.test run --rm api_integration_tests
TEST_EXIT_CODE=$?

# Clean up containers unless --keep-containers is specified
if [ "$KEEP_CONTAINERS" = false ]; then
  echo "🧹 Cleaning up test containers..."
  docker compose -f docker-compose.test.yml --env-file .env.test down -v
else
  echo "🔍 Containers kept running for inspection"
fi

# Show location of test reports
echo "📊 Test reports available in ${REPORT_DIR}"

# Show information about the JSON report
if [ -f "${REPORT_DIR}/integration_test_report.json" ]; then
  echo "📄 JSON test report generated: ${REPORT_DIR}/integration_test_report.json"
fi

# Exit with the test exit code
exit $TEST_EXIT_CODE
```

### Production Rollback Script

**File: `scripts/rollback.sh`**

This script facilitates safe production rollbacks by pulling and deploying previous Docker image versions.

**Features**:
- Lists available versions from container registry
- Rolls back to specific version (by tag, timestamp, or commit SHA)
- Rolls back to latest or previous version
- Verifies deployment health after rollback
- Color-coded output for better readability
- Integrates with GitHub Container Registry (via GitHub CLI)

**Usage**:
```bash
# List available versions
./scripts/rollback.sh
./scripts/rollback.sh --list

# Rollback to specific version
./scripts/rollback.sh master-abc123
./scripts/rollback.sh 2024-01-15-14-30

# Rollback to latest or previous
./scripts/rollback.sh --latest
./scripts/rollback.sh --previous

# Show help
./scripts/rollback.sh --help
```

**Full Script**:

```bash
#!/bin/bash

# Production Rollback Script for Backend API
# Usage: ./scripts/rollback.sh [TAG] [OPTIONS]

set -e

# Configuration
REGISTRY="ghcr.io"
REPOSITORY="your-org/your-repo"  # Update with your registry and repository
IMAGE_NAME="$REGISTRY/$REPOSITORY"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "Production Rollback Script for Backend API"
    echo ""
    echo "Usage: $0 [TAG] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  TAG                 Specific tag to rollback to (commit SHA, timestamp, etc.)"
    echo ""
    echo "Options:"
    echo "  --latest           Rollback to latest version"
    echo "  --previous         Rollback to previous version"
    echo "  --list             List available versions"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # List available versions"
    echo "  $0 master-abc123             # Rollback to specific commit"
    echo "  $0 2024-01-15-14-30          # Rollback to specific timestamp"
    echo "  $0 --latest                  # Rollback to latest version"
    echo "  $0 --previous                # Rollback to previous version"
    echo ""
    echo "Note: This script requires GitHub CLI (gh) to be installed and authenticated."
    echo "      Run 'gh auth login' if you haven't already."
}

list_available_versions() {
    log_info "Fetching available image versions..."
    
    # Get available tags from GitHub Container Registry
    if command -v gh >/dev/null 2>&1; then
        PACKAGES=$(gh api "/user/packages?package_type=container" --jq '.[].name' 2>/dev/null || echo "")
        
        if [ -n "$PACKAGES" ]; then
            # Find the package that matches our repository name
            PACKAGE_NAME=$(echo "$PACKAGES" | grep -i "$(basename $REPOSITORY)" | head -1)
            if [ -z "$PACKAGE_NAME" ]; then
                # If exact match not found, use the first package
                PACKAGE_NAME=$(echo "$PACKAGES" | head -1)
            fi
            TAGS=$(gh api "/user/packages/container/$PACKAGE_NAME/versions" --jq '.[].metadata.container.tags[]' 2>/dev/null || echo "")
        else
            log_error "No container packages found for user"
            TAGS=""
        fi
    else
        log_warning "GitHub CLI not found. Cannot fetch private registry tags without it."
        log_info "Please install GitHub CLI or use manual rollback with known tags."
        log_info ""
        log_info "Manual rollback example:"
        log_info "  ./scripts/rollback.sh master-abc123"
        log_info "  ./scripts/rollback.sh 2024-01-15-14-30"
        return 1
    fi
    
    if [ -z "$TAGS" ]; then
        log_error "No versions found or unable to fetch versions"
        log_info "This might be because:"
        log_info "  1. GitHub CLI is not authenticated (run: gh auth login)"
        log_info "  2. Repository is private and you don't have access"
        log_info "  3. No images have been built yet"
        return 1
    fi
    
    echo ""
    log_info "Available versions:"
    echo "$TAGS" | sort -r | while read tag; do
        if [ -n "$tag" ]; then
            echo "  - $tag"
        fi
    done
    echo ""
}

get_previous_version() {
    if command -v gh >/dev/null 2>&1; then
        # Get container packages silently
        PACKAGES=$(gh api "/user/packages?package_type=container" --jq '.[].name' 2>/dev/null || echo "")
        
        if [ -n "$PACKAGES" ]; then
            # Find the package that matches our repository name
            PACKAGE_NAME=$(echo "$PACKAGES" | grep -i "$(basename $REPOSITORY)" | head -1)
            if [ -z "$PACKAGE_NAME" ]; then
                # If exact match not found, use the first package
                PACKAGE_NAME=$(echo "$PACKAGES" | head -1)
            fi
            
            # Get tags silently
            TAGS=$(gh api "/user/packages/container/$PACKAGE_NAME/versions" --jq '.[].metadata.container.tags[]' 2>/dev/null || echo "")
        else
            return 1
        fi
    else
        return 1
    fi
    
    if [ -z "$TAGS" ]; then
        return 1
    fi
    
    # Get the second most recent tag (skip latest and master)
    # Prefer timestamp-based tags for chronological sorting
    TIMESTAMP_TAGS=$(echo "$TAGS" | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}$" | sort -r)
    COMMIT_TAGS=$(echo "$TAGS" | grep -E "^master-[a-f0-9]+$" | sort -r)
    
    if [ -n "$TIMESTAMP_TAGS" ]; then
        # Use timestamp-based tags (they sort chronologically)
        PREVIOUS=$(echo "$TIMESTAMP_TAGS" | head -2 | tail -1)
    else
        # Fallback to commit tags (alphabetical sort)
        PREVIOUS=$(echo "$COMMIT_TAGS" | head -2 | tail -1)
    fi
    
    if [ -z "$PREVIOUS" ]; then
        return 1
    fi
    
    # Return only the version tag, no logging
    echo "$PREVIOUS"
}

rollback_to_version() {
    local target_tag="$1"
    local full_image_name="$IMAGE_NAME:$target_tag"
    
    log_info "Starting rollback to version: $target_tag"
    
    # Check if docker-compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker compose file not found: $COMPOSE_FILE"
        return 1
    fi
    
    # Pull the target image
    log_info "Pulling image: $full_image_name"
    if ! docker pull "$full_image_name"; then
        log_error "Failed to pull image: $full_image_name"
        return 1
    fi
    
    # Tag the target image as latest
    log_info "Tagging $full_image_name as latest"
    docker tag "$full_image_name" "$IMAGE_NAME:latest"
    
    # Stop current containers
    log_info "Stopping current containers..."
    docker compose down
    
    # Start with new image
    log_info "Starting containers with rolled back image..."
    docker compose up -d
    
    # Verify deployment
    log_info "Verifying deployment..."
    sleep 10  # Give more time for the API to start up
    
    # Check if containers are running
    if docker compose ps | grep -q "Up"; then
        log_success "Rollback completed successfully!"
        log_info "Current version: $target_tag"
        log_info "Containers status:"
        docker compose ps
        
        # Test API health endpoint
        log_info "Testing API health..."
        sleep 5
        if curl -f -s http://localhost:8000/ >/dev/null 2>&1; then
            log_success "API is responding correctly!"
        else
            log_warning "API health check failed, but containers are running"
            log_info "You may want to check the logs: docker compose logs api"
        fi
    else
        log_error "Rollback failed - containers are not running"
        log_info "Container status:"
        docker compose ps
        log_info "Check logs for more details:"
        log_info "  docker compose logs api"
        log_info "  docker compose logs db"
        return 1
    fi
}

# Main script logic
main() {
    log_info "Backend API Rollback script started with arguments: $*"
    
    case "${1:-}" in
        --help|-h)
            log_info "Showing help..."
            show_help
            exit 0
            ;;
        --list)
            log_info "Listing available versions..."
            list_available_versions
            exit 0
            ;;
        --latest)
            log_info "Rolling back to latest version..."
            rollback_to_version "latest"
            ;;
        --previous)
            log_info "Rolling back to previous version..."
            PREVIOUS_VERSION=$(get_previous_version)
            if [ -n "$PREVIOUS_VERSION" ]; then
                log_info "Previous version found: $PREVIOUS_VERSION"
                rollback_to_version "$PREVIOUS_VERSION"
            else
                log_error "Failed to get previous version"
                log_info "Let's try listing versions manually..."
                list_available_versions
                exit 1
            fi
            ;;
        "")
            log_info "No arguments provided, listing available versions..."
            list_available_versions
            ;;
        *)
            log_info "Rolling back to specific version: $1"
            rollback_to_version "$1"
            ;;
    esac
}

# Run main function with all arguments
main "$@"
```

**Configuration**: Update the `REGISTRY` and `REPOSITORY` variables in the script to match your container registry.

**Note**: All convenience scripts are located in the `scripts/` directory to keep the project root clean and organized.

### Additional Useful Scripts

**Migration Helper Script** (suggested):

```bash
#!/bin/bash
# scripts/create_migration.sh

# Usage: ./scripts/create_migration.sh <migration_name>
# Example: ./scripts/create_migration.sh add_user_email_index

if [ -z "$1" ]; then
    echo "Error: Migration name required"
    echo "Usage: $0 <migration_name>"
    exit 1
fi

MIGRATION_NAME="$1"
echo "Creating migration: $MIGRATION_NAME"
docker compose run --rm api alembic revision --autogenerate -m "$MIGRATION_NAME"
```

**Database Backup Script** (suggested):

```bash
#!/bin/bash
# scripts/backup_db.sh

# Usage: ./scripts/backup_db.sh [backup_name]

BACKUP_NAME="${1:-backup_$(date +%Y%m%d_%H%M%S)}"
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

echo "Creating database backup: $BACKUP_NAME"
docker compose exec -T db mysqldump -u${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > "$BACKUP_DIR/$BACKUP_NAME.sql"
echo "Backup saved to: $BACKUP_DIR/$BACKUP_NAME.sql"
```

**Database Restore Script** (suggested):

```bash
#!/bin/bash
# scripts/restore_db.sh

# Usage: ./scripts/restore_db.sh <backup_file>

if [ -z "$1" ]; then
    echo "Error: Backup file required"
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring database from: $BACKUP_FILE"
docker compose exec -T db mysql -u${DB_USER} -p${DB_PASSWORD} ${DB_NAME} < "$BACKUP_FILE"
echo "Database restored successfully"
```

### Script Best Practices

When creating new convenience scripts:

1. **Use shebang**: Always start with `#!/bin/bash`
2. **Error handling**: Use `set -e` to exit on errors
3. **User feedback**: Provide clear, color-coded output
4. **Help text**: Include `--help` option for all scripts
5. **Exit codes**: Return appropriate exit codes (0 for success, non-zero for errors)
6. **Documentation**: Add comments explaining what the script does
7. **Configuration**: Make scripts configurable via environment variables or arguments
8. **Safety checks**: Verify prerequisites before executing (e.g., check if Docker is running)
9. **Cleanup**: Always clean up temporary resources
10. **Idempotency**: Scripts should be safe to run multiple times

---

## Development Guidelines

These guidelines are intended for both human developers and AI assistants working on the template. Once developers fork this template and start adding their business logic, following these guidelines will help maintain code quality and consistency.

### Code Organization & Structure

1. **Follow the existing project structure**: Maintain the separation between `api/`, `core/`, `models/`, `schemas/`, `services/`, and `utils/`
2. **One file per domain concept**: Each major domain entity should have its own files (e.g., `users.py`, `products.py`, `orders.py`)
3. **Keep endpoints thin**: Endpoints should only handle HTTP concerns; business logic belongs in services
4. **Use dependency injection**: Leverage FastAPI's dependency system for database sessions, authentication, etc.
5. **Group related functionality**: Keep related endpoints, services, and models together

### Naming Conventions

1. **Files**: Use snake_case (e.g., `user_service.py`, `order_models.py`)
2. **Classes**: Use PascalCase (e.g., `UserService`, `OrderModel`)
3. **Functions/Methods**: Use snake_case (e.g., `get_user_by_id`, `create_order`)
4. **Constants**: Use UPPER_SNAKE_CASE (e.g., `MAX_PAGE_SIZE`, `DEFAULT_RATE_LIMIT`)
5. **Database tables**: Use snake_case plural (e.g., `users`, `order_items`)
6. **API endpoints**: Use kebab-case in URLs (e.g., `/api/v1/user-profiles`)
7. **Environment variables**: Use UPPER_SNAKE_CASE (e.g., `DB_HOST`, `JWT_SECRET_KEY`)

### API Design

1. **RESTful principles**: Follow REST conventions (GET for read, POST for create, PUT/PATCH for update, DELETE for delete)
2. **Version your API**: Always use `/api/v1/` prefix for endpoints
3. **Consistent response formats**: Use the same response structure across all endpoints
4. **Proper HTTP status codes**: Use appropriate status codes (200, 201, 400, 401, 404, 422, 500, etc.)
5. **Pagination**: Always implement pagination for list endpoints (use `page` and `page_size` query parameters)
6. **Filtering and sorting**: Support filtering and sorting via query parameters when appropriate
7. **Document endpoints**: Always include docstrings with examples in endpoint functions

### Error Handling

1. **Use custom exceptions**: Extend `BaseAPIException` for domain-specific errors
2. **Consistent error responses**: All errors should follow the same response format
3. **Log errors appropriately**: Use appropriate log levels (ERROR for exceptions, WARNING for recoverable issues)
4. **Don't expose internal details**: Never return stack traces or internal error messages to clients
5. **Validate input early**: Use Pydantic schemas for request validation

### Database & Migrations

1. **Always use migrations**: Never modify the database schema directly; always create Alembic migrations
2. **Test migrations**: Test both up and down migrations before committing
3. **Migration naming**: Use descriptive names (e.g., `add_user_email_index`, `create_orders_table`)
4. **No raw SQL in application code**: Use SQLAlchemy ORM; raw SQL only in migrations when necessary
5. **Use transactions**: Wrap related database operations in transactions
6. **Handle database errors**: Catch and handle database exceptions appropriately
7. **Index appropriately**: Add indexes for frequently queried columns

### Testing

1. **Write tests for new features**: Every new feature should have corresponding tests
2. **Test coverage**: Aim for at least 80% code coverage
3. **Integration tests**: Write integration tests for API endpoints
4. **Unit tests**: Write unit tests for services and utilities
5. **Test fixtures**: Use pytest fixtures for common test setup (database, clients, etc.)
6. **Test isolation**: Each test should be independent and not rely on other tests
7. **Test edge cases**: Test both happy paths and error cases
8. **Run tests before committing**: Always run tests locally before committing code

### Documentation

1. **Docstrings**: Write docstrings for all public functions, classes, and methods
2. **Type hints**: Use type hints for all function parameters and return values
3. **API documentation**: FastAPI auto-generates docs, but add detailed descriptions and examples
4. **README updates**: Update README when adding new features or changing setup procedures
5. **Code comments**: Add comments for complex logic or non-obvious decisions
6. **CHANGELOG**: Maintain a CHANGELOG.md for significant changes

### Security

1. **Never commit secrets**: Use environment variables for all secrets and sensitive data
2. **Validate all input**: Always validate and sanitize user input
3. **Use parameterized queries**: Never use string concatenation for SQL queries
4. **Authentication required**: Protect endpoints that require authentication
5. **Authorization checks**: Verify users have permission to perform actions
6. **Rate limiting**: Be aware of rate limiting on sensitive endpoints
7. **HTTPS in production**: Always use HTTPS in production environments
8. **Dependency updates**: Regularly update dependencies to patch security vulnerabilities

### Performance

1. **Database queries**: Avoid N+1 queries; use eager loading when appropriate
2. **Pagination**: Always paginate large result sets
3. **Caching**: Consider caching for frequently accessed, rarely changing data
4. **Async operations**: Use async/await for I/O-bound operations
5. **Connection pooling**: Database connection pooling is already configured; don't create unnecessary connections
6. **Response size**: Keep response payloads reasonable; use pagination and filtering

### Code Quality

1. **DRY principle**: Don't Repeat Yourself - extract common logic into reusable functions/classes
2. **Single Responsibility**: Each function/class should have one clear purpose
3. **Keep functions small**: Functions should be focused and not exceed ~50 lines when possible
4. **Avoid deep nesting**: Refactor deeply nested code into separate functions
5. **Meaningful names**: Use descriptive variable and function names
6. **Remove dead code**: Delete unused code, don't comment it out
7. **Code formatting**: Follow PEP 8 style guide (use tools like `black` or `ruff`)

### Git & Version Control

1. **Meaningful commit messages**: Write clear, descriptive commit messages
2. **Small, focused commits**: Make commits that represent logical units of work
3. **Branch naming**: Use descriptive branch names (e.g., `feature/user-authentication`, `fix/order-calculation-bug`)
4. **Pull requests**: Create pull requests for all changes, even small ones
5. **Code review**: Request code reviews before merging
6. **Rebase before merge**: Keep a clean git history by rebasing feature branches

### Dependencies

1. **Pin versions**: Always pin dependency versions in `requirements.txt`
2. **Check for updates**: Regularly check for dependency updates and security patches
3. **Minimal dependencies**: Only add dependencies that are truly necessary
4. **Document why**: If adding a new dependency, document why it's needed
5. **Test after updates**: Test thoroughly after updating dependencies

### Logging

1. **Use structured logging**: Use the existing JSON logging format
2. **Appropriate log levels**: Use DEBUG, INFO, WARNING, ERROR appropriately
3. **Include context**: Include relevant context in log messages (user ID, request ID, etc.)
4. **Don't log sensitive data**: Never log passwords, tokens, or other sensitive information
5. **Log important events**: Log important business events (user creation, order placement, etc.)

### Metrics & Observability

1. **Add custom metrics**: Add Prometheus metrics for important business operations
2. **Monitor performance**: Track performance metrics for critical operations
3. **Error tracking**: Ensure errors are properly tracked and visible in monitoring tools

---

## AI Rules

These rules are designed for AI-centric IDEs (like Cursor, GitHub Copilot, etc.) to follow when making code changes. They help prevent common AI mistakes and ensure code quality.

### Code Quality & Consistency

1. **Always check for code duplication**: Before adding new code, check if similar functionality already exists
2. **Follow existing patterns**: Match the coding style and patterns used in the existing codebase
3. **Use existing utilities**: Check `app/utils/` and `app/core/` for existing utilities before creating new ones
4. **Maintain consistency**: Keep naming conventions, code structure, and patterns consistent with the codebase

### Testing Requirements

1. **Always write tests**: When adding new features, always write corresponding tests
2. **Run tests before committing**: Never commit code without running tests first
3. **Tests must pass**: All tests must pass before code is considered complete
4. **Test coverage**: Ensure new code has adequate test coverage
5. **Update existing tests**: If modifying existing functionality, update related tests

### Documentation

1. **Document all endpoints**: Every API endpoint must have a docstring with description and examples
2. **Type hints required**: All functions must have complete type hints
3. **Docstrings for public APIs**: All public functions, classes, and methods must have docstrings
4. **Update README if needed**: Update README.md when adding new setup steps or features
5. **Code comments**: Add comments for complex logic or non-obvious code

### Dependency Management

1. **Check latest versions**: When adding dependencies, check for the latest stable version
2. **Pin versions**: Always pin exact versions in requirements.txt (e.g., `fastapi==0.115.14`, not `fastapi>=0.115.0`)
3. **Security check**: Verify dependencies don't have known security vulnerabilities
4. **Minimal dependencies**: Only add dependencies that are absolutely necessary
5. **Document dependencies**: If adding a new dependency, document why it's needed

### Version Management

1. **Increment version**: Always increment the version number when making changes that affect the API
2. **Semantic versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)
3. **Update version in config**: Update `API_VERSION` in `app/core/config.py`
4. **CHANGELOG entry**: Add an entry to CHANGELOG.md for significant changes

### Code Review & Validation

1. **Self-review**: Review your own code before considering it complete
2. **Check for errors**: Always check for syntax errors, type errors, and logical errors
3. **Linter compliance**: Ensure code passes linting checks
4. **No breaking changes without notice**: Don't make breaking changes to existing APIs without discussion

### Security

1. **Never hardcode secrets**: Never commit secrets, API keys, or passwords in code
2. **Input validation**: Always validate and sanitize user input
3. **SQL injection prevention**: Always use parameterized queries, never string concatenation
4. **Authentication checks**: Verify authentication is required for protected endpoints
5. **Authorization checks**: Verify authorization is checked for sensitive operations

### Database & Migrations

1. **Always create migrations**: Never modify database schema without creating a migration
2. **Test migrations**: Test migrations work both up and down
3. **Migration naming**: Use descriptive migration names
4. **No direct schema changes**: Never use `Base.metadata.create_all()` in application code

### Error Handling

1. **Use custom exceptions**: Use existing custom exception classes from `app/core/exceptions.py`
2. **Consistent error format**: All errors must follow the same response format
3. **Log errors**: Always log errors with appropriate log levels
4. **Don't expose internals**: Never expose stack traces or internal error details to clients

### Git Practices

1. **Meaningful commit messages**: Write clear, descriptive commit messages following conventional commits format
2. **Small commits**: Make focused, logical commits rather than large monolithic commits
3. **No WIP commits**: Don't commit work-in-progress code to main/master branches
4. **Check git status**: Always check what files are being committed

### Performance

1. **Avoid N+1 queries**: Check for and fix N+1 query problems
2. **Pagination**: Always implement pagination for list endpoints
3. **Async operations**: Use async/await for I/O-bound operations
4. **Connection pooling**: Don't create unnecessary database connections

### Code Structure

1. **Follow project structure**: Maintain the existing project structure (api/, core/, models/, schemas/, services/, utils/)
2. **Thin controllers**: Keep endpoint functions thin; business logic goes in services
3. **Single responsibility**: Each function/class should have one clear purpose
4. **DRY principle**: Don't repeat code; extract common logic

### Before Committing Checklist

Before committing any code, verify:

1. ✅ All tests pass
2. ✅ Code follows project style and patterns
3. ✅ No code duplication
4. ✅ All endpoints documented
5. ✅ Type hints added
6. ✅ No hardcoded secrets
7. ✅ Migrations created (if schema changed)
8. ✅ Version incremented (if API changed)
9. ✅ CHANGELOG updated (if significant change)
10. ✅ Dependencies checked for latest versions
11. ✅ No syntax or type errors
12. ✅ Linter passes

---

## Metrics & Observability

The template includes built-in Prometheus metrics that can be enabled via feature flag. Additionally, optional monitoring services can be added using a separate Docker Compose file for easy integration with tools like Grafana, Loki, Sentry, and others.

### Built-in Metrics (Prometheus)

The template automatically exports Prometheus metrics when enabled. All metrics are optional and can be disabled via configuration.

#### Default Metrics Exported

When metrics are enabled, the following metrics are automatically collected:

**HTTP Metrics**:
- `http_requests_total` - Total number of HTTP requests (counter)
  - Labels: `method`, `endpoint`, `status_code`
- `http_request_duration_seconds` - HTTP request duration (histogram)
  - Labels: `method`, `endpoint`, `status_code`
  - Includes percentiles: p50, p90, p95, p99
- `http_requests_active` - Currently active HTTP requests (gauge)
- `http_request_size_bytes` - HTTP request size (histogram)
- `http_response_size_bytes` - HTTP response size (histogram)

**Status Code Metrics**:
- `http_status_codes_total` - Count of responses by status code (counter)
  - Labels: `status_code`, `status_class` (2xx, 4xx, 5xx)

**Endpoint Usage**:
- `endpoint_requests_total` - Requests per endpoint (counter)
  - Labels: `endpoint`, `method`

**Database Metrics** (if enabled):
- `db_connections_active` - Active database connections (gauge)
- `db_connections_idle` - Idle database connections (gauge)
- `db_query_duration_seconds` - Database query duration (histogram)
- `db_query_errors_total` - Database query errors (counter)

**System Metrics** (if enabled):
- `process_cpu_seconds_total` - CPU time used (counter)
- `process_resident_memory_bytes` - Resident memory size (gauge)
- `process_virtual_memory_bytes` - Virtual memory size (gauge)
- `process_start_time_seconds` - Process start time (gauge)
- `process_open_fds` - Number of open file descriptors (gauge)

**Additional Important Metrics**:
- `http_request_errors_total` - Total HTTP request errors (counter)
  - Labels: `error_type`, `endpoint`
- `http_timeout_requests_total` - Requests that timed out (counter)
- `database_transactions_total` - Database transactions (counter)
  - Labels: `operation_type` (read/write)
- `cache_operations_total` - Cache hits/misses (counter, if caching enabled)
  - Labels: `operation` (hit/miss), `cache_name`
- `background_jobs_total` - Background job executions (counter, if applicable)
  - Labels: `job_type`, `status` (success/failure)

#### Configuration

**File: `app/core/config.py`** (add to Settings class):

```python
# Metrics Configuration
ENABLE_METRICS: bool = False  # Enable Prometheus metrics endpoint
METRICS_PATH: str = "/metrics"  # Path for metrics endpoint
METRICS_INCLUDE_SYSTEM: bool = False  # Include system metrics (CPU, memory)
METRICS_INCLUDE_DB: bool = False  # Include database connection metrics
```

**File: `.env.example`**:

```bash
# Metrics
ENABLE_METRICS=false
METRICS_PATH=/metrics
METRICS_INCLUDE_SYSTEM=false
METRICS_INCLUDE_DB=false
```

#### Prometheus Metrics Middleware

**File: `app/core/metrics.py`**

```python
"""Prometheus metrics collection for FastAPI."""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
    start_http_server
)
from prometheus_client.multiprocess import MultiProcessCollector
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import re
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Enable process metrics if system metrics are enabled
if settings.METRICS_INCLUDE_SYSTEM:
    from prometheus_client import PROCESS_COLLECTOR, PLATFORM_COLLECTOR
    # These are automatically registered when imported

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_active = Gauge(
    'http_requests_active',
    'Currently active HTTP requests'
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000)
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint', 'status_code'],
    buckets=(100, 1000, 10000, 100000, 1000000)
)

http_status_codes_total = Counter(
    'http_status_codes_total',
    'Total number of HTTP responses by status code',
    ['status_code', 'status_class']
)

endpoint_requests_total = Counter(
    'endpoint_requests_total',
    'Total number of requests per endpoint',
    ['endpoint', 'method']
)

http_request_errors_total = Counter(
    'http_request_errors_total',
    'Total number of HTTP request errors',
    ['error_type', 'endpoint']
)

http_timeout_requests_total = Counter(
    'http_timeout_requests_total',
    'Total number of requests that timed out',
    ['endpoint', 'method']
)

# Database Metrics (if enabled)
if settings.METRICS_INCLUDE_DB:
    from app.core.database import engine
    
    db_connections_active = Gauge(
        'db_connections_active',
        'Active database connections'
    )
    
    db_connections_idle = Gauge(
        'db_connections_idle',
        'Idle database connections'
    )
    
    db_query_duration_seconds = Histogram(
        'db_query_duration_seconds',
        'Database query duration in seconds',
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
    )
    
    db_query_errors_total = Counter(
        'db_query_errors_total',
        'Total number of database query errors',
        ['error_type']
    )

def normalize_path(path: str) -> str:
    """
    Normalize path for metrics (replace IDs with placeholders).
    
    Examples:
    /api/v1/users/123 -> /api/v1/users/{id}
    /api/v1/products/456/images -> /api/v1/products/{id}/images
    """
    # Replace numeric IDs
    path = re.sub(r'/\d+', '/{id}', path)
    # Replace UUIDs
    path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path, flags=re.IGNORECASE)
    return path

def get_status_class(status_code: int) -> str:
    """Get status code class (2xx, 4xx, 5xx)."""
    if 200 <= status_code < 300:
        return '2xx'
    elif 400 <= status_code < 500:
        return '4xx'
    elif 500 <= status_code < 600:
        return '5xx'
    else:
        return 'other'

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.ENABLE_METRICS:
            return await call_next(request)
        
        # Skip metrics endpoint itself
        if request.url.path == settings.METRICS_PATH:
            return await call_next(request)
        
        # Increment active requests
        http_requests_active.inc()
        
        # Normalize path for metrics
        endpoint = normalize_path(request.url.path)
        method = request.method
        
        # Track request size
        request_size = 0
        if hasattr(request, '_body'):
            request_size = len(request._body) if request._body else 0
        
        # Start timer
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            status_code = response.status_code
            status_class = get_status_class(status_code)
            
            # Track response size
            response_size = 0
            if hasattr(response, 'body'):
                response_size = len(response.body) if response.body else 0
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(duration)
            
            http_status_codes_total.labels(
                status_code=status_code,
                status_class=status_class
            ).inc()
            
            endpoint_requests_total.labels(
                endpoint=endpoint,
                method=method
            ).inc()
            
            if request_size > 0:
                http_request_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(request_size)
            
            if response_size > 0:
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code
                ).observe(response_size)
            
            return response
            
        except Exception as e:
            # Record 500 error
            duration = time.time() - start_time
            status_code = 500
            status_class = '5xx'
            error_type = type(e).__name__
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(duration)
            
            http_status_codes_total.labels(
                status_code=status_code,
                status_class=status_class
            ).inc()
            
            http_request_errors_total.labels(
                error_type=error_type,
                endpoint=endpoint
            ).inc()
            
            raise
        finally:
            # Decrement active requests
            http_requests_active.dec()

def get_metrics_response() -> Response:
    """Get Prometheus metrics response."""
    if not settings.ENABLE_METRICS:
        return StarletteResponse(
            content="Metrics disabled",
            status_code=404
        )
    
    try:
        # In multi-process mode (with workers), use MultiProcessCollector
        # For single-process, use default registry
        if hasattr(REGISTRY, '_collector_to_aggregator_map'):
            registry = REGISTRY
        else:
            registry = REGISTRY
        
        output = generate_latest(registry)
        return StarletteResponse(
            content=output,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return StarletteResponse(
            content=f"Error generating metrics: {str(e)}",
            status_code=500
        )
```

#### Adding Metrics Endpoint

**File: `app/api/endpoints/metrics.py`**

```python
from fastapi import APIRouter
from fastapi.responses import Response
from app.core.metrics import get_metrics_response
from app.core.config import settings

router = APIRouter()

@router.get(
    settings.METRICS_PATH,
    tags=["metrics"],
    summary="Prometheus metrics endpoint",
    description="Exports Prometheus metrics for monitoring"
)
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format. Only available when ENABLE_METRICS=true.
    """
    return get_metrics_response()
```

**File: `app/api/api.py`** (add to router):

```python
from app.api.endpoints import health, version, metrics

# ... existing code ...

api_router.include_router(
    metrics.router,
    tags=["metrics"]
)
```

**File: `app/main.py`** (add middleware):

```python
from app.core.metrics import PrometheusMiddleware

# Add Prometheus middleware if metrics enabled
if settings.ENABLE_METRICS:
    app.add_middleware(PrometheusMiddleware)
```

#### Custom Metrics

Developers can add custom business metrics for their specific use cases.

**Example: E-commerce Custom Metrics**

```python
from prometheus_client import Counter, Histogram, Gauge

# Order metrics
orders_created_total = Counter(
    'orders_created_total',
    'Total number of orders created',
    ['payment_method', 'delivery_type']
)

order_value_total = Counter(
    'order_value_total',
    'Total value of orders',
    ['currency']
)

orders_in_progress = Gauge(
    'orders_in_progress',
    'Number of orders currently being processed'
)

order_processing_duration_seconds = Histogram(
    'order_processing_duration_seconds',
    'Time taken to process an order',
    ['order_type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
)

# Product metrics
products_viewed_total = Counter(
    'products_viewed_total',
    'Total number of product views',
    ['category_id', 'product_id']
)

products_in_stock = Gauge(
    'products_in_stock',
    'Number of products currently in stock',
    ['category_id']
)

# Usage in service layer
def create_order(order_data):
    start_time = time.time()
    orders_in_progress.inc()
    
    try:
        # ... create order logic ...
        
        # Record metrics
        orders_created_total.labels(
            payment_method=order_data.payment_method,
            delivery_type=order_data.delivery_type
        ).inc()
        
        order_value_total.labels(
            currency=order_data.currency
        ).inc(order_data.total_amount)
        
        order_processing_duration_seconds.labels(
            order_type=order_data.type
        ).observe(time.time() - start_time)
        
        return order
    finally:
        orders_in_progress.dec()
```

**Best Practices for Custom Metrics**:
- Use appropriate metric types (Counter, Gauge, Histogram)
- Keep label cardinality low (avoid high-cardinality labels like user IDs)
- Use meaningful metric names with units
- Document your custom metrics
- Group related metrics logically

#### Querying Metrics for HTTP Method and Status Code Breakdowns

The metrics are structured to easily query HTTP method and status code breakdowns. Here are the Prometheus queries you'll need:

**HTTP Method Breakdown** (GET, POST, PUT, PATCH, DELETE, etc.):

```promql
# Total requests by HTTP method (absolute counts)
sum by (method) (http_requests_total)

# Requests per second by method
sum by (method) (rate(http_requests_total[5m]))

# Percentage distribution by method
sum by (method) (rate(http_requests_total[5m])) / sum(rate(http_requests_total[5m])) * 100
```

**HTTP Status Code Breakdown** (200, 401, 404, 503, etc.):

```promql
# Total requests by status code (absolute counts)
sum by (status_code) (http_status_codes_total)

# Requests per second by status code
sum by (status_code) (rate(http_status_codes_total[5m]))

# Percentage distribution by status code
sum by (status_code) (rate(http_status_codes_total[5m])) / sum(rate(http_status_codes_total[5m])) * 100

# Status codes grouped by class (2xx, 4xx, 5xx)
sum by (status_class) (rate(http_status_codes_total[5m]))
```

**Combined Queries** (Method + Status Code):

```promql
# Requests by method and status code
sum by (method, status_code) (http_requests_total)

# Error rate by method (4xx and 5xx)
sum by (method) (rate(http_requests_total{status_code=~"4..|5.."}[5m]))
```

#### Grafana Dashboard Panels for Method and Status Breakdowns

Here are example Grafana panel configurations that create pie charts with tables (showing counts and percentages):

**File: `monitoring/grafana/dashboards/http-breakdowns.json`**

```json
{
  "dashboard": {
    "title": "HTTP Request Breakdowns",
    "tags": ["fastapi", "http"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Method Breakdown",
        "type": "piechart",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "sum by (method) (http_requests_total)",
            "legendFormat": "{{method}}",
            "refId": "A"
          }
        ],
        "options": {
          "pieType": "pie",
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "values": ["value", "percent"]
          },
          "tooltip": {
            "mode": "single"
          }
        }
      },
      {
        "id": 2,
        "title": "HTTP Status Code Breakdown",
        "type": "piechart",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "sum by (status_code) (http_status_codes_total)",
            "legendFormat": "{{status_code}}",
            "refId": "A"
          }
        ],
        "options": {
          "pieType": "pie",
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "values": ["value", "percent"]
          },
          "tooltip": {
            "mode": "single"
          }
        }
      },
      {
        "id": 3,
        "title": "HTTP Methods (Table View)",
        "type": "table",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "sum by (method) (http_requests_total)",
            "format": "table",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "align": "auto",
              "displayMode": "list"
            }
          },
          "overrides": []
        }
      },
      {
        "id": 4,
        "title": "HTTP Status Codes (Table View)",
        "type": "table",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "sum by (status_code) (http_status_codes_total)",
            "format": "table",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "align": "auto",
              "displayMode": "list"
            }
          },
          "overrides": []
        }
      }
    ]
  }
}
```

**Quick Setup in Grafana UI**:

1. **Create HTTP Method Breakdown Panel**:
   - Go to Grafana → Dashboards → New Dashboard
   - Click "Add visualization"
   - Select "Pie chart" visualization
   - In the query editor:
     - Data source: Prometheus
     - Query: `sum by (method) (http_requests_total)`
     - Legend: `{{method}}`
   - In the panel options:
     - Legend: Enable "Show legend"
     - Legend placement: Right
     - Legend values: Check "Value" and "Percent"
   - This creates a pie chart with a table legend showing counts and percentages

2. **Create HTTP Status Code Breakdown Panel**:
   - Add another panel (or duplicate the method panel)
   - Change the query to: `sum by (status_code) (http_status_codes_total)`
   - Change legend to: `{{status_code}}`
   - This creates the status code breakdown pie chart

3. **For Time-Series Views** (optional):
   - Add Panel → Visualization: Time Series
   - Query: `sum by (method) (rate(http_requests_total[5m]))`
   - Shows request rate over time by method
   - Useful for seeing trends

**Verification**:

You can verify the metrics are working by:

1. **Check Prometheus directly**:
   ```bash
   # Access Prometheus UI at http://localhost:9090
   # Try these queries:
   sum by (method) (http_requests_total)
   sum by (status_code) (http_status_codes_total)
   ```

2. **Check metrics endpoint**:
   ```bash
   curl http://localhost:8000/metrics | grep http_requests_total
   curl http://localhost:8000/metrics | grep http_status_codes_total
   ```

The metrics you see will have labels like:
```
http_requests_total{method="GET",endpoint="/api/v1/users/{id}",status_code="200"} 1234
http_requests_total{method="POST",endpoint="/api/v1/users",status_code="201"} 567
http_status_codes_total{status_code="200",status_class="2xx"} 1234
http_status_codes_total{status_code="404",status_class="4xx"} 89
```

When you aggregate these in Prometheus/Grafana (using `sum by (method)` or `sum by (status_code)`), you get exactly the breakdowns shown in your image - pie charts with tables showing counts and percentages for each method and status code!

### Optional Monitoring Services

The template includes a separate Docker Compose file for optional monitoring services. These are completely optional and can be started independently.

**File: `docker-compose.monitoring.yml`**

```yaml
version: '3.8'

services:
  # Prometheus - Metrics collection and storage
  prometheus:
    image: prom/prometheus:latest
    container_name: fastapi_prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    networks:
      - monitoring
      - backend

  # Grafana - Metrics visualization
  grafana:
    image: grafana/grafana:latest
    container_name: fastapi_grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3001
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    depends_on:
      - prometheus
    networks:
      - monitoring

  # Loki - Log aggregation
  loki:
    image: grafana/loki:latest
    container_name: fastapi_loki
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring

  # Grafana Alloy - Log shipper (sends logs to Loki)
  # Note: Promtail is deprecated; Grafana Labs recommends Alloy for new setups
  alloy:
    image: grafana/alloy:latest
    container_name: fastapi_alloy
    restart: unless-stopped
    ports:
      - "12345:12345"  # Alloy HTTP server for health checks and UI
    volumes:
      - ./monitoring/alloy/config.river:/etc/alloy/config.river:ro
      - ./logs:/var/log/app:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - alloy_data:/var/lib/alloy/data
    command:
      - run
      - --server.http.listen-addr=0.0.0.0:12345
      - --storage.path=/var/lib/alloy/data
      - /etc/alloy/config.river
    depends_on:
      - loki
    networks:
      - monitoring

  # Sentry - Error tracking (optional, requires SENTRY_DSN)
  sentry:
    image: getsentry/sentry:latest
    container_name: fastapi_sentry
    restart: unless-stopped
    ports:
      - "9000:9000"
    environment:
      - SENTRY_SECRET_KEY=${SENTRY_SECRET_KEY}
      - SENTRY_POSTGRES_HOST=sentry-db
      - SENTRY_DB_USER=sentry
      - SENTRY_DB_PASSWORD=${SENTRY_DB_PASSWORD}
      - SENTRY_DB_NAME=sentry
      - SENTRY_REDIS_HOST=sentry-redis
    volumes:
      - sentry_data:/var/lib/sentry/files
    depends_on:
      - sentry-db
      - sentry-redis
    networks:
      - monitoring

  sentry-db:
    image: postgres:15
    container_name: fastapi_sentry_db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=sentry
      - POSTGRES_PASSWORD=${SENTRY_DB_PASSWORD}
      - POSTGRES_DB=sentry
    volumes:
      - sentry_db_data:/var/lib/postgresql/data
    networks:
      - monitoring

  sentry-redis:
    image: redis:7-alpine
    container_name: fastapi_sentry_redis
    restart: unless-stopped
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
  backend:
    external: true  # Connect to backend network from main docker-compose.yml

volumes:
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  loki_data:
    driver: local
  alloy_data:
    driver: local
  sentry_data:
    driver: local
  sentry_db_data:
    driver: local
```

#### Prometheus Configuration

**File: `monitoring/prometheus/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'fastapi-template'

# Alertmanager configuration (optional)
# alerting:
#   alertmanagers:
#     - static_configs:
#         - targets: ['alertmanager:9093']

# Load rules once and periodically evaluate them
# rule_files:
#   - "alert_rules.yml"

# Scrape configurations
scrape_configs:
  # Scrape Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Scrape FastAPI application
  - job_name: 'fastapi-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['api:8000']
        labels:
          service: 'api'
          environment: 'production'
    scrape_interval: 10s
    scrape_timeout: 5s

  # Optional: Scrape database exporter if using
  # - job_name: 'mysql-exporter'
  #   static_configs:
  #     - targets: ['mysql-exporter:9104']
```

#### Grafana Configuration

**File: `monitoring/grafana/provisioning/datasources/prometheus.yml`**

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
```

**File: `monitoring/grafana/provisioning/dashboards/dashboard.yml`**

```yaml
apiVersion: 1

providers:
  - name: 'FastAPI Dashboards'
    orgId: 1
    folder: 'FastAPI'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

**File: `monitoring/grafana/dashboards/fastapi-overview.json`** (Example dashboard)

```json
{
  "dashboard": {
    "title": "FastAPI Overview",
    "tags": ["fastapi"],
    "timezone": "browser",
    "panels": [
      {
        "title": "HTTP Requests per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Status Codes",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_status_codes_total[5m])",
            "legendFormat": "{{status_code}}"
          }
        ]
      },
      {
        "title": "Active Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "http_requests_active",
            "legendFormat": "Active"
          }
        ]
      }
    ]
  }
}
```

#### Loki Configuration

**File: `monitoring/loki/loki-config.yml`**

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

#### Grafana Alloy Configuration

**File: `monitoring/alloy/config.river`**

```river
// Grafana Alloy configuration for shipping logs to Loki
// Note: Promtail is deprecated; Alloy is the recommended successor

// Loki client configuration
loki.write "loki" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}

// Local file discovery for application logs
local.file_match "app_logs" {
  path_targets = [{
    __path__ = "/var/log/app/*.log",
    job      = "fastapi",
    service  = "api",
  }]
}

// Read logs from discovered files
loki.source.file "app_logs" {
  targets    = local.file_match.app_logs.targets
  forward_to = [loki.process.app_logs.receiver]
}

// Process logs: parse JSON, extract labels
loki.process "app_logs" {
  forward_to = [loki.write.loki.receiver]

  // Parse JSON log format
  stage.json {
    expressions = {
      timestamp = "timestamp",
      level     = "level",
      message   = "message",
      logger    = "logger",
    }
  }

  // Extract labels from parsed fields
  stage.labels {
    values = {
      level  = "level",
      logger = "logger",
    }
  }

  // Output the message field
  stage.output {
    source = "message"
  }
}

// Optional: Docker container logs discovery
local.file_match "docker_logs" {
  path_targets = [{
    __path__ = "/var/lib/docker/containers/*/*-json.log",
    job      = "docker",
  }]
}

// Read Docker container logs
loki.source.file "docker_logs" {
  targets    = local.file_match.docker_logs.targets
  forward_to = [loki.process.docker_logs.receiver]
}

// Process Docker logs
loki.process "docker_logs" {
  forward_to = [loki.write.loki.receiver]

  // Parse Docker JSON log format
  stage.json {
    expressions = {
      output = "log",
      stream = "stream",
      attrs  = "attrs",
    }
  }

  // Extract container labels
  stage.labels {
    values = {
      stream = "stream",
    }
  }

  // Extract container name from path
  stage.regex {
    expression = ".*/(?P<container_id>[^/]+)-json\\.log$"
    source     = "__path__"
  }

  // Output the log message
  stage.output {
    source = "output"
  }
}
```

**Note on Grafana Alloy**:
- Alloy uses the River configuration language (not YAML)
- It's the recommended successor to Promtail
- Supports both logs and metrics collection
- More flexible and performant than Promtail
- Configuration is declarative and component-based

#### Sentry Integration (Optional)

**File: `app/core/sentry.py`** (if using Sentry)

```python
"""Sentry integration for error tracking."""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

sentry_sdk = None

def init_sentry():
    """Initialize Sentry if DSN is configured."""
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    
    if not sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ],
            traces_sample_rate=0.1,  # 10% of transactions
            environment=settings.ENVIRONMENT,
            release=settings.API_VERSION,
        )
        logger.info("Sentry initialized successfully")
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
```

**Add to `requirements.txt`** (optional):

```
sentry-sdk[fastapi]==2.19.0
```

**Add to `app/main.py`**:

```python
# Initialize Sentry if configured
if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
    from app.core.sentry import init_sentry
    init_sentry()
```

#### Using Monitoring Services

**Quick Start**:

1. **Start monitoring services**:
   ```bash
   docker compose -f docker-compose.monitoring.yml up -d
   ```

2. **Enable metrics in your API**:
   ```bash
   # In .env file
   ENABLE_METRICS=true
   ```

3. **Access services**:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001 (admin/admin)
   - Loki: http://localhost:3100
   - Alloy: http://localhost:12345 (health check and UI)
   - Sentry: http://localhost:9000 (if enabled)

4. **View metrics in Grafana**:
   - Login to Grafana (default: admin/admin)
   - Go to Configuration > Data Sources
   - Prometheus should be pre-configured
   - Import the FastAPI dashboard from `monitoring/grafana/dashboards/`

**Production Considerations**:

- Change default passwords for Grafana and Sentry
- Use environment variables for sensitive configuration
- Consider using external Prometheus/Grafana instances for production
- Set up alerting rules in Prometheus
- Configure log retention policies in Loki
- Use reverse proxy (nginx/traefik) for production access

#### Additional Monitoring Tools

**CrowdSec Integration** (Security/Threat Intelligence):

CrowdSec can be added as an optional service for threat detection and blocking.

**File: `docker-compose.monitoring.yml`** (add to services):

```yaml
  crowdsec:
    image: crowdsecurity/crowdsec:latest
    container_name: fastapi_crowdsec
    restart: unless-stopped
    volumes:
      - ./monitoring/crowdsec/config:/etc/crowdsec:ro
      - crowdsec_data:/var/lib/crowdsec/data
    environment:
      - COLLECTIONS=crowdsecurity/nginx
    networks:
      - monitoring
```

**OpenTelemetry Integration** (Alternative to Prometheus):

For teams preferring OpenTelemetry:

```python
# requirements.txt (optional)
opentelemetry-api==1.24.0
opentelemetry-sdk==1.24.0
opentelemetry-instrumentation-fastapi==0.45b0
opentelemetry-exporter-prometheus==1.24.0
```

**File: `app/core/otel.py`**:

```python
"""OpenTelemetry integration (optional alternative to Prometheus)."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def init_otel(app):
    """Initialize OpenTelemetry."""
    # Only if enabled
    if not getattr(settings, 'ENABLE_OTEL', False):
        return
    
    provider = TracerProvider()
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    FastAPIInstrumentor.instrument_app(app)
```

---

## Deployment

### Environment-Specific Configurations

- **Development**: Debug enabled, verbose logging, OpenAPI docs enabled
- **Staging**: Production-like, with additional logging
- **Production**: Optimized, minimal logging, security hardened

### Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] SSL/TLS certificates configured
- [ ] Rate limiting configured
- [ ] Monitoring and alerting setup
- [ ] Backup strategy in place
- [ ] Health checks configured
- [ ] Log aggregation setup
- [ ] Security scanning completed

---

## Minimal Functionality

The template includes only essential endpoints:

1. **GET /** - Minimal root endpoint (returns `{"status": "ok"}` only)
2. **GET /api/v1/health/** - Health check
3. **GET /api/v1/health/ready** - Readiness check (with DB)
4. **GET /api/v1/health/live** - Liveness check
5. **GET /api/v1/version/** - Version information

All other functionality (authentication, CRUD operations, etc.) should be added by developers based on their specific requirements.

---

## Summary

This template provides:

✅ **Complete Infrastructure**: Database, authentication, error handling, logging
✅ **Testing Framework**: Integration and unit test utilities ready to use
✅ **Docker Setup**: Production and test containers configured
✅ **CI/CD**: Automated testing and Docker builds
✅ **Security**: JWT auth, rate limiting, input validation
✅ **Metrics & Observability**: Prometheus metrics with optional Grafana, Loki, Sentry integration
✅ **Best Practices**: Code organization, error handling, logging patterns
✅ **Minimal Logic**: Only essential endpoints, ready for customization

Developers can fork this template and immediately start building their domain-specific functionality without worrying about infrastructure concerns.
