"""Prometheus metrics helpers for cache observability."""

import re
from typing import Optional

from prometheus_client import Counter

_RESP_CACHE_PREFIX = "cache:resp:v1:"
_ROUTE_SEGMENT_PATTERN = re.compile(r"[^a-zA-Z0-9_]")
_MAX_ROUTE_LABEL_LENGTH = 120

_VALID_CACHE_RESULTS = {"hit", "miss", "error", "bypass"}

redis_cache_lookups_total = Counter(
    "redis_cache_lookups_total",
    "Redis cache lookup outcomes by logical route",
    ("route_name", "result"),
)

redis_cache_sets_total = Counter(
    "redis_cache_sets_total",
    "Redis cache set operations by logical route",
    ("route_name",),
)

redis_cache_invalidations_total = Counter(
    "redis_cache_invalidations_total",
    "Redis cache invalidation operations by logical route",
    ("route_name",),
)


def extract_route_name_from_cache_key(cache_key: str) -> Optional[str]:
    """
    Extract logical route_name from response-cache key.

    Example:
      cache:resp:v1:products_list:skip=0:limit=100 -> products_list
    """
    if not cache_key or not cache_key.startswith(_RESP_CACHE_PREFIX):
        return None
    remainder = cache_key[len(_RESP_CACHE_PREFIX):]
    route_name = remainder.split(":", maxsplit=1)[0].strip()
    if not route_name:
        return None
    return route_name


def normalize_route_name(route_name: Optional[str]) -> str:
    """Sanitize route names so they are stable low-cardinality labels."""
    if not route_name:
        return "unknown"
    normalized = _ROUTE_SEGMENT_PATTERN.sub("_", route_name).strip("_")
    if not normalized:
        return "unknown"
    return normalized[:_MAX_ROUTE_LABEL_LENGTH]


def record_cache_lookup(cache_key: str, result: str) -> None:
    """Record hit/miss/error/bypass for endpoint response-cache lookups."""
    if result not in _VALID_CACHE_RESULTS:
        return
    route_name = extract_route_name_from_cache_key(cache_key)
    if route_name is None:
        return
    redis_cache_lookups_total.labels(
        route_name=normalize_route_name(route_name),
        result=result,
    ).inc()


def record_cache_set(cache_key: str) -> None:
    """Record response-cache set operations for endpoint keys."""
    route_name = extract_route_name_from_cache_key(cache_key)
    if route_name is None:
        return
    redis_cache_sets_total.labels(route_name=normalize_route_name(route_name)).inc()


def record_cache_invalidation(route_name: str, deleted_count: int = 1) -> None:
    """Record cache invalidations for a logical route name."""
    if deleted_count <= 0:
        return
    redis_cache_invalidations_total.labels(
        route_name=normalize_route_name(route_name),
    ).inc(deleted_count)
