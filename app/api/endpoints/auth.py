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
from app.services.auth import (
    authenticate_admin,
    create_admin_tokens,
    refresh_access_token,
    get_current_admin_from_cookie,
    store_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
    verify_password,
    get_password_hash
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