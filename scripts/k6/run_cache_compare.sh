#!/usr/bin/env bash
# Compare two environments with k6 using Docker (no local k6 install required).
#
# Usage:
#   ./scripts/k6/run_cache_compare.sh 'https://staging.example.com' 'https://api.example.com'
#
# Optional env:
#   API_PATH   — default /api/v1/products/?limit=1000&skip=0
#   VUS        — default 20
#   DURATION   — default 2m
#   SKIP_TLS_VERIFY — set to true for self-signed certs
#
# Writes JSON summaries under scripts/k6/out/

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
K6_DIR="${ROOT}/scripts/k6"
OUT="${K6_DIR}/out"
IMAGE="${K6_IMAGE:-grafana/k6:latest}"

STAGING_URL="${1:-}"
PROD_URL="${2:-}"

if [[ -z "${STAGING_URL}" || -z "${PROD_URL}" ]]; then
  echo "Usage: $0 <staging_base_url> <production_base_url>" >&2
  echo "Example: $0 'https://staging-api.example.com' 'https://api.example.com'" >&2
  exit 1
fi

mkdir -p "${OUT}"
# k6 in grafana/k6 often runs as a non-root UID; bind mounts may be root-owned or
# not writable by that UID. Make the dir world-writable and run as root so
# --summary-export can always create files on the host mount.
chmod a+rwx "${OUT}" 2>/dev/null || true

run_k6() {
  local label="$1"
  local base_url="$2"
  local summary="${OUT}/summary-${label}.json"

  echo ""
  echo "=== k6 run: ${label} (${base_url}) ==="

  docker run --rm -i --user 0:0 \
    -v "${K6_DIR}:/scripts/k6" \
    -w /scripts/k6 \
    "${IMAGE}" run \
    -e "BASE_URL=${base_url}" \
    -e "API_PATH=${API_PATH:-/api/v1/products/?limit=1000&skip=0}" \
    -e "VUS=${VUS:-20}" \
    -e "DURATION=${DURATION:-2m}" \
    -e "WARMUP_ITERATIONS=${WARMUP_ITERATIONS:-3}" \
    -e "SKIP_TLS_VERIFY=${SKIP_TLS_VERIFY:-false}" \
    --summary-export="/scripts/k6/out/summary-${label}.json" \
    products_cache_bench.js

  echo "Summary written: ${summary}"
}

run_k6 "staging" "${STAGING_URL}"
run_k6 "production" "${PROD_URL}"

echo ""
echo "Done. Summary JSON:"
echo "  ${OUT}/summary-staging.json"
echo "  ${OUT}/summary-production.json"
echo ""

if [[ "${SKIP_COMPARE:-0}" != "1" ]]; then
  python3 "${K6_DIR}/compare_summaries.py" \
    "${OUT}/summary-staging.json" \
    "${OUT}/summary-production.json" \
    --left-label "Staging" \
    --right-label "Production"
else
  echo "SKIP_COMPARE=1 set; skipping compare_summaries.py."
  echo "Visual compare: python3 ${K6_DIR}/compare_summaries.py"
fi
