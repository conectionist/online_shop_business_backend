"""Rate limiting for the API (slowapi). Shared limiter instance for use in main and routers."""
from fastapi import Request
from slowapi import Limiter


def _order_rate_limit_key(request: Request) -> str:
    """Client IP for rate limiting: X-Forwarded-For (first element) if present, else request.client.host."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return request.scope.get("client", ("unknown",))[0]


limiter = Limiter(key_func=_order_rate_limit_key)
