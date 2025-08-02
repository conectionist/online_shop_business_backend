"""Authentication service for admin users"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    is_token_expired
)
from app.core.config import settings
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminLogin, AdminResponse

# Security scheme for JWT tokens
security = HTTPBearer()


def authenticate_admin(db: Session, username: str, password: str) -> Optional[Admin]:
    """
    Authenticate an admin user with username and password.
    
    Args:
        db: Database session
        username: Admin username
        password: Admin password (plain text)
        
    Returns:
        Admin object if authentication successful, None otherwise
    """
    try:
        # Get admin by username
        admin = db.query(Admin).filter(Admin.username == username).first()
        
        if not admin:
            return None
            
        # Verify password
        if not verify_password(password, admin.password):
            return None
            
        return admin
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during authentication: {str(e)}"
        )


def create_admin(db: Session, admin: AdminCreate) -> Admin:
    """
    Create a new admin user.
    
    Args:
        db: Database session
        admin: Admin creation data
        
    Returns:
        Created Admin object
        
    Raises:
        HTTPException: If username already exists or database error occurs
    """
    try:
        # Check if username already exists
        existing_admin = db.query(Admin).filter(Admin.username == admin.username).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Admin with username '{admin.username}' already exists"
            )
        
        # Hash the password
        hashed_password = get_password_hash(admin.password)
        
        # Create new admin
        db_admin = Admin(
            username=admin.username,
            password=hashed_password
        )
        
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        
        return db_admin
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating admin: {str(e)}"
        )


def get_admin_by_id(db: Session, admin_id: int) -> Optional[Admin]:
    """
    Get admin by ID.
    
    Args:
        db: Database session
        admin_id: Admin ID
        
    Returns:
        Admin object if found, None otherwise
    """
    try:
        return db.query(Admin).filter(Admin.id == admin_id).first()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving admin: {str(e)}"
        )


def get_admin_by_username(db: Session, username: str) -> Optional[Admin]:
    """
    Get admin by username.
    
    Args:
        db: Database session
        username: Admin username
        
    Returns:
        Admin object if found, None otherwise
    """
    try:
        return db.query(Admin).filter(Admin.username == username).first()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving admin: {str(e)}"
        )


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """
    Get the current authenticated admin from JWT token.
    
    Args:
        credentials: JWT token from Authorization header
        db: Database session
        
    Returns:
        Admin object if token is valid
        
    Raises:
        HTTPException: If token is invalid, expired, or admin not found
    """
    try:
        # Verify the token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        # Check if token is expired
        if is_token_expired(credentials.credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Get admin ID from token
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get admin from database
        admin = get_admin_by_id(db, int(admin_id))
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found"
            )
        
        return admin
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}"
        )


def create_admin_tokens(admin: Admin) -> dict:
    """
    Create access and refresh tokens for an admin.
    
    Args:
        admin: Admin object
        
    Returns:
        Dictionary with access_token, refresh_token, and token_type
    """
    # Create token payload
    token_data = {
        "sub": str(admin.id),
        "username": admin.username,
        "type": "access"
    }
    
    refresh_data = {
        "sub": str(admin.id),
        "username": admin.username,
        "type": "refresh"
    }
    
    # Create tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(refresh_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "admin": AdminResponse(
            id=admin.id,
            username=admin.username,
            created_at=admin.created_at,
            updated_at=admin.updated_at
        )
    }


def refresh_access_token(refresh_token: str, db: Session) -> dict:
    """
    Refresh an access token using a refresh token.
    
    Args:
        refresh_token: Refresh token
        db: Database session
        
    Returns:
        Dictionary with new access_token and token_type
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Check if token is expired
        if is_token_expired(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        
        # Get admin ID from token
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get admin from database
        admin = get_admin_by_id(db, int(admin_id))
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found"
            )
        
        # Create new access token
        token_data = {
            "sub": str(admin.id),
            "username": admin.username,
            "type": "access"
        }
        
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh error: {str(e)}"
        ) 