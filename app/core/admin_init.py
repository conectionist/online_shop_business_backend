"""Admin initialization module for creating default admin user on startup"""

import logging
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.admin import Admin
from app.core.config import settings

logger = logging.getLogger(__name__)


def initialize_default_admin():
    """
    Initialize the default admin user if it doesn't exist.
    
    This function is called on application startup to ensure there's always
    at least one admin user available for authentication.
    """
    try:
        # Get a database session
        db = next(get_db())
        
        # Check if admin with the configured username exists
        existing_admin = db.query(Admin).filter(Admin.username == settings.ADMIN_USERNAME).first()
        
        if existing_admin:
            logger.info(f"Default admin user '{settings.ADMIN_USERNAME}' already exists")
            return
        
        # Create the default admin user
        hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
        
        default_admin = Admin(
            username=settings.ADMIN_USERNAME,
            password=hashed_password
        )
        
        db.add(default_admin)
        db.commit()
        
        logger.info(f"Created default admin user '{settings.ADMIN_USERNAME}'")
        
    except Exception as e:
        logger.error(f"Failed to initialize default admin user: {str(e)}")
        raise
    finally:
        db.close() 