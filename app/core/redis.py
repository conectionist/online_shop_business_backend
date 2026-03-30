"""Redis connection management for response caching.

Simple behavior by design:
- If Redis is available, use it.
- If Redis is unavailable (startup or runtime), disable it and fall back to DB.
- If Redis comes back, retry connection periodically and resume cache usage.
"""

import logging
import socket
import time
import redis

from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_DB

logger = logging.getLogger(__name__)

# Short timeouts so a dead Redis fails fast (<<1 s per operation).
# These apply to the TCP connection/socket phase (after DNS, which we avoid
# by pre-resolving to an IP in init_redis).
_SOCKET_CONNECT_TIMEOUT = 0.3   # seconds
_SOCKET_TIMEOUT = 0.2           # seconds
_RECONNECT_INTERVAL_SECONDS = 30

_redis_client: redis.Redis | None = None
_redis_disabled_logged = False
_last_reconnect_attempt_monotonic = 0.0
_resolved_redis_host: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_host(host: str) -> str:
    """Resolve *host* to its IPv4 address once at startup.

    Using an IP avoids the OS-level DNS timeout on every failed Redis call
    when the Redis container is stopped (Docker removes the DNS entry but the
    OS resolver still waits the full timeout for each query).
    """
    try:
        ip = socket.gethostbyname(host)
        if ip != host:
            logger.debug("Redis: resolved hostname %s -> %s", host, ip)
        return ip
    except OSError:
        # Resolution failed at startup (e.g. Redis not running yet in test);
        # fall back to the original hostname.
        return host


def disable_redis(reason: Exception | str) -> None:
    """Disable Redis for this worker and fall back to DB path."""
    global _redis_client, _redis_disabled_logged
    if _redis_client is not None:
        try:
            _redis_client.close()
        except redis.RedisError:
            pass
        finally:
            _redis_client = None
    if not _redis_disabled_logged:
        logger.warning(
            "Redis disabled at runtime (%s). Falling back to DB-only path until restart.",
            reason,
        )
        _redis_disabled_logged = True


def _build_client() -> redis.Redis:
    """Create a Redis client with current settings."""
    host = _resolved_redis_host or REDIS_HOST
    return redis.Redis(
        host=host,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=_SOCKET_CONNECT_TIMEOUT,
        socket_timeout=_SOCKET_TIMEOUT,
        retry_on_timeout=False,
    )


def _try_reconnect_if_due() -> None:
    """Attempt reconnect at most once per interval while disabled."""
    global _redis_client, _redis_disabled_logged, _last_reconnect_attempt_monotonic
    now = time.monotonic()
    if now - _last_reconnect_attempt_monotonic < _RECONNECT_INTERVAL_SECONDS:
        return
    _last_reconnect_attempt_monotonic = now

    client = _build_client()
    try:
        client.ping()
        _redis_client = client
        _redis_disabled_logged = False
        logger.info("Redis reconnected successfully; cache resumed.")
    except redis.RedisError:
        # Keep quiet between attempts; Redis errors are already logged at disable time.
        _redis_client = None


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def init_redis() -> None:
    """Initialize the Redis connection pool and verify connectivity."""
    global _redis_client, _redis_disabled_logged, _resolved_redis_host, _last_reconnect_attempt_monotonic
    _redis_disabled_logged = False
    _last_reconnect_attempt_monotonic = 0.0
    _resolved_redis_host = _resolve_host(REDIS_HOST)
    _redis_client = _build_client()
    try:
        _redis_client.ping()
        logger.info(
            "Redis connected at %s (%s:%s) db=%s",
            REDIS_HOST, _resolved_redis_host, REDIS_PORT, REDIS_DB,
        )
    except redis.RedisError as exc:
        logger.warning(
            "Redis unavailable at startup (%s:%s): %s — caching disabled",
            _resolved_redis_host, REDIS_PORT, exc,
        )
        _redis_client = None


def close_redis() -> None:
    """Close the Redis connection pool on shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except redis.RedisError as exc:
            logger.warning("Error closing Redis connection: %s", exc)
        finally:
            _redis_client = None


def get_redis_client() -> redis.Redis | None:
    """Return active Redis client, retrying periodically when unavailable."""
    if _redis_client is None:
        _try_reconnect_if_due()
    return _redis_client
