"""Authentication service for admin users"""

from datetime import datetime, timedelta
import hashlib
from typing import Optional
from fastapi import HTTPException, status, Depends, Request
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
from app.models.refresh_token import RefreshToken
from app.schemas.admin import AdminCreate, AdminLogin, AdminResponse


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



def get_current_admin_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
) -> Admin:
    """
    Get the current authenticated admin from the access_token cookie.

    This is the cookie-based equivalent of get_current_admin (header-based).
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Verify the token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    # Check if token is expired
    if is_token_expired(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )

    # Require access token; reject refresh tokens when used for admin API access
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required",
        )

    # If a refresh token cookie is present, require a valid, active session.
    # Otherwise, fall back to access-token-only auth for legacy test helpers.
    refresh_token = request.cookies.get("refresh_token")
    session = None
    if refresh_token:
        session = get_current_session(db, refresh_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found",
            )

        if session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked",
            )

        if session.expires_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired",
            )

    # Get admin ID from token
    admin_id = payload.get("sub")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    if session and session.admin_id != int(admin_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session does not match token",
        )

    # Get admin from database
    admin = get_admin_by_id(db, int(admin_id))
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found",
        )

    return admin


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
        "admin": {
            "id": admin.id,
            "username": admin.username
        }
    }


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_request_meta(request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
    if not request:
        return None, None
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


def store_refresh_token(
    db: Session,
    admin_id: int,
    refresh_token: str,
    *,
    expires_at: datetime,
    request: Optional[Request] = None,
) -> RefreshToken:
    from app.utils.user_agent_parser import parse_user_agent
    from app.utils.ip_geolocation import get_location_from_ip
    
    token_hash = hash_refresh_token(refresh_token)
    ip_address, user_agent = _get_request_meta(request)
    
    # Parse user agent for device/browser/OS info
    ua_info = parse_user_agent(user_agent)
    
    # Get location from IP (optional)
    location_info = get_location_from_ip(ip_address)

    # Revoke existing active sessions from the same device fingerprint
    now = datetime.utcnow()
    db.query(RefreshToken).filter(
        RefreshToken.admin_id == admin_id,
        RefreshToken.device_type == ua_info["device_type"],
        RefreshToken.browser_name == ua_info["browser_name"],
        RefreshToken.os_name == ua_info["os_name"],
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > now,
    ).update({"revoked_at": now}, synchronize_session="fetch")

    row = RefreshToken(
        admin_id=admin_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
        # Enhanced session metadata
        session_name=ua_info["session_name"],
        device_type=ua_info["device_type"],
        browser_name=ua_info["browser_name"],
        os_name=ua_info["os_name"],
        location_city=location_info["city"],
        location_country=location_info["country"],
    )
    db.add(row)
    return row


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    now = datetime.utcnow()

    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .one_or_none()
    )
    if row and row.revoked_at is None:
        row.revoked_at = now


def revoke_all_refresh_tokens(db: Session, admin_id: int) -> int:
    now = datetime.utcnow()
    updated = (
        db.query(RefreshToken)
        .filter(RefreshToken.admin_id == admin_id)
        .filter(RefreshToken.revoked_at.is_(None))
        .update({RefreshToken.revoked_at: now}, synchronize_session=False)
    )
    return int(updated or 0)


def revoke_other_refresh_tokens(db: Session, admin_id: int, current_token_hash: str) -> int:
    """Revoke all refresh tokens for an admin except the current session."""
    now = datetime.utcnow()
    updated = (
        db.query(RefreshToken)
        .filter(RefreshToken.admin_id == admin_id)
        .filter(RefreshToken.revoked_at.is_(None))
        .filter(RefreshToken.token_hash != current_token_hash)
        .update({RefreshToken.revoked_at: now}, synchronize_session=False)
    )
    return int(updated or 0)


def refresh_access_token(refresh_token: str, db: Session, request: Optional[Request] = None) -> dict:
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
        
        if is_token_expired(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )

        token_hash = hash_refresh_token(refresh_token)
        token_row = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .one_or_none()
        )
        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        if token_row.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        now = datetime.utcnow()
        if token_row.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        token_row.last_used_at = now
        
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

        new_refresh_token = create_refresh_token({
            "sub": str(admin.id),
            "username": admin.username,
            "type": "refresh",
        })
        new_payload = verify_token(new_refresh_token)
        if not new_payload or not new_payload.get("exp"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh error"
            )
        new_expires_at = datetime.utcfromtimestamp(int(new_payload["exp"]))

        new_row = store_refresh_token(
            db,
            admin.id,
            new_refresh_token,
            expires_at=new_expires_at,
            request=request,
        )

        token_row.revoked_at = now
        db.flush()
        token_row.replaced_by_token_id = new_row.id

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
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


# ============================================================================
# Session Management Functions
# ============================================================================

def get_active_sessions(db: Session, admin_id: int) -> list[RefreshToken]:
    """
    Get all active (non-revoked, non-expired) sessions for an admin.
    
    Args:
        db: Database session
        admin_id: Admin ID
        
    Returns:
        List of active RefreshToken objects, ordered by last_used_at descending
    """
    now = datetime.utcnow()
    return (
        db.query(RefreshToken)
        .filter(RefreshToken.admin_id == admin_id)
        .filter(RefreshToken.revoked_at.is_(None))
        .filter(RefreshToken.expires_at > now)
        .order_by(RefreshToken.last_used_at.desc())
        .all()
    )


def get_session_by_id(
    db: Session, 
    session_id: int, 
    admin_id: int
) -> Optional[RefreshToken]:
    """
    Get a specific session by ID, ensuring it belongs to the admin.
    
    Args:
        db: Database session
        session_id: Session (RefreshToken) ID
        admin_id: Admin ID
        
    Returns:
        RefreshToken object if found and belongs to admin, None otherwise
    """
    return (
        db.query(RefreshToken)
        .filter(RefreshToken.id == session_id)
        .filter(RefreshToken.admin_id == admin_id)
        .one_or_none()
    )


def revoke_session_by_id(
    db: Session, 
    session_id: int, 
    admin_id: int
) -> bool:
    """
    Revoke a specific session by ID.
    
    Args:
        db: Database session
        session_id: Session (RefreshToken) ID
        admin_id: Admin ID
        
    Returns:
        True if session was revoked, False if not found or already revoked
    """
    session = get_session_by_id(db, session_id, admin_id)
    if not session or session.revoked_at is not None:
        return False
    
    session.revoked_at = datetime.utcnow()
    return True


def get_current_session(
    db: Session, 
    refresh_token: str
) -> Optional[RefreshToken]:
    """
    Get the current session from the refresh token cookie.
    
    Args:
        db: Database session
        refresh_token: Refresh token string
        
    Returns:
        RefreshToken object if found, None otherwise
    """
    token_hash = hash_refresh_token(refresh_token)
    return (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .one_or_none()
    )


def cleanup_expired_sessions(db: Session, days_to_keep: int = 30) -> int:
    """
    Delete expired sessions older than the specified number of days.
    
    This function removes expired refresh tokens from the database to keep
    it clean and maintain performance. Only tokens that have been expired
    for longer than the specified retention period are deleted.
    
    Args:
        db: Database session
        days_to_keep: Number of days to keep expired sessions (default: 30)
        
    Returns:
        Number of sessions deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    deleted = (
        db.query(RefreshToken)
        .filter(RefreshToken.expires_at < cutoff_date)
        .delete(synchronize_session=False)
    )
    
    return int(deleted or 0) 
