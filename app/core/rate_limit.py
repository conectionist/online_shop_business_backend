"""Rate limiting for the API (slowapi). Shared limiter instance for use in main and routers."""
import logging

from fastapi import Request
from slowapi import Limiter

logger = logging.getLogger(__name__)

_warned_about_untrusted_proxy = False


def _client_ip_key(request: Request) -> str:
    """The client's IP as Uvicorn resolved it.

    Uvicorn reads X-Forwarded-For only from the proxies in FORWARDED_ALLOW_IPS, so a
    client cannot pick its own rate-limit key by sending that header.
    """
    host = request.client.host if request.client else "unknown"
    _warn_once_if_proxy_untrusted(request, host)
    return host


def _warn_once_if_proxy_untrusted(request: Request, host: str) -> None:
    """Log when a request names a forwarded client that Uvicorn didn't use.

    From a proxy missing from FORWARDED_ALLOW_IPS, every customer has the proxy's
    address, so they all share one rate limit.
    """
    global _warned_about_untrusted_proxy
    if _warned_about_untrusted_proxy:
        return

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return

    # A trusted proxy's forwarded address replaces the peer's, so it is in the list.
    if host in {address.strip() for address in forwarded.split(",")}:
        return

    _warned_about_untrusted_proxy = True
    logger.warning(
        "A request from %s carried X-Forwarded-For, which Uvicorn did not use. If %s is "
        "your reverse proxy, add it to FORWARDED_ALLOW_IPS: until then all its clients "
        "share one rate limit.",
        host,
        host,
    )


limiter = Limiter(key_func=_client_ip_key)
