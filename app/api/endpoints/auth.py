"""Authentication endpoints for admin login and token management"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response
from uuid import uuid4
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.auth_cookies import set_auth_cookies, clear_auth_cookies
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    AdminInfo,
    PasswordChangeRequest,
    PasswordChangeResponse,
    LogoutResponse
)
from app.schemas.admin import AdminCreate, AdminResponse
from app.schemas.session import SessionInfo, SessionListResponse, SessionRevokeResponse
from app.services.auth import (
    authenticate_admin,
    create_admin_tokens,
    refresh_access_token,
    get_current_admin_from_cookie,
    store_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
    revoke_other_refresh_tokens,
    verify_password,
    get_password_hash,
    hash_refresh_token,
    get_active_sessions,
    get_session_by_id,
    revoke_session_by_id,
    get_current_session
)
from app.models.admin import Admin

router = APIRouter()


@router.post("/login", response_model=LoginResponse, responses={
    200: {
        "description": "Login successful",
        "content": {
            "application/json": {
                "example": {
                    "expires_in": 1800,
                    "admin": {
                        "id": 1,
                        "username": "admin"
                    },
                    "note": "Auth tokens are returned via httpOnly cookies, not in this JSON body."
                }
            }
        }
    },
    429: {"description": "Too many login attempts from this IP; try again later"},
    401: {"description": "Invalid credentials"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
@limiter.limit(settings.LOGIN_RATE_LIMIT_STRING)
def login(
    request: Request,
    login_data: LoginRequest,
    background: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate an admin user with username and password.

    On successful authentication, this endpoint:
    - Issues access and refresh JWTs using the existing token helpers.
    - Stores those tokens in secure httpOnly cookies on the response.
    - Returns admin information (and optional metadata) in the JSON body,
      without exposing the raw tokens.
    """
    try:
        # Authenticate the admin
        admin = authenticate_admin(db, login_data.username, login_data.password)
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create tokens
        tokens = create_admin_tokens(admin)

        refresh_payload = None
        try:
            from app.core.security import verify_token
            refresh_payload = verify_token(tokens["refresh_token"])
        except Exception:
            refresh_payload = None

        if not refresh_payload or not refresh_payload.get("exp"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login error: Failed to create refresh token"
            )

        from datetime import datetime
        refresh_expires_at = datetime.utcfromtimestamp(int(refresh_payload["exp"]))

        store_refresh_token(
            db,
            admin.id,
            tokens["refresh_token"],
            expires_at=refresh_expires_at,
            request=request,
        )
        db.commit()

        # Set auth cookies (access + refresh) on the response
        set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])

        # Fire-and-forget: notify admins subscribed to admin_login topic
        def _notify_admin_login(admin_id: int, admin_username: str):
            try:
                from app.core.database import SessionLocal
                from app.services.push_notifications import send_to_subscriptions_by_topic
                session = SessionLocal()
                try:
                    login_uid = uuid4().hex
                    payload = {
                        "title": "Admin Login",
                        "body": f"Admin '{admin_username}' has logged in",
                        "data": {
                            "type": "admin_login",
                            "admin_id": admin_id,
                            "admin_username": admin_username
                        },
                        "tag": f"admin_login_{admin_id}_{login_uid}"
                    }
                    send_to_subscriptions_by_topic(
                        session,
                        "admin_login",
                        payload,
                        event_id=f"admin_login_{admin_id}_{login_uid}"
                    )
                finally:
                    session.close()
            except Exception:
                # Best-effort; do not fail login on notification issues
                pass

        background.add_task(_notify_admin_login, admin.id, admin.username)

        # Return admin info and metadata only; tokens are delivered via cookies
        return LoginResponse(
            expires_in=tokens["expires_in"],
            admin=tokens["admin"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/refresh", response_model=TokenRefreshResponse, responses={
    200: {
        "description": "Token refreshed successfully",
        "content": {
            "application/json": {
                "example": {
                    "expires_in": 1800,
                    "note": "Auth tokens are returned via httpOnly cookies, not in this JSON body."
                }
            }
        }
    },
    401: {"description": "Invalid, missing, or expired refresh token"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def refresh_token(
    refresh_data: TokenRefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh an access token using the refresh token stored in cookies.

    This endpoint:
    - Reads the refresh token from the httpOnly `refresh_token` cookie.
    - Uses existing refresh logic to validate and issue a new access token.
    - Updates auth cookies on success.
    - Returns only metadata (e.g. expires_in) in the JSON body, without raw tokens.
    """
    try:
        # Read refresh token from cookies
        refresh_token_cookie = request.cookies.get("refresh_token")
        if not refresh_token_cookie:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing refresh token cookie"
            )

        # Refresh the access token using the cookie value
        tokens = refresh_access_token(refresh_token_cookie, db, request=request)

        db.commit()

        # Update auth cookies (access + optionally refresh) on the response
        # If refresh_access_token does not rotate the refresh token, keep the
        # existing cookie value; otherwise, prefer the new one.
        new_refresh_token = tokens.get("refresh_token", refresh_token_cookie)
        set_auth_cookies(response, tokens["access_token"], new_refresh_token)

        return TokenRefreshResponse(
            expires_in=tokens["expires_in"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
        )


@router.get(
    "/me",
    response_model=AdminInfo,
    responses={
        200: {
            "description": "Current authenticated admin",
            "content": {
                "application/json": {
                    "example": {"id": 1, "username": "admin"},
                }
            },
        },
        401: {"description": "Not authenticated or token invalid"},
    },
)
def get_me(current_admin: Admin = Depends(get_current_admin_from_cookie)):
    """Return the currently authenticated admin based on the access_token cookie."""
    return {"id": current_admin.id, "username": current_admin.username}

@router.post("/change-password", response_model=PasswordChangeResponse, responses={
    200: {
        "description": "Password changed successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Password changed successfully"
                }
            }
        }
    },
    400: {"description": "Invalid current password"},
    401: {"description": "Unauthorized"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def change_password(
    password_data: PasswordChangeRequest,
    response: Response,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Change the current admin's password.
    
    This endpoint allows an authenticated admin to change their own password.
    The admin must provide their current password for verification.
    Only the authenticated admin can change their own password.
    """
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_admin.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        # Hash the new password
        new_hashed_password = get_password_hash(password_data.new_password)
        
        # Update the admin's password
        current_admin.password = new_hashed_password
        revoke_all_refresh_tokens(db, current_admin.id)
        db.commit()

        clear_auth_cookies(response)
        
        return PasswordChangeResponse(
            message="Password changed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change error: {str(e)}"
        ) 


@router.post("/logout", response_model=LogoutResponse, responses={
    200: {
        "description": "Logout successful",
        "content": {
            "application/json": {
                "example": {
                    "message": "Logged out successfully"
                }
            }
        }
    },
    401: {"description": "Not authenticated"},
    500: {"description": "Internal server error"}
})
def logout(
    response: Response,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db),
):
    """
    Logout the current admin user by clearing authentication cookies.
    
    This endpoint:
    - Clears both access_token and refresh_token cookies
    - Returns a success message
    - Requires valid authentication (cookies must be present)
    """
    try:
        refresh_token_cookie = request.cookies.get("refresh_token")
        if refresh_token_cookie:
            revoke_refresh_token(db, refresh_token_cookie)
            db.commit()

        # Clear auth cookies (access + refresh) on the response
        clear_auth_cookies(response)
        
        return LogoutResponse(
            message="Logged out successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}"
        ) 


@router.post("/logout-all", response_model=LogoutResponse, responses={
    200: {
        "description": "Logout all devices successful",
        "content": {
            "application/json": {
                "example": {
                    "message": "Logged out from all devices successfully"
                }
            }
        }
    },
    401: {"description": "Not authenticated"},
    500: {"description": "Internal server error"}
})
def logout_all(
    response: Response,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db),
):
    try:
        revoke_all_refresh_tokens(db, current_admin.id)
        db.commit()

        clear_auth_cookies(response)

        return LogoutResponse(message="Logged out from all devices successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout-all error: {str(e)}"
        )


@router.post("/logout-others", response_model=LogoutResponse, responses={
    200: {
        "description": "Logged out from all other devices",
        "content": {
            "application/json": {
                "example": {
                    "message": "Logged out from 2 other device(s)"
                }
            }
        }
    },
    401: {"description": "Not authenticated"},
    500: {"description": "Internal server error"}
})
def logout_others(
    request: Request,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db),
):
    """
    Logout from all other devices except the current one.

    This endpoint:
    - Revokes all refresh tokens except the one belonging to the current session
    - Keeps the current session alive (no cookies are cleared)
    - Returns a success message with the number of revoked sessions
    """
    try:
        refresh_token_cookie = request.cookies.get("refresh_token")
        if not refresh_token_cookie:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing refresh token cookie"
            )

        current_token_hash = hash_refresh_token(refresh_token_cookie)
        revoked_count = revoke_other_refresh_tokens(db, current_admin.id, current_token_hash)
        db.commit()

        return LogoutResponse(message=f"Logged out from {revoked_count} other device(s)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout-others error: {str(e)}"
        )


