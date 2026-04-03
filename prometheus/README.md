# Prometheus Scrape Example

This folder contains a minimal Prometheus configuration for scraping metrics
from this API, including Bearer token authentication for `GET /metrics`.

## Files

- `prometheus.yml`: Example scrape config.
- `grafana-dashboard-online-shop-redis-cache.json`: Grafana dashboard (import JSON) for Redis cache metrics.

## Grafana dashboard

The dashboard visualizes `redis_cache_lookups_total`, `redis_cache_sets_total`, and
`redis_cache_invalidations_total` (rates, hit/miss breakdown by `route_name`, and hit ratio).

### Import

1. In Grafana: **Dashboards → New → Import**.
2. Upload `grafana-dashboard-online-shop-redis-cache.json` or paste its contents.
3. When prompted, pick your **Prometheus** datasource (the JSON uses a placeholder `DS_PROMETHEUS`).
4. Save; the dashboard UID is `online-shop-redis-cache`.

Requires a Prometheus instance that already scrapes this API (see above). Refresh is 30s; adjust in the dashboard if needed.

## How token auth works

The API protects `/metrics` with Bearer authentication:

- App env var: `METRICS_AUTH_REQUIRED=true`
- App env var: `METRICS_BEARER_TOKENS=<comma-separated-token-list>`

Prometheus sends one token on every scrape request via the `Authorization`
header:

- Header format: `Authorization: Bearer <token>`
- Prometheus source: `authorization.credentials_file`

The token in Prometheus must match one of the values in
`METRICS_BEARER_TOKENS`.

## Recommended secret handling

Do not hardcode tokens in `prometheus.yml`. Use a file mounted into the
Prometheus container instead.

Example secret file content:

`/etc/prometheus/secrets/online_shop_metrics_token`

```text
replace-with-your-real-metrics-token
```

## Example run (dockerized Prometheus)

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: online_shop_prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/secrets:/etc/prometheus/secrets:ro
    ports:
      - "9090:9090"
    command:
      - --config.file=/etc/prometheus/prometheus.yml
```

Then place the token in:

- `./prometheus/secrets/online_shop_metrics_token`

## Target value to use

Use the target according to where Prometheus runs:

- Same Docker network as API: `api:8000`
- Different host / VM: `api.example.com:443` with `scheme: https`

If you use HTTPS, update `scheme` in `prometheus.yml` accordingly.

## Quick verification

1. Start Prometheus and open `http://localhost:9090/targets`.
2. Confirm the `online_shop_api` target is `UP`.
3. Query metric examples:
   - `redis_cache_lookups_total`
   - `redis_cache_sets_total`
   - `redis_cache_invalidations_total`

## Local curl check with token

```bash
curl -i \
  -H "Authorization: Bearer <your-token>" \
  http://localhost:8000/metrics
```

