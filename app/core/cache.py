"""
Whole-response cache layer backed by Redis.

All public functions degrade gracefully: if Redis is unavailable they log a
warning and return a cache-miss / no-op so the request proceeds normally via
the database path.
"""

import json
import time
import logging
from datetime import date, datetime
from typing import Any

import redis as redis_lib

from app.core.redis import get_redis_client, disable_redis

logger = logging.getLogger(__name__)

# Key prefixes (include API version for safe future migrations)
_RESP_PREFIX = "cache:resp:v1"
_LOCK_PREFIX = "cache:lock:v1"

# Stampede lock defaults
_LOCK_TTL_SECONDS = 5
_LOCK_RETRY_ATTEMPTS = 3
_LOCK_RETRY_DELAY_SECONDS = 0.2


def _json_serializer(obj: Any) -> str:
    """Match FastAPI ``jsonable_encoder`` so cached JSON matches uncached responses."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ---------------------------------------------------------------------------
# Key builders
# ---------------------------------------------------------------------------

def build_cache_key(route_name: str, **params: Any) -> str:
    """
    Build a deterministic cache key.

    Examples:
        build_cache_key("list_products_ordered", list_id=12)
        -> "cache:resp:v1:list_products_ordered:list_id=12"
    """
    parts = [_RESP_PREFIX, route_name]
    for k, v in sorted(params.items()):
        parts.append(f"{k}={v}")
    return ":".join(parts)


# ---------------------------------------------------------------------------
# Get / set / delete
# ---------------------------------------------------------------------------

def get_cached_response(key: str) -> str | None:
    """
    Return the cached JSON string for *key*, or ``None`` on miss / error.
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        return client.get(key)
    except redis_lib.RedisError as exc:
        logger.warning("Redis GET error for %s: %s", key, exc)
        disable_redis(exc)
        return None


def set_cached_response(key: str, data: Any) -> None:
    """
    Serialize *data* to JSON and store it in Redis with no TTL.
    """
    client = get_redis_client()
    if client is None:
        return
    try:
        payload = json.dumps(data, default=_json_serializer, ensure_ascii=False)
        client.set(key, payload)
    except (TypeError, ValueError) as exc:
        # Serialization errors should not fail requests; just skip caching this payload.
        logger.warning("Cache serialization error for %s: %s", key, exc)
    except redis_lib.RedisError as exc:
        logger.warning("Redis SET error for %s: %s", key, exc)
        disable_redis(exc)


def delete_key(key: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.delete(key)
    except redis_lib.RedisError as exc:
        logger.warning("Redis DELETE error for %s: %s", key, exc)
        disable_redis(exc)


def _delete_by_pattern(pattern: str) -> int:
    """
    Delete all keys matching the glob *pattern* using SCAN (non-blocking).
    Returns the number of keys deleted.
    """
    client = get_redis_client()
    if client is None:
        return 0
    deleted = 0
    try:
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
    except redis_lib.RedisError as exc:
        logger.warning("Redis SCAN/DELETE error for pattern %s: %s", pattern, exc)
        disable_redis(exc)
    return deleted


# ---------------------------------------------------------------------------
# Stampede lock
# ---------------------------------------------------------------------------

def acquire_computation_lock(key: str, ttl: int = _LOCK_TTL_SECONDS) -> bool:
    """
    Try to acquire a short-lived lock for *key* to prevent thundering herd.
    Returns ``True`` if the lock was acquired.
    """
    client = get_redis_client()
    if client is None:
        return True  # no Redis → let request through
    lock_key = f"{_LOCK_PREFIX}:{key}"
    try:
        return bool(client.set(lock_key, "1", nx=True, ex=ttl))
    except redis_lib.RedisError as exc:
        logger.warning("Redis lock acquire error for %s: %s", lock_key, exc)
        disable_redis(exc)
        return True  # degrade: let request through


def release_computation_lock(key: str) -> None:
    lock_key = f"{_LOCK_PREFIX}:{key}"
    delete_key(lock_key)


def wait_for_cache(key: str) -> str | None:
    """
    Wait briefly for another worker to populate the cache (used when the
    stampede lock was NOT acquired).  Returns the cached value or None.
    """
    for _ in range(_LOCK_RETRY_ATTEMPTS):
        time.sleep(_LOCK_RETRY_DELAY_SECONDS)
        cached = get_cached_response(key)
        if cached is not None:
            return cached
    return None


# ---------------------------------------------------------------------------
# Domain-specific invalidation helpers
# ---------------------------------------------------------------------------

def invalidate_for_list(list_id: int) -> None:
    """Invalidate cached responses for list product endpoints."""
    n = _delete_by_pattern(f"{_RESP_PREFIX}:list_products_ordered:*list_id={list_id}*")
    n += _delete_by_pattern(f"{_RESP_PREFIX}:list_products:*list_id={list_id}*")
    if n:
        logger.info("Cache invalidated %d key(s) for list_id=%s", n, list_id)


def invalidate_for_product(product_id: int) -> None:
    """Invalidate caches containing product data (detail, list, and list endpoints that embed products)."""
    n = _delete_by_pattern(f"{_RESP_PREFIX}:product_detail:*product_id={product_id}*")
    n += _delete_by_pattern(f"{_RESP_PREFIX}:products_list:*")
    n += _delete_by_pattern(f"{_RESP_PREFIX}:list_products_ordered:*")
    n += _delete_by_pattern(f"{_RESP_PREFIX}:list_products:*")
    if n:
        logger.info("Cache invalidated %d key(s) for product_id=%s", n, product_id)


def invalidate_for_categories() -> None:
    """Invalidate all category caches and list endpoints that embed category data."""
    n = _delete_by_pattern(f"{_RESP_PREFIX}:categories_all:*")
    n += _delete_by_pattern(f"{_RESP_PREFIX}:category_detail:*")
    n += _delete_by_pattern(f"{_RESP_PREFIX}:list_products_ordered:*")
    if n:
        logger.info("Cache invalidated %d category key(s)", n)


def invalidate_for_reference_data(entity_name: str) -> None:
    """Invalidate cached reference-data responses for *entity_name*."""
    n = _delete_by_pattern(f"{_RESP_PREFIX}:{entity_name}_*")
    if n:
        logger.info("Cache invalidated %d key(s) for %s", n, entity_name)