# ============================================================================
# Session Management Endpoints
# ============================================================================

@router.get(
    "/sessions",
    response_model=SessionListResponse,
    responses={
        200: {
            "description": "List of active sessions",
            "content": {
                "application/json": {
                    "example": {
                        "sessions": [
                            {
                                "id": 123,
                                "session_name": "Chrome on macOS",
                                "device_type": "desktop",
                                "browser_name": "Chrome",
                                "os_name": "macOS",
                                "ip_address": "192.168.1.100",
                                "location_city": None,
                                "location_country": None,
                                "created_at": "2026-02-07T10:00:00Z",
                                "last_used_at": "2026-02-07T11:00:00Z",
                                "expires_at": "2026-02-14T10:00:00Z",
                                "is_current": True
                            }
                        ],
                        "total": 1
                    }
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def list_sessions(
    request: Request,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    List all active sessions for the current admin.
    
    Returns all non-revoked, non-expired sessions with metadata.
    The current session (based on the refresh token cookie) is marked with is_current=True.
    """
    try:
        # Get all active sessions
        sessions = get_active_sessions(db, current_admin.id)
        
        # Get current session token hash to mark current session
        current_refresh_token = request.cookies.get("refresh_token")
        current_token_hash = hash_refresh_token(current_refresh_token) if current_refresh_token else None
        
        # Build response
        session_list = []
        for session in sessions:
            session_info = SessionInfo(
                id=session.id,
                session_name=session.session_name or "Unknown Device",
                device_type=session.device_type or "unknown",
                browser_name=session.browser_name or "unknown",
                os_name=session.os_name or "unknown",
                ip_address=session.ip_address,
                location_city=session.location_city,
                location_country=session.location_country,
                created_at=session.created_at,
                last_used_at=session.last_used_at,
                expires_at=session.expires_at,
                is_current=(session.token_hash == current_token_hash)
            )
            session_list.append(session_info)
        
        return SessionListResponse(
            sessions=session_list,
            total=len(session_list)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sessions: {str(e)}"
        )


@router.get(
    "/sessions/current",
    response_model=SessionInfo,
    responses={
        200: {"description": "Current session details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Current session not found"}
    }
)
def get_current_session_details(
    request: Request,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get details of the current session.
    
    Returns metadata about the session associated with the current refresh token.
    """
    try:
        # Get current refresh token from cookie
        current_refresh_token = request.cookies.get("refresh_token")
        if not current_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No active session"
            )
        
        # Get session from database
        session = get_current_session(db, current_refresh_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current session not found"
            )
        
        # Verify session belongs to current admin
        if session.admin_id != current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to current admin"
            )
        
        return SessionInfo(
            id=session.id,
            session_name=session.session_name or "Unknown Device",
            device_type=session.device_type or "unknown",
            browser_name=session.browser_name or "unknown",
            os_name=session.os_name or "unknown",
            ip_address=session.ip_address,
            location_city=session.location_city,
            location_country=session.location_country,
            created_at=session.created_at,
            last_used_at=session.last_used_at,
            expires_at=session.expires_at,
            is_current=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting current session: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionInfo,
    responses={
        200: {"description": "Session details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
def get_session_details(
    session_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific session by ID.
    
    Only returns sessions belonging to the current admin.
    """
    try:
        # Get session from database
        session = get_session_by_id(db, session_id, current_admin.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if this is the current session
        current_refresh_token = request.cookies.get("refresh_token")
        current_token_hash = hash_refresh_token(current_refresh_token) if current_refresh_token else None
        is_current = (session.token_hash == current_token_hash)
        
        return SessionInfo(
            id=session.id,
            session_name=session.session_name or "Unknown Device",
            device_type=session.device_type or "unknown",
            browser_name=session.browser_name or "unknown",
            os_name=session.os_name or "unknown",
            ip_address=session.ip_address,
            location_city=session.location_city,
            location_country=session.location_country,
            created_at=session.created_at,
            last_used_at=session.last_used_at,
            expires_at=session.expires_at,
            is_current=is_current
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting session: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=SessionRevokeResponse,
    responses={
        200: {"description": "Session revoked successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"},
        400: {"description": "Cannot revoke current session (use /auth/logout instead)"}
    }
)
def revoke_session(
    session_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session by ID (logout that device).
    
    This endpoint allows an admin to remotely logout from another device.
    To logout from the current device, use POST /auth/logout instead.
    """
    try:
        # Get session from database
        session = get_session_by_id(db, session_id, current_admin.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if trying to revoke current session
        current_refresh_token = request.cookies.get("refresh_token")
        if current_refresh_token:
            current_token_hash = hash_refresh_token(current_refresh_token)
            if session.token_hash == current_token_hash:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot revoke current session. Use POST /auth/logout instead."
                )
        
        # Revoke the session
        success = revoke_session_by_id(db, session_id, current_admin.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already revoked"
            )
        
        db.commit()
        
        return SessionRevokeResponse(
            message="Session revoked successfully",
            session_id=session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking session: {str(e)}"
        )