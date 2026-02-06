"""Helpers and constants for authentication cookies.

This module centralizes cookie names and common options for access and
refresh token cookies. It does NOT change any endpoint behavior by itself;
endpoints will opt in to using these helpers in later roadmap steps.
"""

from typing import Any, Dict, Optional

from fastapi import Response

from app.core.config import settings


# Public cookie names for auth tokens
ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"


def _base_cookie_params(max_age: int) -> Dict[str, Any]:
    """Build base cookie parameters shared by auth cookies.

    The values are derived from environment-aware settings so we can
    adjust behavior (e.g. Secure, SameSite) from configuration.
    """
    params: Dict[str, Any] = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": settings.COOKIE_PATH,
        "max_age": max_age,
    }

    # Only set domain if configured; an empty string means "use default host".
    if settings.COOKIE_DOMAIN:
        params["domain"] = settings.COOKIE_DOMAIN

    return params


def get_access_cookie_params() -> Dict[str, Any]:
    """Return parameters for the access token cookie."""
    return _base_cookie_params(settings.ACCESS_TOKEN_COOKIE_MAX_AGE)


def get_refresh_cookie_params() -> Dict[str, Any]:
    """Return parameters for the refresh token cookie."""
    return _base_cookie_params(settings.REFRESH_TOKEN_COOKIE_MAX_AGE)


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    """Set access and refresh token cookies on the given response."""
    access_params = get_access_cookie_params()
    refresh_params = get_refresh_cookie_params()

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        **access_params,
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        **refresh_params,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear auth cookies on the given response.

    Uses the same path/domain attributes as the setters to ensure
    cookies are actually removed in the browser.
    """
    # Build base params without max_age, then override for clearing.
    access_params = get_access_cookie_params()
    refresh_params = get_refresh_cookie_params()

    # Ensure we clear regardless of current value.
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value="",
        max_age=0,
        **{k: v for k, v in access_params.items() if k not in {"max_age"}},
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value="",
        max_age=0,
        **{k: v for k, v in refresh_params.items() if k not in {"max_age"}},
    )

"""Helpers for setting and clearing authentication cookies.

These utilities centralize how access and refresh token cookies are managed,
using configuration from app.core.config.settings.
"""

from fastapi import Response

from app.core.config import settings


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set access and refresh token cookies on the response."""
    common_kwargs = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": settings.COOKIE_PATH,
    }
    if settings.COOKIE_DOMAIN:
        common_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_COOKIE_MAX_AGE,
        **common_kwargs,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
        **common_kwargs,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear access and refresh token cookies on the response."""
    common_kwargs = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": settings.COOKIE_PATH,
        "max_age": 0,
    }
    if settings.COOKIE_DOMAIN:
        common_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value="",
        **common_kwargs,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value="",
        **common_kwargs,
    )

