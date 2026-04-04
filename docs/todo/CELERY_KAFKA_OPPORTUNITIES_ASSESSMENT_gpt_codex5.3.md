# Celery / Kafka Opportunities Assessment

## Overview

This document captures concrete opportunities to improve the backend by introducing:

- **Celery** (with **Redis** as broker/backend initially)
- **Kafka** (only where event-stream semantics materially justify the operational cost)

The goal is to prioritize changes that improve reliability, latency, scalability, and operational clarity, while avoiding unnecessary complexity.

**Status**: Backlog / To Be Implemented Later  
**Last Updated**: 2026-04-03  
**Scope**: `online_shop_business_backend` monolith (FastAPI + MySQL + Redis cache)

---

## Scoring Model

Scores are from **1 to 5**:

- **1** = technically possible, low value, likely unnecessary complexity
- **2** = some value, but still likely premature for current architecture
- **3** = meaningful value in specific scenarios; moderate priority
- **4** = high value, strong candidate once implementation bandwidth exists
- **5** = extremely high value; architecture should move here as soon as feasible

Each score includes:

- Current behavior and constraints
- Expected value (business + technical)
- Added complexity and risk

---

## Current-State Snapshot (Why this matters)

### Existing infrastructure

- Redis exists and is already used for caching.
- There is no Celery runtime currently configured.
- There is no RabbitMQ runtime currently configured.
- There is no Kafka runtime currently configured.

### Current async/background patterns

- In-process `BackgroundTasks` are used for push notification side effects.
- One in-process `asyncio.create_task` loop handles periodic pruning.
- Some notification retry paths use blocking `time.sleep()` in process.

### Architectural implication

The codebase already has real async candidates, but they are executed inside API process boundaries. This creates a reliability and scaling gap that Celery can address immediately with lower risk than Kafka.

---

## Opportunity Inventory (Detailed)

## 1) Push notification fan-out via real queue workers

**Current behavior**

- Notification fan-out loops through subscriptions synchronously in process.
- Retry/backoff includes blocking sleep in send flow.

**Primary code areas**

- `app/services/push_notifications.py`
  - `send_to_subscriptions_by_topic(...)`
  - `broadcast_to_active_subscriptions(...)`
  - `send_to_subscription(...)`

**Recommendation**

- Move fan-out and delivery retries to **Celery tasks**.
- Use Redis broker/backend first.
- Keep chunked/batched fan-out in workers.

**Score: 5/5**

**Why**

- Highest immediate value: better reliability and latency isolation.
- API workers stop performing long-lived fan-out and retry loops.
- Straightforward migration path because logic already exists and can be taskified.

**Risks / complexity**

- Need idempotency and dedupe guarantees per notification event.
- Need queue monitoring and alerting.

---

## 2) Order-created notifications: from in-process side effect to durable async job

**Current behavior**

- Order creation schedules notification side effects using `BackgroundTasks`.
- Failures are not as observable as a dedicated job system.

**Primary code areas**

- `app/services/order.py`
  - `create_order(...)`
  - internal notify callback after commit

**Recommendation**

- Emit `notify_new_order(order_id, ...)` as Celery task after successful commit.

**Score: 5/5**

**Why**

- Critical user/business event should not rely on process-local background execution.
- Reliable retries and operational visibility add significant value.

**Risks / complexity**

- Ensure order data fetch in task is idempotent and resilient to eventual read timing.

---

## 3) Push API endpoints that claim "queued" should become truly queued

**Current behavior**

- Push endpoints return queue-like semantics but run on in-process background mechanism.

**Primary code areas**

- `app/api/endpoints/push.py`

**Recommendation**

- Replace in-process add-task pattern with Celery enqueue + task id response.

**Score: 4/5**

**Why**

- Improves API contract correctness and operator confidence.
- Better observability (job id, state transitions, failure reason).

**Risks / complexity**

- Need a small job-status API or minimal visibility strategy.

---

## 4) Replace in-process periodic prune loop with scheduler + workers

**Current behavior**

- A process-local async loop is started from app startup.

**Primary code areas**

- `app/main.py`
  - startup lifecycle logic
  - prune loop launch

**Recommendation**

- Move to **Celery Beat** (single scheduler) + worker task.

**Score: 4/5**

**Why**

- Eliminates duplicate loop behavior across replicas.
- Decouples periodic maintenance from API process uptime/restarts.

**Risks / complexity**

- Must remove/disable old loop path to avoid double execution.

---

## 5) Session cleanup: startup-only -> scheduled recurring task

**Current behavior**

- Expired sessions cleanup is tied to startup flow.

**Primary code areas**

- `app/main.py`
- `app/services/auth.py` cleanup routine

**Recommendation**

- Execute via Celery Beat on a defined schedule.

**Score: 3/5**

**Why**

- Useful hygiene improvement with moderate value.
- Better consistency than startup-triggered cleanup.

**Risks / complexity**

- Low; mostly scheduling and observability wiring.

---

## 6) Staging uploads cleanup: external/manual scheduling -> unified scheduler

