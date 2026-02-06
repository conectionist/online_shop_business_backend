"""Authentication endpoints for admin login and token management"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response
from uuid import uuid4
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.auth_cookies import set_auth_cookies
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    AdminInfo,
    PasswordChangeRequest,
    PasswordChangeResponse
)
from app.schemas.admin import AdminCreate, AdminResponse
from app.services.auth import (
    authenticate_admin,
    create_admin_tokens,
    refresh_access_token,
    get_current_admin,
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
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800
                }
            }
        }
    },
    401: {"description": "Invalid or expired refresh token"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh an access token using a refresh token.
    
    This endpoint allows getting a new access token using a valid refresh token.
    This is useful when the access token expires but the refresh token is still valid.
    
    The new access token will have the same expiration time as the original.
    """
    try:
        # Refresh the access token
        tokens = refresh_access_token(refresh_data.refresh_token, db)
        
        return TokenRefreshResponse(
            access_token=tokens["access_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
        )


# @router.post("/create-admin", response_model=AdminResponse, status_code=status.HTTP_201_CREATED, responses={
#     201: {
#         "description": "Admin user created successfully",
#         "content": {
#             "application/json": {
#                 "example": {
#                     "id": 2,
#                     "username": "newadmin"
#                 }
#             }
#         }
#     },
#     409: {"description": "Admin with this username already exists"},
#     422: {"description": "Validation error"},
#     500: {"description": "Internal server error"}
# })
# def create_admin_user(
#     admin_data: AdminCreate,
#     current_admin: Admin = Depends(get_current_admin),
#     db: Session = Depends(get_db)
# ):
#     """
#     Create a new admin user (admin only).
#     
#     This endpoint allows existing admins to create new admin users.
#     Only authenticated admin users can access this endpoint.
#     
#     The password will be securely hashed before storage.
#     If the username already exists, the request will fail with a 409 Conflict error.
#     """
#     try:
#         # Create the admin user
#         admin = create_admin(db, admin_data)
#         
#         return AdminResponse(
#             id=admin.id,
#             username=admin.username
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Admin creation error: {str(e)}"
#         )


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
    current_admin: Admin = Depends(get_current_admin),
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
        db.commit()
        
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