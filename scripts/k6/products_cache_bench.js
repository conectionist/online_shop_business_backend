/**
 * Load-test a cacheable GET endpoint and record X-Cache HIT vs miss.
 *
 * Run with Docker (recommended in this repo):
 *   mkdir -p scripts/k6/out && chmod a+rwx scripts/k6/out
 *   docker run --rm -i --user 0:0 -v "$(pwd)/scripts/k6:/scripts/k6" -w /scripts/k6 grafana/k6:latest run \
 *     -e BASE_URL=https://staging.example.com \
 *     -e API_PATH='/api/v1/products/?limit=1000&skip=0' \
 *     --summary-export=/scripts/k6/out/summary.json \
 *     products_cache_bench.js
 *   (--user 0:0 avoids permission denied writing the summary JSON on a bind mount.)
 *
 * Compare two summary JSONs (terminal table + HTML):
 *   python3 scripts/k6/compare_summaries.py scripts/k6/out/summary-staging.json scripts/k6/out/summary-production.json
 *
 * Env:
 *   BASE_URL          (required) e.g. https://api.example.com — no trailing slash
 *   API_PATH          (optional) default /api/v1/products/?limit=1000&skip=0
 *   VUS               (optional) default 20
 *   DURATION          (optional) default 2m
 *   WARMUP_ITERATIONS (optional) default 3 — extra GETs before main phase to warm cache
 *   SKIP_TLS_VERIFY   (optional) set to "true" for self-signed HTTPS
 *   EXTRA_HEADERS     (optional) JSON object string, e.g. '{"Authorization":"Bearer x"}'
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate } from "k6/metrics";

const cacheHits = new Counter("x_cache_hits");
/** Any response where X-Cache is not HIT (missing on miss, or other values). */
const cacheNotHits = new Counter("x_cache_not_hits");
const hitRate = new Rate("x_cache_hit_rate");

function requireEnv(name) {
  const v = __ENV[name];
  if (!v || String(v).trim() === "") {
    throw new Error(`Missing required env: ${name}`);
  }
  return String(v).trim();
}

function optionalEnv(name, defaultValue) {
  const v = __ENV[name];
  if (v === undefined || v === null || String(v).trim() === "") {
    return defaultValue;
  }
  return String(v).trim();
}

function buildUrl() {
  const base = requireEnv("BASE_URL").replace(/\/$/, "");
  const path = optionalEnv("API_PATH", "/api/v1/unitati");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

function headerGet(res, name) {
  const want = name.toLowerCase();
  const h = res.headers || {};
  for (const k of Object.keys(h)) {
    if (k.toLowerCase() === want) {
      return h[k];
    }
  }
  return undefined;
}

function parseExtraHeaders() {
  const raw = optionalEnv("EXTRA_HEADERS", "");
  if (!raw) {
    return {};
  }
  try {
    return JSON.parse(raw);
  } catch (e) {
    throw new Error(`EXTRA_HEADERS must be valid JSON object: ${e}`);
  }
}

function recordCache(res) {
  const xc = headerGet(res, "X-Cache");
  if (String(xc || "").toUpperCase() === "HIT") {
    cacheHits.add(1);
    hitRate.add(1);
    return;
  }
  cacheNotHits.add(1);
  hitRate.add(0);
}

const url = buildUrl();
const extraHeaders = parseExtraHeaders();
const warmupIterations = Math.max(0, parseInt(optionalEnv("WARMUP_ITERATIONS", "3"), 10) || 0);

const vus = Math.max(1, parseInt(optionalEnv("VUS", "20"), 10) || 20);
const duration = optionalEnv("DURATION", "2m");

const skipTls = optionalEnv("SKIP_TLS_VERIFY", "false").toLowerCase() === "true";

export const options = {
  insecureSkipTLSVerify: skipTls,
  vus,
  duration,
  // No default thresholds: compare runs should exit 0 even if an env is down or returns 401/403.
  // Add thresholds in a wrapper or extend this script when you want fail-fast CI gates.
};

export function setup() {
  const params = {
    headers: {
      Accept: "application/json",
      ...extraHeaders,
    },
    tags: { name: "products_cache_bench" },
  };

  for (let i = 0; i < warmupIterations; i++) {
    const res = http.get(url, params);
    check(res, {
      "warmup status 200": (r) => r.status === 200,
    });
    recordCache(res);
    sleep(0.05);
  }

  return { url };
}

export default function (data) {
  const target = data && data.url ? data.url : url;
  const res = http.get(target, {
    headers: {
      Accept: "application/json",
      ...extraHeaders,
    },
    tags: { name: "products_cache_bench" },
  });

  check(res, {
    "status 200": (r) => r.status === 200,
  });
  recordCache(res);
  sleep(0.05);
}
