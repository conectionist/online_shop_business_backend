import os
import random
import re

import requests


def _api_base_url() -> str:
    return os.environ.get("API_BASE_URL", "http://localhost:8000")


def _metrics_text() -> str:
    response = requests.get(f"{_api_base_url()}/metrics")
    assert response.status_code == 200, (
        f"/metrics should return 200, got {response.status_code}: {response.text}"
    )
    return response.text


def _metric_value(metrics_text: str, metric_name: str, labels: dict[str, str]) -> float:
    for line in metrics_text.splitlines():
        if not line.startswith(f"{metric_name}" + "{"):
            continue
        match = re.match(r'^[^{]+\{([^}]*)\}\s+([0-9.eE+-]+)$', line)
        if not match:
            continue
        raw_labels, raw_value = match.groups()
        pairs = re.findall(r'(\w+)="([^"]*)"', raw_labels)
        line_labels = {k: v for k, v in pairs}
        if line_labels == labels:
            return float(raw_value)
    return 0.0


def test_metrics_endpoint_exposes_cache_series():
    text = _metrics_text()
    assert "redis_cache_lookups_total" in text
    assert "redis_cache_sets_total" in text
    assert "redis_cache_invalidations_total" in text


def test_per_endpoint_cache_hit_and_miss_counters_increase():
    route_name = "unitati_list"
    params = {
        "skip": random.randint(0, 100),
        "limit": 1,
    }

    before = _metrics_text()
    miss_before = _metric_value(
        before,
        "redis_cache_lookups_total",
        {"route_name": route_name, "result": "miss"},
    )
    hit_before = _metric_value(
        before,
        "redis_cache_lookups_total",
        {"route_name": route_name, "result": "hit"},
    )

    first = requests.get(f"{_api_base_url()}/api/v1/unitati/", params=params)
    assert first.status_code == 200, (
        f"First unitati list request should return 200, got {first.status_code}: {first.text}"
    )

    second = requests.get(f"{_api_base_url()}/api/v1/unitati/", params=params)
    assert second.status_code == 200, (
        f"Second unitati list request should return 200, got {second.status_code}: {second.text}"
    )
    assert second.headers.get("X-Cache") == "HIT", (
        "Second request should be served from cache (X-Cache=HIT). "
        f"Got X-Cache={second.headers.get('X-Cache')}"
    )

    after = _metrics_text()
    miss_after = _metric_value(
        after,
        "redis_cache_lookups_total",
        {"route_name": route_name, "result": "miss"},
    )
    hit_after = _metric_value(
        after,
        "redis_cache_lookups_total",
        {"route_name": route_name, "result": "hit"},
    )

    assert miss_after >= miss_before + 1, (
        "Expected at least one cache miss increment for first request, "
        f"before={miss_before}, after={miss_after}"
    )
    assert hit_after >= hit_before + 1, (
        "Expected at least one cache hit increment for second request, "
        f"before={hit_before}, after={hit_after}"
    )
