# Celery + Kafka Implementation Plan

This document covers four opportunities to improve the backend by introducing **Celery** (with Redis as broker) for task queues and **Kafka** for event streaming. Items are ordered by priority.

> **Current stack:** FastAPI + SQLAlchemy + MySQL + Redis (cache only) + single Uvicorn worker.
> Redis is already running in `docker-compose.yml` and can double as the Celery broker at zero extra infrastructure cost.

---

## Table of Contents

1. [Web Push Notification Delivery (Priority 4/5)](#1-web-push-notification-delivery)
2. [Image Processing Offload (Priority 4/5)](#2-image-processing-offload)
3. [Scheduled Cleanup Tasks via Celery Beat (Priority 3/5)](#3-scheduled-cleanup-tasks-via-celery-beat)
4. [Event Sourcing / Audit Trail via Kafka (Priority 2/5 now → 4/5 when needed)](#4-event-sourcing--audit-trail-via-kafka)
5. [Shared Infrastructure Setup](#5-shared-infrastructure-setup)

---

## 1. Web Push Notification Delivery

**Priority: 4/5** — Already works via `BackgroundTasks`, but lacks durability, parallelism, and observability.

### Current Implementation

| File | What it does |
|------|-------------|
| `app/services/push_notifications.py` → `send_to_subscription()` (lines 84–153) | Synchronous `pywebpush.webpush()` call with `time.sleep`-based exponential backoff retry (up to 3 retries). Blocks the calling thread for the duration of each HTTP request to the push service. |
| `app/services/push_notifications.py` → `broadcast_to_active_subscriptions()` (lines 155–198) | Iterates **all** active subscriptions sequentially in batches of 500, calling `send_to_subscription()` for each one. A single thread handles the entire broadcast. |
| `app/services/push_notifications.py` → `send_to_subscriptions_by_topic()` (lines 499–555) | Same sequential pattern for topic-based sends. |
| `app/services/push_notifications.py` → `send_to_admin_subscriptions()` (lines 232–278) | Same pattern for per-admin sends. |
| `app/services/push_notifications.py` → `send_to_all_admins()` (lines 281–325) | Same pattern for all-admin sends. |
| `app/services/order.py` → `create_order()` (lines 561–615) | Schedules `_notify_new_order` via `background.add_task()`. The inner function opens a new `SessionLocal()`, fetches the order, composes a payload, and calls `send_to_subscriptions_by_topic("new_order", ...)`. |
| `app/api/endpoints/auth.py` (lines 55–81, 157) | Schedules `_notify_admin_login` via `background.add_task()`. |
| `app/services/list.py` (lines 147–175, 257–285) | Schedules list-published notification via `background.add_task()`. |
| `app/api/endpoints/push.py` (lines 88–260) | Admin push test/broadcast/notify endpoints — all use `background.add_task()`. |

### Problems

1. **No durability** — `BackgroundTasks` runs in-process. If the API container crashes or restarts while a notification is in flight, it is silently lost. There is no retry queue, no persistent storage of pending tasks.
2. **Thread blocking** — Each `webpush()` call is a synchronous HTTP request. The retry logic uses `time.sleep()` (lines 149–152) which blocks a Uvicorn threadpool thread. With a single worker, this directly limits API throughput.
3. **Sequential broadcast** — `broadcast_to_active_subscriptions()` sends to subscribers one by one. With 100 subscribers and an average 200ms per push, a broadcast takes ~20 seconds — all on a single thread.
4. **No observability** — Failures are logged and swallowed (`except Exception: pass` at line 611–613 in `order.py`). There is no way to see pending tasks, retry counts, failure rates, or dead-letter entries.
5. **Deduplication without atomicity** — `send_to_subscription()` checks `notification_log` for dedup (lines 97–106) but the check-then-insert is not atomic, risking duplicate sends under concurrent background tasks.

### Proposed Solution: Celery Tasks

#### New file: `app/tasks/push_notifications.py`

```python
from celery import shared_task
from app.core.database import SessionLocal
from app.services.push_notifications import (
    send_to_subscription as _send_to_sub_sync,
    PushSendError,
)
from app.models.web_push_subscription import WebPushSubscription
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=2,
    retry_backoff=True,        # exponential: 2, 4, 8, 16, 32s
    retry_backoff_max=60,
    acks_late=True,            # re-queue if worker crashes mid-task
    reject_on_worker_lost=True,
)
def send_push_notification(self, subscription_id: int, payload: dict, event_id: str | None = None):
    """Deliver a single Web Push notification with Celery-managed retries."""
    db = SessionLocal()
    try:
        sub = db.query(WebPushSubscription).get(subscription_id)
        if not sub or not sub.is_active:
            return {"status": "skipped", "reason": "inactive_or_missing"}

        # Delegate to existing sync function but with max_retries=0
        # (Celery handles retries, not the inner loop)
        result = _send_to_sub_sync(sub, payload, max_retries=0, event_id=event_id, db=db)
        return {"status": "sent" if result else "failed"}
    except PushSendError as exc:
        if exc.status_code in (404, 410):
            # Subscription gone — deactivate, don't retry
            sub.is_active = False
            db.add(sub)
            db.commit()
            return {"status": "deactivated"}
        raise self.retry(exc=exc)
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task
def broadcast_push_notification(payload: dict, topic_name: str | None = None, event_id: str | None = None):
    """Fan out individual send tasks for a broadcast or topic send."""
    db = SessionLocal()
    try:
        if topic_name:
            # Query subscriptions for the topic (reuse existing query logic)
            from app.models.notification_topic import NotificationTopic
            from app.models.subscription_topic import SubscriptionTopic
            topic = db.query(NotificationTopic).filter(NotificationTopic.name == topic_name).first()
            if not topic:
                return {"status": "topic_not_found"}
            sub_ids = [
                row.subscription_id
                for row in db.query(SubscriptionTopic).filter(SubscriptionTopic.topic_id == topic.id).all()
            ]
            subs = db.query(WebPushSubscription).filter(
                WebPushSubscription.id.in_(sub_ids),
                WebPushSubscription.is_active == True,
            ).all()
        else:
            subs = db.query(WebPushSubscription).filter(
                WebPushSubscription.is_active == True,
            ).all()

        for sub in subs:
            send_push_notification.delay(sub.id, payload, event_id)

        return {"status": "fanned_out", "count": len(subs)}
    finally:
        db.close()
```

#### Changes to existing code

**`app/services/order.py`** — Replace the `_notify_new_order` closure + `background.add_task()` block (lines 561–615) with:
```python
from app.tasks.push_notifications import broadcast_push_notification

# After db.commit() + db.refresh():
broadcast_push_notification.delay(
    payload={
        "title": title,
        "body": body,
        "data": {"type": "new_order", "order_id": db_order.id, "url": order_link},
        "tag": f"new_order_{db_order.id}",
    },
    topic_name="new_order",
    event_id=f"new_order_{db_order.id}",
)
```

Same pattern applies to:
- `app/api/endpoints/auth.py` — replace `_notify_admin_login` + `background.add_task()`
- `app/services/list.py` — replace `_notify_list_published` + `background.add_task()`
- `app/api/endpoints/push.py` — replace all `background.add_task(_send)` patterns

The `BackgroundTasks` parameter can be removed from the `create_order()`, `create_list()`, `update_list()` function signatures and from all endpoint definitions that only passed it for push notifications.

### Benefits

| Aspect | Before (BackgroundTasks) | After (Celery) |
|--------|-------------------------|----------------|
| Durability | Lost on crash | Persisted in Redis broker; `acks_late` re-queues on worker crash |
| Parallelism | 1 thread | N workers × M prefetch; broadcast fans out to parallel tasks |
| Retry | Manual `time.sleep` loop in API process | Celery exponential backoff with configurable max retries + dead-letter |
| Observability | `logger.info/error` only | Flower dashboard, Prometheus celery-exporter, task result backend |
| API impact | Blocks a threadpool thread | Zero impact — tasks run in separate container |

---

## 2. Image Processing Offload

**Priority: 4/5** — Currently blocks the HTTP response; CPU-bound work competes with request serving.

### Current Implementation

| File | What it does |
|------|-------------|
| `app/core/image_processing.py` → `process_and_save_image_versions()` (lines 88–195) | Reads uploaded file bytes, validates with PIL, generates 3 versions (original, medium 800×800, thumbnail 200×200) using `Image.thumbnail()` with LANCZOS resampling, writes each to disk. All synchronous. |
| `app/core/image_processing.py` → `resize_image()` (lines 24–66) | Opens image bytes with PIL, applies EXIF transpose, resizes with LANCZOS, saves to BytesIO. CPU-bound. |
| `app/api/endpoints/product_images.py` | `POST .../products/{id}/images` — calls `process_and_save_image_versions(subdirectory="products")` synchronously. HTTP response waits. |
| `app/api/endpoints/categories.py` (lines ~269, 307, 479, 613) | Category image upload on create/update — calls `process_and_save_image_versions(subdirectory="categories")` synchronously. |
| `app/api/endpoints/products.py` (lines ~298–355) | Product create with `primary_image` — calls image processing synchronously. |
| `app/core/staging_uploads.py` | Staging upload (no resize), used with `primary_image_upload_id` flow. |

### Problems

1. **Blocks the event loop** — Upload handlers are `async def` but call synchronous PIL code. In a single-worker Uvicorn setup, this blocks the entire event loop for the duration of image processing (could be 500ms–2s per upload depending on image size).
2. **User waits** — The HTTP 200/201 response is not returned until all 3 image versions are generated and written to disk. For a 10MB JPEG, the user stares at a spinner for several seconds.
3. **No retry on failure** — If disk write fails partway (e.g., disk full after writing "original" but before "thumbnail"), the upload is partially saved with no recovery mechanism.
4. **CPU contention** — PIL LANCZOS resampling is CPU-intensive. Running it in the API process means image uploads degrade response times for all concurrent requests.

### Proposed Solution: Celery Task

#### New file: `app/tasks/image_processing.py`

```python
from celery import shared_task
from app.core.image_processing import resize_image
from app.core.file_upload import get_upload_dir
import os
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def process_image_versions(
    self,
    raw_image_path: str,
    image_dir: str,
    image_id: str,
    ext: str,
    versions: dict,
):
    """Generate resized versions of an uploaded image in a worker process.

    Args:
        raw_image_path: Absolute path to the original uploaded file (already saved by the API).
        image_dir: Relative path to the image directory under uploads.
        image_id: UUID hex string identifying this image.
        ext: File extension (e.g., ".jpg").
        versions: Dict mapping version name → (width, height) or None for original.
    """
    try:
        upload_root = get_upload_dir()
        full_dir = os.path.join(upload_root, image_dir)
        os.makedirs(full_dir, exist_ok=True)

        with open(raw_image_path, "rb") as f:
            file_content = f.read()

        for version_name, size in versions.items():
            if version_name == "original":
                # Original is already saved by the API at upload time
                continue
            processed_content = resize_image(file_content, tuple(size))
            filename = f"{image_id}-{version_name}{ext}"
            file_path = os.path.join(full_dir, filename)
            with open(file_path, "wb") as f:
                f.write(processed_content)

        logger.info("Image versions generated for %s", image_id)
        return {"status": "completed", "image_id": image_id}
    except Exception as exc:
        logger.error("Image processing failed for %s: %s", image_id, exc)
        raise self.retry(exc=exc)
```

#### Changes to existing code

**`app/core/image_processing.py` → `process_and_save_image_versions()`** — Split into two phases:

1. **Synchronous (in API request):** Validate image bytes, generate UUID, save original to disk, return the `image_dir` path immediately.
2. **Asynchronous (Celery task):** Generate medium + thumbnail versions in a worker.

The endpoint response returns immediately with the `image_dir`. The frontend can show a placeholder for medium/thumbnail until they appear (or poll/use the original in the meantime).

**`app/core/image_versions.py` → `resolve_image_versions()`** — Already handles missing versions gracefully (returns `null` for versions not found on disk). No changes needed.

### Considerations

- **Shared volume** — The `api` and `celery_worker` containers must both mount `./uploads:/app/uploads` so the worker can read the raw file and write processed versions.
- **Failure UX** — If a version fails to generate, the original is still available. Admin can re-upload. Celery retries cover transient disk errors.
- **Ordering guarantee** — Not needed. Each image is independent.

### Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Response time | 1–3s (image size dependent) | ~100ms (save original + enqueue) |
| Event loop | Blocked during PIL resize | Free — only fast I/O for original save |
| CPU isolation | Competes with HTTP requests | Runs in dedicated worker container |
| Retry | None — partial state on failure | Celery retries; original always safe |

---

## 3. Scheduled Cleanup Tasks via Celery Beat

**Priority: 3/5** — Three different cleanup mechanisms with three different patterns; Celery Beat unifies them.

### Current Implementation

| Task | Current mechanism | File | Problems |
|------|-------------------|------|----------|
| **Expired session cleanup** | Runs once at API startup in `startup_event()` | `app/main.py` lines 164–176; `app/services/auth.py` → `cleanup_expired_sessions()` lines 602–625 | Only runs when API starts. If the API stays up for months, sessions accumulate. |
| **Inactive push subscription pruning** | `asyncio.create_task(prune_loop())` — infinite loop with `await asyncio.sleep(86400)` | `app/main.py` lines 178–195; `app/services/push_notifications.py` → `prune_inactive_subscriptions()` lines 201–223 | Runs inside the API process; dies on restart; no visibility into when it last ran or if it failed; holds a DB session for each run. |
| **Staging upload cleanup** | Standalone script `scripts/cleanup_staging_uploads.py`, meant to be run via cron/CronJob externally | `scripts/cleanup_staging_uploads.py` lines 1–81 | Not wired to anything — requires external cron configuration that may not exist. |

### Proposed Solution: Celery Beat

#### New file: `app/tasks/cleanup.py`

```python
from celery import shared_task
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions(days_to_keep: int = 30):
    """Delete expired refresh tokens older than the retention period."""
    from app.services.auth import cleanup_expired_sessions as _cleanup
    db = SessionLocal()
    try:
        deleted = _cleanup(db, days_to_keep=days_to_keep)
        db.commit()
        logger.info("Cleanup: removed %d expired sessions", deleted)
        return {"deleted": deleted}
    finally:
        db.close()


@shared_task
def prune_inactive_push_subscriptions(older_than_days: int = 7):
    """Hard-delete inactive push subscriptions past retention."""
    from app.services.push_notifications import prune_inactive_subscriptions
    db = SessionLocal()
    try:
        deleted = prune_inactive_subscriptions(db, older_than_days=older_than_days)
        logger.info("Prune: removed %d inactive subscriptions", deleted)
        return {"deleted": deleted}
    finally:
        db.close()


@shared_task
def cleanup_staging_uploads(ttl_hours: int = 24):
    """Remove old staging upload directories."""
    from scripts.cleanup_staging_uploads import cleanup_staging_uploads as _cleanup
    removed = _cleanup(ttl_hours=ttl_hours)
    logger.info("Staging cleanup: removed %d directories", removed)
    return {"removed": removed}
```

#### Celery Beat schedule (in `app/celery_app.py`):

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "app.tasks.cleanup.cleanup_expired_sessions",
        "schedule": crontab(hour=3, minute=0),  # daily at 3:00 AM
        "args": (30,),
    },
    "prune-inactive-subscriptions": {
        "task": "app.tasks.cleanup.prune_inactive_push_subscriptions",
        "schedule": crontab(hour=4, minute=0),  # daily at 4:00 AM
        "args": (7,),
    },
    "cleanup-staging-uploads": {
        "task": "app.tasks.cleanup.cleanup_staging_uploads",
        "schedule": crontab(hour=5, minute=0),  # daily at 5:00 AM
        "args": (24,),
    },
}
```

#### Changes to existing code

**`app/main.py`** — Remove from `startup_event()`:
- Lines 164–176: session cleanup block (replaced by scheduled task)
- Lines 178–195: `prune_loop()` + `asyncio.create_task()` (replaced by scheduled task)

The startup function becomes simpler: just `init_redis()` + `initialize_default_admin()`.

### Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Reliability | Prune loop dies on process restart; session cleanup runs once at startup | Celery Beat is a dedicated scheduler process; tasks survive API restarts |
| Consistency | 3 different mechanisms (startup hook, asyncio loop, external cron) | Single pattern: Celery Beat schedule |
| Observability | `logger.info` only | Flower dashboard shows last run time, result, duration, failures |
| API process | Prune loop holds DB session inside API process | Tasks run in worker container; API process is clean |
| Staging cleanup | Requires manual cron setup that may not exist | Automatically scheduled — no external configuration needed |

---

## 4. Event Sourcing / Audit Trail via Kafka

**Priority: 2/5 now → 4/5 when analytics, email, or multi-service features are needed.**

### Current State

There is **no structured event stream** in the codebase. Business events (order created, product updated, admin logged in, list published) are:
- Logged as debug text via `logger.info()` (e.g., `_format_order_for_debug()` in `app/services/order.py`)
- Optionally trigger Web Push notifications via `BackgroundTasks` (soon Celery)
- Not persisted in any event store or audit table

The `notification_log` table (`app/models/notification_log.py`) tracks push deduplication only — it is not a general audit log.

The `source` query parameter on `POST /orders/` (e.g., "Cart", "Admin", "ProductPage") is used in debug logs only and not stored in the database.

### Why Kafka (and not just Celery)

Celery is a task queue — it says "do this work." Kafka is an event log — it says "this happened." They serve different purposes:

| Concern | Celery | Kafka |
|---------|--------|-------|
| "Send push notification to subscription #42" | Yes | No |
| "Order #123 was created — notify, audit, update analytics, trigger email" | Awkward (must create separate tasks for each consumer) | Natural (publish once, N consumers read independently) |
| Event replay / reprocessing | Not possible | Read from any offset |
| Decoupling producers from consumers | Tight (producer must know which tasks to call) | Loose (producer publishes to a topic; consumers subscribe independently) |

### When to Introduce Kafka

Kafka adds significant infrastructure complexity (broker, Zookeeper/KRaft, schema registry). It is **not justified now** but becomes high-value when any of these are planned:

- **Customer-facing email confirmations** (order placed, shipped, etc.)
- **Analytics dashboards** (order volume over time, popular products, conversion funnel)
- **Audit trail for compliance** (who changed what, when)
- **Multi-service architecture** (separate services for orders, inventory, notifications)
- **Real-time inventory sync** (stock decremented on order, restored on cancel)
- **Webhook delivery to external systems** (accounting, ERP, shipping)

### Proposed Architecture (for when the time comes)

#### Topics

| Topic | Key | Producers | Consumers |
|-------|-----|-----------|-----------|
| `order.events` | `order_id` | `app/services/order.py` | notifications, analytics, audit, email, inventory |
| `product.events` | `product_id` | `app/services/product.py`, `product_images.py` | search indexer, cache invalidation, analytics |
| `admin.events` | `admin_id` | `app/services/auth.py` | audit, security monitoring |
| `list.events` | `list_id` | `app/services/list.py` | notifications, analytics |

#### Event Schema (example for `order.events`)

```json
{
  "event_type": "order.created",
  "event_id": "uuid-v4",
  "timestamp": "2026-04-04T12:00:00Z",
  "data": {
    "order_id": 123,
    "liste_id": 5,
    "nume_client": "Ion Popescu",
    "items_count": 3,
    "total_value": 150.50,
    "source": "Cart"
  },
  "metadata": {
    "ip_address": "1.2.3.4",
    "user_agent": "Mozilla/5.0 ..."
  }
}
```

#### Docker Compose addition

```yaml
kafka:
  image: bitnami/kafka:3.7
  container_name: online_shop_kafka
  restart: unless-stopped
  environment:
    - KAFKA_CFG_NODE_ID=1
    - KAFKA_CFG_PROCESS_ROLES=controller,broker
    - KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
    - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
    - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
    - KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER
    - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
    - KAFKA_CFG_LOG_RETENTION_HOURS=168  # 7 days
  volumes:
    - kafka_data:/bitnami/kafka
  networks:
    - backend
```

#### Python dependencies

```
confluent-kafka  # or aiokafka for async producer
```

#### Integration point (example for order creation)

```python
# In app/services/order.py, after db.commit():
from app.events import publish_event

publish_event("order.events", {
    "event_type": "order.created",
    "data": {"order_id": db_order.id, "liste_id": db_order.liste_id, ...},
})
```

Consumers (notification sender, analytics writer, audit logger) each run as independent processes reading from the same topic at their own pace.

### Implementation Steps (when the time comes)

1. Add Kafka to `docker-compose.yml` (KRaft mode — no Zookeeper needed since Kafka 3.3+)
2. Create `app/events/producer.py` with a singleton Kafka producer
3. Create `app/events/schemas.py` defining event schemas (Pydantic models)
4. Add `publish_event()` calls after key business actions (order CRUD, product CRUD, auth)
5. Create consumer processes (can be Celery tasks that poll Kafka, or standalone consumer scripts)
6. Add a `kafka_consumer` service to `docker-compose.yml`

---

## 5. Shared Infrastructure Setup

This section covers the Celery + Redis broker infrastructure needed by items 1, 2, and 3.

### 5.1. New dependency: `requirements.txt`

Add:
```
celery==5.4.0
flower==2.0.1
```

(`flower` is the Celery monitoring dashboard — optional but strongly recommended.)

### 5.2. New file: `app/celery_app.py`

```python
from celery import Celery
from app.core.config import settings

broker_url = (
    f"redis://{settings.REDIS_USERNAME}:{settings.REDIS_PASSWORD}"
    f"@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB + 1}"
)

app = Celery(
    "online_shop",
    broker=broker_url,
    backend=broker_url,  # result backend (optional, for task result tracking)
    include=[
        "app.tasks.push_notifications",
        "app.tasks.image_processing",
        "app.tasks.cleanup",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Bucharest",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=4,
    # Dead-letter: tasks that fail after all retries go here
    task_reject_on_worker_lost=True,
)
```

> **Note:** Uses `REDIS_DB + 1` (DB 1) for the Celery broker to avoid colliding with the cache layer (DB 0). This requires no extra Redis instance.

### 5.3. Docker Compose additions (`docker-compose.yml`)

```yaml
celery_worker:
  build:
    context: .
    dockerfile: Dockerfile
    args:
      UID: 1000
      GID: 1000
  container_name: online_shop_celery_worker
  restart: unless-stopped
  command: celery -A app.celery_app worker --loglevel=info --concurrency=4
  environment:
    # Same env vars as `api` for DB, Redis, VAPID, etc.
    <<: *api-env  # Use YAML anchor (define on api service)
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
  volumes:
    - ./uploads:/app/uploads  # shared volume for image processing
    - ./logs:/app/logs
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '1.0'
      reservations:
        memory: 128M
        cpus: '0.25'
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  networks:
    - backend

celery_beat:
  build:
    context: .
    dockerfile: Dockerfile
    args:
      UID: 1000
      GID: 1000
  container_name: online_shop_celery_beat
  restart: unless-stopped
  command: celery -A app.celery_app beat --loglevel=info
  environment:
    <<: *api-env
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
  deploy:
    resources:
      limits:
        memory: 128M
        cpus: '0.25'
      reservations:
        memory: 64M
        cpus: '0.10'
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  networks:
    - backend
```

### 5.4. New directory structure

```
app/
├── celery_app.py           # Celery application instance + Beat schedule
├── tasks/
│   ├── __init__.py
│   ├── push_notifications.py   # Item 1
│   ├── image_processing.py     # Item 2
│   └── cleanup.py              # Item 3
```

### 5.5. Monitoring (optional but recommended)

Add a Flower container for real-time task monitoring:

```yaml
celery_flower:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: online_shop_celery_flower
  restart: unless-stopped
  command: celery -A app.celery_app flower --port=5555 --basic-auth=admin:${FLOWER_PASSWORD}
  environment:
    <<: *api-env
  depends_on:
    - redis
  ports:
    - "5555:5555"
  networks:
    - backend
    - frontend
```

### 5.6. Implementation order

1. **Set up infrastructure** (section 5) — `celery_app.py`, `app/tasks/__init__.py`, docker-compose services. Verify a basic test task works end-to-end.
2. **Migrate push notifications** (item 1) — Highest impact; replace `BackgroundTasks` calls with Celery tasks. Remove `BackgroundTasks` parameters from function signatures.
3. **Migrate image processing** (item 2) — Split `process_and_save_image_versions()` into sync validation + async resize.
4. **Migrate cleanup tasks** (item 3) — Move startup/loop logic to Celery Beat. Simplify `main.py` startup.
5. **Kafka** (item 4) — Defer until analytics/email/audit features are on the roadmap.
