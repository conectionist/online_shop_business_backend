"""Database connection module for SQLAlchemy integration"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database connection details from environment variables with explicit error handling
def get_env_var(var_name):
    """Get an environment variable or raise an exception if it's not set"""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set")
    return value

# Get required environment variables with no fallbacks
try:
    DB_HOST = get_env_var("DB_HOST")
    DB_PORT = get_env_var("DB_PORT")
    DB_USER = get_env_var("DB_USER")
    DB_PASSWORD = get_env_var("DB_PASSWORD")
    DB_NAME = get_env_var("DB_NAME")
except ValueError as e:
    # Log the error and re-raise to prevent silent failures
    print(f"ERROR: {e}")
    print("Make sure all required environment variables are set before starting the application")
    raise

# Create database URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine with explicit pooling tuned for low idle + bursts
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=10,
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Database dependency to use in FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