**Current behavior**

- Cleanup currently exists as script/ops procedure.

**Primary code areas**

- `scripts/cleanup_staging_uploads.py`

**Recommendation**

- Register as Celery periodic task under the same scheduler model.

**Score: 3/5**

**Why**

- Consolidates maintenance jobs in one runtime.
- Reduces external scheduling drift.

**Risks / complexity**

- Low; mostly integration and safety checks.

---

## 7) Optional image processing offload for heavy uploads

**Current behavior**

- Image transforms run in request path.

**Primary code areas**

- `app/core/image_processing.py`

**Recommendation**

- Offload final image processing variants to Celery for large workloads.
- Keep lightweight validation synchronous.

**Score: 3/5**

**Why**

- Good performance gain only if payload size/concurrency is substantial.
- Optional now; valuable at higher scale.

**Risks / complexity**

- Must define UX for eventual consistency (image appears after async processing).

---

## 8) Inventory correctness around order creation (queue-related architecture note)

**Current behavior**

- Stock is checked in order flow, but queue/event orchestration is not the direct fix.

**Primary code areas**

- `app/services/order.py` (stock check)
- list-product stock models/services

**Recommendation**

- Prioritize transactional stock reservation/decrement correctness first.
- Celery/Kafka may assist side effects, but core inventory consistency belongs in DB transaction semantics.

**Score: 3/5** (for async/event contribution)

**Why**

- Important domain issue, but not primarily solved by queueing alone.

**Risks / complexity**

- High business impact if designed incorrectly; should be handled as a dedicated design stream.

---

## 9) Kafka for order/list/admin events (future-proofing stream)

**Current behavior**

- Monolithic architecture with limited independent consumers.

**Recommendation**

- Defer Kafka until clear multi-consumer, replay, or cross-service requirements exist.

**Score: 2/5**

**Why**

- Potential strategic value exists, but likely premature now.
- Operational burden is substantial relative to current architecture.

**Risks / complexity**

- High: brokers, consumer lag monitoring, schema/version governance, delivery guarantees.

---

## 10) Kafka for push delivery pipeline

**Recommendation**

- Do not use Kafka for current push pipeline.
- Keep this in task-queue territory (Celery + Redis).

**Score: 1/5**

**Why**

- Task retry workflow is queue-native, not stream-native.

---

## 11) RabbitMQ introduction instead of Redis broker

**Recommendation**

- Defer RabbitMQ unless broker-specific AMQP routing/guarantees become mandatory.
- Start with Redis broker for Celery due to existing stack alignment.

**Score: 2/5**

**Why**

- RabbitMQ can be excellent, but adds another distributed system to operate now.

---

## 12) Kafka-first architecture migration now

**Recommendation**

- Not advised for this phase.

**Score: 1/5**

**Why**

- Very high complexity relative to immediate product value in current monolith.

---

## Prioritized Backlog (Implementation Order)

### Phase 1 (Highest value, lowest regret)

1. Push fan-out and retries to Celery workers (**5/5**)
2. Order-created notification as durable Celery job (**5/5**)
3. Push API endpoints to real queue semantics with task IDs (**4/5**)

### Phase 2 (Operational consistency)

4. Replace in-process prune loop with Celery Beat (**4/5**)
5. Session cleanup periodic task (**3/5**)
6. Staging upload cleanup periodic task (**3/5**)

### Phase 3 (Conditional / scale dependent)

7. Optional async image processing for heavy media traffic (**3/5**)
8. Re-evaluate Kafka once multiple independent consumers exist (**2/5 now**)

---

## Suggested Future Architecture (Target, Not Yet Implemented)

### Core components

- `api` (FastAPI)
- `redis` (cache + Celery broker/backend; logically separated db/index/namespaces)
- `celery_worker` (task execution)
- `celery_beat` (periodic schedule)
- optional dashboard/metrics exporter for worker visibility

### Design constraints

- API must enqueue only after DB transaction success for business events.
- Tasks must be idempotent and safe to retry.
- Fan-out operations should be chunked to avoid oversized tasks.
- Error handling must be explicit and observable.

---

## Definition of Done (for later implementation)

For each migrated opportunity:

1. Task path is no longer process-local `BackgroundTasks` for that flow.
2. Retries/backoff are configured in worker layer.
3. Failure is visible in logs/metrics (not silently swallowed).
4. API response contract reflects actual async behavior.
5. Operational runbook includes queue health checks and failure recovery.

---

## Explicit Deferred Items

These are intentionally deferred to avoid premature complexity:

- Kafka cluster introduction
- RabbitMQ adoption (unless strict AMQP needs appear)
- Broad event-sourcing migration

Reason: current monolith + existing Redis foundation makes Celery-first the highest ROI path.

---

## Decision Summary

- **Adopt later**: Celery + Redis for background/periodic workloads (high value)
- **Defer**: Kafka until architecture and consumer landscape justify it
- **Reassess quarterly**: if integrations and independent consumers increase, revisit Kafka score

