# Backend Web Push Notifications — Checklist

> Scope: Enable PWA push notifications support on the FastAPI backend (no frontend code in this doc). Follow docker-first workflow.

## Phase 0 — Prep and Decisions
- [x] Confirm target environments and domains for CORS and Trusted Hosts — covered via `CORS_ORIGINS` and `ALLOWED_HOSTS` envs in docker compose; ensure prod domains are set in `.env`
- [x] Decide if subscriptions are tied to authenticated users now or later — device-level now; plan for optional `user_id` mapping later
- [x] Choose initial send strategy: background tasks vs. queue (defer queue if unsure) — start with FastAPI `BackgroundTasks`

## Phase 1 — Dependencies & Config
- [x] Add `pywebpush` to `requirements.txt`
- [ ] Generate VAPID keys (one-time): `npx web-push generate-vapid-keys`
- [ ] Add env vars: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`
- [x] Load new env vars in `app/core/config.py` → `settings`
- [x] Add VAPID envs to `docker-compose.yml` (`api.environment`)
- [x] Rebuild containers to pick up dependency/config changes

## Phase 2 — Data Model & Migration
- [x] Create SQLAlchemy model `WebPushSubscription` (utf8mb4, proper engine/table args)
- [x] Fields: `id`, `user_id` (nullable), `endpoint` (unique), `p256dh_key`, `auth_key`, `user_agent`, `is_active`, `created_at`, `updated_at`, `last_success_at`, `last_failure_reason`
- [x] Create Alembic migration for the new table
- [ ] Seed test data paths if needed for integration tests
- [x] Rebuild containers and run migrations

## Phase 3 — Pydantic Schemas
- [x] Add `PushSubscriptionIn` (endpoint, keys.p256dh, keys.auth, user_agent?)
- [x] Add `PushSubscriptionOut` response schema
- [x] Add optional `SendNotificationRequest` (title, body, data?, icon?, tag?)

## Phase 4 — Service Layer
- [x] Implement `save_or_update_subscription(sub, user_id?)`
- [x] Implement `deactivate_subscription(endpoint)` / `delete_subscription(endpoint)`
- [x] Implement `send_to_subscription(subscription, payload)` using `pywebpush`
- [x] Handle `WebPushException` (410/404 → deactivate, record failure)
- [x] Implement broadcast helper with graceful degradation

## Phase 5 — API Endpoints
- [ ] `POST /api/v1/push/subscribe` — create/update subscription (auth optional now)
- [ ] `DELETE /api/v1/push/subscribe` — unsubscribe by endpoint (or id)
- [ ] `GET /api/v1/push/public-key` — return VAPID public key for the PWA
- [ ] `POST /api/v1/push/test` — admin-only: send test payload
- [ ] Input validation for endpoint/p256dh/auth

## Phase 6 — Background Execution & Reliability
- [ ] Use FastAPI `BackgroundTasks` for non-blocking send
- [ ] Add retry/backoff for transient failures
- [ ] Mark inactive on 410 Gone and prune stale subscriptions periodically

## Phase 7 — Security & Access Control
- [ ] AuthN/AuthZ for send/test endpoints (admin-only)
- [ ] Optional: tie subscriptions to `user_id` for authenticated clients
- [ ] Rate-limit broadcast/test endpoints

## Phase 8 — CORS/Trusted Hosts & Config Review
- [ ] Ensure PWA origins are present in `CORS_ORIGINS`
- [ ] Review `ALLOWED_HOSTS` for deployment domains
- [ ] Ensure sensitive keys never logged

## Phase 9 — Testing (Docker-first)
- [ ] Unit tests: service save/update
- [ ] Unit tests: send success path
- [ ] Unit tests: expired/invalid subscription → deactivate
- [ ] Integration tests: subscribe/unsubscribe endpoints
- [ ] Integration tests: send test (simulate success/failure)
- [ ] Run tests via docker test container with `.env.test`

## Phase 10 — Ops & Docs
- [ ] Add ops notes in `docs/` (key generation, env setup, example payloads)
- [ ] Document production practice: prebuilt images, env injected at runtime
- [ ] Avoid `docker compose down -v` in production to preserve volumes

## Nice-to-haves (Future)
- [ ] Move sending to a queue (e.g., Redis + RQ/Celery)
- [ ] Per-user notification preferences and topics
- [ ] Metrics and dashboards for delivery success/latency
