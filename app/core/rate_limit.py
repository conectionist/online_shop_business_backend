"""Rate limiting for the API (slowapi). Shared limiter instance for use in main and routers."""
import logging
from time import monotonic

from fastapi import Request
from slowapi import Limiter

logger = logging.getLogger(__name__)

# Repeated rather than logged once, so one stray direct request can't use it up.
_UNTRUSTED_PROXY_WARNING_INTERVAL_SECONDS = 60 * 60
_last_untrusted_proxy_warning: float | None = None


def _client_ip_key(request: Request) -> str:
    """The client's IP as Uvicorn resolved it.

    Uvicorn reads X-Forwarded-For only from the proxies in FORWARDED_ALLOW_IPS, so a
    client cannot pick its own rate-limit key by sending that header (unless
    FORWARDED_ALLOW_IPS is "*", which trusts everyone).
    """
    host = request.client.host if request.client else "unknown"
    _warn_if_proxy_untrusted(request, host)
    return host


def _warn_if_proxy_untrusted(request: Request, host: str) -> None:
    """Log, at most hourly, a request naming a forwarded client that Uvicorn didn't use.

    From a proxy missing from FORWARDED_ALLOW_IPS, every customer has the proxy's
    address, so they all share one rate limit.
    """
    global _last_untrusted_proxy_warning
    now = monotonic()
    if (
        _last_untrusted_proxy_warning is not None
        and now - _last_untrusted_proxy_warning < _UNTRUSTED_PROXY_WARNING_INTERVAL_SECONDS
    ):
        return

    # Every header line: a proxy may add its own line after one the client sent.
    forwarded = {
        address.strip()
        for line in request.headers.getlist("x-forwarded-for")
        for address in line.split(",")
        if address.strip()
    }
    if not forwarded:
        return

    # A trusted proxy's forwarded address replaces the peer's, so it is in the list.
    if host in forwarded:
        return

    _last_untrusted_proxy_warning = now
    logger.warning(
        "A request from %s carried X-Forwarded-For, which Uvicorn did not use. If %s is "
        "your reverse proxy, add it to FORWARDED_ALLOW_IPS: until then all its clients "
        "share one rate limit.",
        host,
        host,
    )


limiter = Limiter(key_func=_client_ip_key)
