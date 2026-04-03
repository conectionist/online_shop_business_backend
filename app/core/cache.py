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
from app.core.metrics import (
    record_cache_invalidation,
    record_cache_lookup,
    record_cache_set,
)

logger = logging.getLogger(__name__)

# Key prefixes (include API version for safe future migrations)
_RESP_PREFIX = "cache:resp:v1"
_LOCK_PREFIX = "cache:lock:v1"
_IMGVER_PREFIX = "cache:imgver:v1"

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


def build_image_versions_key(image_path: str) -> str:
    """Redis key for cached ``image_versions`` dict for a storage path."""
    return f"{_IMGVER_PREFIX}:{image_path}"


# ---------------------------------------------------------------------------
# Image version cache (per-path dict, invalidated on image writes)
# ---------------------------------------------------------------------------


def get_cached_image_versions(image_path: str) -> dict[str, str] | None:
    """
    Return cached ``{original, medium, thumbnail}`` for *image_path*, or None on miss/error.
    """
    if not image_path:
        return None
    key = build_image_versions_key(image_path)
    raw = get_cached_response(key)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        o, m, t = data.get("original"), data.get("medium"), data.get("thumbnail")
        if not all(isinstance(x, str) for x in (o, m, t)):
            return None
        return {"original": o, "medium": m, "thumbnail": t}
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in image_versions cache for %s", key)
        delete_key(key)
        return None


def set_cached_image_versions(image_path: str, versions: dict[str, str]) -> None:
    """Store resolved image versions under *image_path* (no TTL; invalidated explicitly)."""
    if not image_path:
        return
    key = build_image_versions_key(image_path)
    set_cached_response(key, versions)


def invalidate_image_versions_path(image_path: str | None) -> None:
    """Remove cached image versions for *image_path* if set."""
    if not image_path or not str(image_path).strip():
        return
    delete_key(build_image_versions_key(image_path.strip()))


# ---------------------------------------------------------------------------
# Get / set / delete
# ---------------------------------------------------------------------------

def get_cached_response(key: str) -> str | None:
    """
    Return the cached JSON string for *key*, or ``None`` on miss / error.
    """
    client = get_redis_client()
    if client is None:
        record_cache_lookup(key, "bypass")
        return None
    try:
        cached = client.get(key)
        if cached is None:
            record_cache_lookup(key, "miss")
        else:
            record_cache_lookup(key, "hit")
        return cached
    except redis_lib.RedisError as exc:
        record_cache_lookup(key, "error")
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
        record_cache_set(key)
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
    n_ordered = _delete_by_pattern(f"{_RESP_PREFIX}:list_products_ordered:*list_id={list_id}*")
    n_list = _delete_by_pattern(f"{_RESP_PREFIX}:list_products:*list_id={list_id}*")
    n = n_ordered + n_list
    record_cache_invalidation("list_products_ordered", n_ordered)
    record_cache_invalidation("list_products", n_list)
    if n:
        logger.info("Cache invalidated %d key(s) for list_id=%s", n, list_id)


def invalidate_for_product(product_id: int) -> None:
    """Invalidate caches containing product data (detail, list, and list endpoints that embed products)."""
    n_product_detail = _delete_by_pattern(f"{_RESP_PREFIX}:product_detail:*product_id={product_id}*")
    n_products_list = _delete_by_pattern(f"{_RESP_PREFIX}:products_list:*")
    n_list_ordered = _delete_by_pattern(f"{_RESP_PREFIX}:list_products_ordered:*")
    n_list = _delete_by_pattern(f"{_RESP_PREFIX}:list_products:*")
    n = n_product_detail + n_products_list + n_list_ordered + n_list
    record_cache_invalidation("product_detail", n_product_detail)
    record_cache_invalidation("products_list", n_products_list)
    record_cache_invalidation("list_products_ordered", n_list_ordered)
    record_cache_invalidation("list_products", n_list)
    if n:
        logger.info("Cache invalidated %d key(s) for product_id=%s", n, product_id)


def invalidate_for_categories() -> None:
    """Invalidate all category caches and list endpoints that embed category data."""
    n_categories_all = _delete_by_pattern(f"{_RESP_PREFIX}:categories_all:*")
    n_category_detail = _delete_by_pattern(f"{_RESP_PREFIX}:category_detail:*")
    n_list_ordered = _delete_by_pattern(f"{_RESP_PREFIX}:list_products_ordered:*")
    n = n_categories_all + n_category_detail + n_list_ordered
    record_cache_invalidation("categories_all", n_categories_all)
    record_cache_invalidation("category_detail", n_category_detail)
    record_cache_invalidation("list_products_ordered", n_list_ordered)
    if n:
        logger.info("Cache invalidated %d category key(s)", n)


def invalidate_for_reference_data(entity_name: str) -> None:
    """Invalidate cached reference-data responses for *entity_name*."""
    n = _delete_by_pattern(f"{_RESP_PREFIX}:{entity_name}_*")
    # This helper invalidates list/detail groups in one pattern, so the
    # label is tracked at entity granularity.
    record_cache_invalidation(entity_name, n)
    if n:
        logger.info("Cache invalidated %d key(s) for %s", n, entity_name)
