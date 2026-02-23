# Backup & Restore - Async Worker Implementation Plan

## Overview

This document outlines the plan to implement the backup and restore strategy described in [api_backup_restore_strategy.md](api_backup_restore_strategy.md) for this FastAPI backend application using an **asynchronous worker-based architecture**.

**Status**: Design Refined
**Last Updated**: 2026-02-19
**Target**: Production-ready backup/restore system with async job workers

---

## Comparison with Existing Plan

This codebase already has a [synchronous implementation plan](BACKUP_RESTORE_IMPLEMENTATION_PLAN.md). Here's how this async worker approach differs:

| Aspect | Existing Plan (Synchronous) | This Plan (Async Workers) |
|--------|---------------------------|--------------------------|
| **Execution** | Direct API execution | Background workers poll jobs |
| **Progress Tracking** | Not available (blocking request) | Real-time progress (DB for backups, file for restores) |
| **Scalability** | Limited (blocks API workers) | High (dedicated worker containers) |
| **User Experience** | Wait for completion | Immediate response, poll status |
| **Complexity** | Lower (simpler architecture) | Higher (more components) |
| **Use Case** | Small databases, quick operations | Large databases, long-running ops |
| **Job Queue** | None | Database-backed polling |
| **Architecture** | Monolithic | Distributed (API + workers) |

**Recommendation**: Choose this async plan if:
- Backups take >30 seconds
- You want real-time progress tracking
- You need to avoid blocking API workers
- You want enterprise-grade job management

---

## Executive Summary

### Feasibility: ✅ **APPLICABLE WITH ADAPTATIONS**

The backup/restore strategy can be successfully implemented in this codebase. The existing architecture provides a solid foundation:

- ✅ MySQL 8.4 database with SQLAlchemy ORM
- ✅ Organized file storage structure (`/app/uploads`)
- ✅ Docker Compose infrastructure
- ✅ FastAPI with service layer pattern
- ⚠️ Requires adaptation: No heavy job queue (will use database-backed polling)
- 🆕 New components needed: Backup worker service, maintenance mode, encryption

---

## Current Infrastructure Analysis

### Technology Stack
- **Framework**: FastAPI 0.128.0 (Python 3.14)
- **Database**: MySQL 8.4 with SQLAlchemy 2.0.46
- **ORM**: SQLAlchemy with Alembic migrations
- **Deployment**: Docker Compose with multi-environment support
- **Auth**: Cookie-based JWT with refresh tokens
- **File Storage**: `/app/uploads` with UUID-based directory structure

### Existing Capabilities

#### 1. Database Infrastructure ✅
```yaml
Current Setup:
  Database: MySQL 8.4
  ORM: SQLAlchemy 2.0.46
  Migrations: Alembic 1.18.3
  Models: 23 models (admins, orders, products, categories, etc.)
  Connection Pooling: Configured (size=5, max_overflow=5, pool_pre_ping=True)
```

**Backup Strategy Fit**:
- Can use `mysqldump` for consistent backups
- Database credentials already configured
- `pool_pre_ping=True` already set — handles reconnection automatically after a restore (no API restart needed)

#### 2. File Storage ✅
```
uploads/
├── products/
│   └── {uuid}/          # Product images
└── categories/
    └── {uuid}/          # Category images
```

**Backup Strategy Fit**:
- Clean, organized structure
- UUID-based directories prevent conflicts
- Already mounted as Docker volume
- Easy to archive with tar

#### 3. Docker Infrastructure ✅
```yaml
Current Services:
  - api (FastAPI application)
  - db (MySQL 8.4)

Networks:
  - frontend (external bridge)
  - backend (internal, isolated)

Volumes:
  - mysql_data (database)
  - uploads (file storage)
```

**Backup Strategy Fit**:
- Easy to add backup-worker and restore-worker services
- Network isolation already configured
- Volume management in place

#### 4. Async Processing ⚠️ **NEEDS ADAPTATION**
```python
Current Approach:
  - FastAPI BackgroundTasks (lightweight)
  - Asyncio event loop tasks (scheduled maintenance)
  - No Celery/RQ infrastructure
```

**Strategy Requirement**: Job queue for async backup execution

**Adaptation**: Use database-backed polling pattern instead of heavy job queue

---

## Key Design Decisions

These decisions were made during design review and supersede any conflicting guidance elsewhere in this document.

### Decision 1: Separate Metadata Stores for Backup vs Restore

**Problem**: Using the application DB as the source of truth for restore job progress is incoherent — the restore operation replaces the DB mid-job, wiping the job record.

**Decision**:
- **Backup job metadata** → application DB (`backups` table). Safe because `mysqldump --single-transaction` takes a consistent snapshot; writes to the `backups` table after the snapshot starts do not affect the backup.
- **Restore job state** → filesystem (`/app/backups/restore_<id>.state.json`). This file lives on the `backups` volume, which persists across DB restores. It is the authoritative source of truth during and after a restore operation.

The `restores` table in the DB tracks restore requests initiated from the current DB state (best-effort, pre-restore). During a restore, the worker writes all progress to the state file. After the restore completes and the DB is back up, the final state is readable from the file.

**API behaviour for `GET /api/v1/restores/{id}`**:
1. Query the `restores` table in the DB
2. If not found (DB was restored and wiped the record), check for `/app/backups/restore_<id>.state.json`
3. Return whichever source has more current information

### Decision 2: No Docker Socket Mount

**Problem**: Mounting `/var/run/docker.sock` gives the restore worker full root access to the Docker host, which is a critical security risk.

**Decision**: Do not mount the Docker socket. The API does not need to restart after a restore because `pool_pre_ping=True` is already configured in `app/core/database.py`. SQLAlchemy will automatically detect stale connections on first use and reconnect transparently. `RESTART_API` is removed from `RestoreStage`.

### Decision 3: Maintenance Mode via File Flag

**Problem**: Querying the DB on every request to check maintenance mode (Option A) adds latency under normal load for zero benefit 99.9% of the time, and fails if the DB is down during a restore.

**Decision**: Use a file flag (Option C). The restore worker creates `/app/flags/maintenance.flag` to enable maintenance mode and deletes it when done. The API middleware checks for this file's existence — a single filesystem stat call with no DB overhead.

A `flags` volume is shared between the `api` and `restore-worker` containers so they both see the same flag file.

### Decision 4: Mandatory Pre-restore Safety Snapshot + Auto-rollback

**Problem**: If a restore crashes mid-operation (specifically during `RESTORE_DB`), the database is in an unknown partial state. Simply marking the job as failed and requiring manual intervention leaves the system down until an admin acts.

**Decision**:
1. Before touching anything, the restore worker runs a fast local `mysqldump` to `/app/backups/safety_<restore_id>.sql`
2. If the restore fails at any stage, auto-rollback by replaying the safety snapshot
3. Maintenance mode stays on throughout — disabled only after successful restore **or** successful rollback
4. The state file records the final outcome (success, failed+rolled_back, failed+rollback_failed)
5. If the rollback itself fails, maintenance mode stays on and manual intervention is required — this is true disaster recovery territory

### Decision 5: Rate Limiting on Backup Creation

**Decision**: Enforce a maximum of 1 queued or running backup at a time, checked at the application layer (endpoint validation). Additionally, use the existing `slowapi` rate limiter on `POST /api/v1/backups` to prevent abuse.

### Decision 6: No Backup Download Endpoint

The API is a control plane only. It issues commands to the backup/restore workers; backup files never transit through the API. If admins need to retrieve backup files off-server, that is handled by external sync services (out of scope).

---

## What Needs Adaptation

### 1. Job Queue Architecture

#### Strategy Assumption
The generic strategy assumes a heavy job queue (Celery + Redis):
```
API → Redis Queue → Celery Worker → Execution
```

#### Our Adaptation: Database-Backed Polling
```
API → Database (backups table) → Backup Worker (polls) → Execution
```

**Implementation**:
```python
# Worker polling loop — uses asyncio.create_subprocess_exec, not subprocess.run
async def backup_worker_loop():
    while True:
        async with db.begin():
            job = db.execute(
                select(Backup)
                .filter(Backup.status == BackupStatus.QUEUED)
                .with_for_update(skip_locked=True)
                .limit(1)
            ).scalar_one_or_none()

            if job:
                job.status = BackupStatus.RUNNING
                job.started_at = datetime.now(timezone.utc).replace(tzinfo=None)

        if job:
            await execute_backup(job)

        await asyncio.sleep(5)
```

**Important**: all subprocess calls in workers must use `asyncio.create_subprocess_exec` (non-blocking), never `subprocess.run` (blocks the event loop).

**Pros**:
- ✅ No new dependencies (Redis, Celery)
- ✅ Simple to implement and maintain
- ✅ Fits lightweight architecture
- ✅ Database handles concurrency with row-level locks

**Cons**:
- ⚠️ Polling delay (5s typical)
- ⚠️ Less scalable for high-frequency jobs (fine for backups)

---

### 2. Maintenance Mode — File Flag

The maintenance mode flag is a plain file on a shared Docker volume visible to both the `api` and `restore-worker` containers.

```python
MAINTENANCE_FLAG_PATH = Path("/app/flags/maintenance.flag")

@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    # Always allow health/status endpoints
    allowed = {"/health", "/api/v1/system/status"}
    if request.url.path in allowed:
        return await call_next(request)

    if MAINTENANCE_FLAG_PATH.exists():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "System under maintenance. Please try again later.",
                "retry_after": 300
            }
        )

    return await call_next(request)
```

```python
# Restore worker — enable/disable maintenance mode
def enable_maintenance():
    MAINTENANCE_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAINTENANCE_FLAG_PATH.touch()

def disable_maintenance():
    MAINTENANCE_FLAG_PATH.unlink(missing_ok=True)
```

**Advantages over DB flag**:
- Zero DB overhead on every request
- Works even when the DB is down (during restore)
- Simpler to reason about

---

### 3. Backup Encryption

#### Recommended: Age Encryption
[Age](https://github.com/FiloSottile/age) is modern, simple, and secure.

**Installation**:
```dockerfile
# In Dockerfile
RUN apt-get update && apt-get install -y age
```

**Key Generation** (one-time):
```bash
age-keygen -o /secrets/backup-key.txt
# Public key printed to stdout — safe to store in env var
# Private key in file — keep secure
```

**Encryption Workflow** (using async subprocess):
```python
import asyncio

async def encrypt_backup(backup_path: str, public_key: str) -> str:
    encrypted_path = f"{backup_path}.age"
    proc = await asyncio.create_subprocess_exec(
        "age", "-e", "-r", public_key, "-o", encrypted_path, backup_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"age encryption failed: {stderr.decode()}")
    os.remove(backup_path)
    return encrypted_path

async def decrypt_backup(encrypted_path: str, private_key_path: str) -> str:
    decrypted_path = encrypted_path.replace(".age", "")
    proc = await asyncio.create_subprocess_exec(
        "age", "-d", "-i", private_key_path, "-o", decrypted_path, encrypted_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"age decryption failed: {stderr.decode()}")
    return decrypted_path
```

**Key Management**:
```yaml
services:
  backup-worker:
    environment:
      - BACKUP_PUBLIC_KEY=${BACKUP_PUBLIC_KEY}

  restore-worker:
    secrets:
      - backup-private-key          # Only the restore worker gets the private key

secrets:
  backup-private-key:
    file: ./secrets/backup-key.txt
```

**Security**:
- ✅ Public key in environment variables (safe to expose)
- ✅ Private key ONLY in Docker secrets, never in database/code
- ✅ Private key ONLY available to restore worker, not API or backup worker
- ✅ Use different keys per environment

---

## Proposed Architecture

### System Overview

```
┌─────────────────┐
│   Frontend      │
│   (React/Vue)   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────────────────┐
│  API Container (FastAPI)                    │
│                                             │
│  POST /api/v1/backups                       │
│    → Validate (reject if one already        │
│      queued/running), create DB record      │
│                                             │
│  GET /api/v1/backups                        │
│    → List backups with status               │
│                                             │
│  GET /api/v1/backups/{id}                   │
│    → Get backup status & progress           │
│                                             │
│  DELETE /api/v1/backups/{id}                │
│    → Delete backup record + file            │
│                                             │
│  POST /api/v1/restores                      │
│    → Create DB record (status=queued)       │
│                                             │
│  GET /api/v1/restores/{id}                  │
│    → Check DB, fall back to state file      │
│                                             │
│  GET /api/v1/system/status                  │
│    → Check maintenance flag file            │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐  ┌──────────────────────────┐
│  MySQL Database  │  │  flags volume             │
│                  │  │                           │
│  - backups       │  │  /app/flags/              │
│  - restores      │  │    maintenance.flag       │
│  - [23 existing] │  │    (created/deleted by    │
│                  │  │    restore-worker)        │
└────────┬─────────┘  └──────────────────────────┘
         │ Polls every 5s
         ▼
┌─────────────────────────────────────────────┐
│  Backup Worker Container                    │
│                                             │
│  while True:                                │
│    job = poll_queued_backups()              │
│    if job:                                  │
│      1. mysqldump database                  │
│      2. tar /uploads directory              │
│      3. encrypt archive (age)               │
│      4. calculate checksum (SHA-256)        │
│      5. update progress in DB               │
│      6. mark completed in DB               │
│      7. clean up old backups (retention)   │
│    sleep(5)                                 │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Restore Worker Container                   │
│                                             │
│  while True:                                │
│    job = poll_queued_restores()             │
│    if job:                                  │
│      1. write state file (restore ID)      │
│      2. take safety snapshot (mysqldump)   │
│      3. enable maintenance mode (flag)     │
│      4. decrypt & verify backup            │
│      5. restore database                   │
│      6. restore files                      │
│      7. run migrations                     │
│      8. validate restore                   │
│      9. disable maintenance mode           │
│     10. update state file: completed       │
│                                             │
│    on failure at any step:                  │
│      → rollback using safety snapshot      │
│      → disable maintenance mode            │
│      → update state file: failed+rolled_back│
│    sleep(5)                                 │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Backup Storage Volume (/app/backups)        │
│                                             │
│  backup_20260219_120000.tar.gz.age          │
│  backup_20260219_120000.meta.json           │
│  safety_<restore_id>.sql    ← pre-restore   │
│  restore_<restore_id>.state.json ← progress │
└─────────────────────────────────────────────┘
```

### Restore State File Schema

`/app/backups/restore_<id>.state.json`:
```json
{
  "id": "uuid",
  "backup_id": "uuid",
  "status": "running|completed|failed|rolled_back",
  "stage": "safety_snapshot|maintenance_mode|decrypt|verify|restore_db|...",
  "progress": 60,
  "started_at": "2026-02-19T12:00:00",
  "completed_at": null,
  "error_message": null
}
```

### Docker Compose Configuration

```yaml
# docker-compose.yml additions
services:
  # Existing services: api, db

  api:
    # ... existing config ...
    volumes:
      - flags:/app/flags            # Read maintenance flag

  backup-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: python -m app.workers.backup_worker
    container_name: backup-worker
    environment:
      - ENVIRONMENT=production
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
      - BACKUP_PUBLIC_KEY=${BACKUP_PUBLIC_KEY}
      - BACKUP_RETENTION_DAYS=30
    volumes:
      - ./uploads:/app/uploads:ro       # Read-only: archive uploads
      - backups:/app/backups            # Write: store backup archives
    networks:
      - backend
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  restore-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: python -m app.workers.restore_worker
    container_name: restore-worker
    environment:
      - ENVIRONMENT=production
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
    volumes:
      - ./uploads:/app/uploads          # Write: restore file tree
      - backups:/app/backups            # Write: state files, safety snapshots
      - flags:/app/flags                # Write: maintenance.flag
    secrets:
      - backup-private-key
    networks:
      - backend
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

volumes:
  backups:
    driver: local
  flags:
    driver: local

secrets:
  backup-private-key:
    file: ./secrets/backup-key.txt
```

**Note**: No `/var/run/docker.sock` mount. The API does not need to restart after a restore because `pool_pre_ping=True` is already configured — SQLAlchemy detects and replaces stale connections automatically.

---

## Implementation Plan

### Phase 1: Database Schema & Models (1 day)

#### 1.1 Create Database Models

**File**: `app/models/backup.py`

```python
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, BigInteger, JSON
from sqlalchemy.dialects.mysql import CHAR
from app.core.database import Base
import enum
import uuid
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class BackupStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class BackupStage(str, enum.Enum):
    INITIALIZED = "initialized"
    DB_DUMP = "db_dump"
    FILE_ARCHIVE = "file_archive"
    ENCRYPTION = "encryption"
    CHECKSUM = "checksum"
    STORAGE = "storage"
    COMPLETED = "completed"

class Backup(Base):
    __tablename__ = "backups"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(Enum(BackupStatus), nullable=False, default=BackupStatus.QUEUED, index=True)
    stage = Column(Enum(BackupStage), nullable=False, default=BackupStage.INITIALIZED)
    progress = Column(Integer, default=0)  # 0-100

    backup_path = Column(String(500))          # Full path to .tar.gz.age file
    size_bytes = Column(BigInteger)
    checksum = Column(String(64))              # SHA-256 hex

    backup_metadata = Column(JSON)             # Avoid collision with SQLAlchemy's .metadata attribute

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_now, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_by = Column(Integer, nullable=True)   # Admin ID

class RestoreStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class RestoreStage(str, enum.Enum):
    INITIALIZED = "initialized"
    SAFETY_SNAPSHOT = "safety_snapshot"
    MAINTENANCE_MODE = "maintenance_mode"
    DECRYPT = "decrypt"
    VERIFY = "verify"
    RESTORE_DB = "restore_db"
    RESTORE_FILES = "restore_files"
    MIGRATE = "migrate"
    VALIDATE = "validate"
    COMPLETED = "completed"
    # Note: RESTART_API stage removed — pool_pre_ping=True handles reconnection automatically

class Restore(Base):
    __tablename__ = "restores"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_id = Column(CHAR(36), nullable=False, index=True)

    status = Column(Enum(RestoreStatus), nullable=False, default=RestoreStatus.QUEUED, index=True)
    stage = Column(Enum(RestoreStage), nullable=False, default=RestoreStage.INITIALIZED)
    progress = Column(Integer, default=0)

    # Path to the pre-restore safety snapshot SQL file (on backup volume)
    safety_snapshot_path = Column(String(500), nullable=True)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_now, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_by = Column(Integer, nullable=True)
```

**Notable changes from original plan**:
- `metadata` renamed to `backup_metadata` — `metadata` is a reserved attribute on SQLAlchemy `Base` subclasses
- `datetime.utcnow` replaced with `_now()` — MySQL TIMESTAMP columns return naive datetimes; using `datetime.now(timezone.utc).replace(tzinfo=None)` avoids the deprecated call and keeps comparisons consistent
- `SystemSettings` model removed — maintenance mode uses a file flag, not a DB row
- `RESTART_API` removed from `RestoreStage`
- `pre_restore_snapshot_id` replaced with `safety_snapshot_path` (direct file path)

#### 1.2 Create Pydantic Schemas

**File**: `app/schemas/backup.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.backup import BackupStatus, BackupStage, RestoreStatus, RestoreStage

class BackupCreate(BaseModel):
    pass  # No parameters — backup always captures full current state

class BackupResponse(BaseModel):
    id: str
    status: BackupStatus
    stage: BackupStage
    progress: int = Field(ge=0, le=100)
    backup_path: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    backup_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RestoreCreate(BaseModel):
    backup_id: str

class RestoreResponse(BaseModel):
    id: str
    backup_id: str
    status: RestoreStatus
    stage: RestoreStage
    progress: int = Field(ge=0, le=100)
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SystemStatusResponse(BaseModel):
    maintenance_mode: bool
```

**Deliverables**:
- ✅ Database models created
- ✅ Alembic migration generated and applied
- ✅ Pydantic schemas defined

---

### Phase 2: API Endpoints (1 day)

**File**: `app/api/endpoints/backups.py`

**Key Endpoints**:
- `POST /api/v1/backups` — Create backup job (reject if one already queued/running; rate-limited via slowapi)
- `GET /api/v1/backups` — List backups
- `GET /api/v1/backups/{id}` — Get backup status & progress
- `DELETE /api/v1/backups/{id}` — Delete backup record and archive file

**File**: `app/api/endpoints/restores.py`

**Key Endpoints**:
- `POST /api/v1/restores` — Initiate restore (creates DB record + queues job)
- `GET /api/v1/restores/{id}` — Get restore status (checks DB, falls back to state file if DB record missing post-restore)

**File**: `app/api/endpoints/system_config.py` (extend existing)

**Key Endpoints**:
- `GET /api/v1/system/status` — Returns `{"maintenance_mode": true/false}` by checking flag file

**Rate Limiting** (`POST /api/v1/backups`):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

@router.post("/backups")
@limiter.limit("5/hour")
async def create_backup(request: Request, db: Session = Depends(get_db), ...):
    # Reject if a backup is already queued or running
    active = db.query(Backup).filter(
        Backup.status.in_([BackupStatus.QUEUED, BackupStatus.RUNNING])
    ).first()
    if active:
        raise HTTPException(409, "A backup is already in progress")
    ...
```

---

### Phase 3: Backup Worker Service (2 days)

**File**: `app/workers/backup_worker.py`

Polling worker that:
1. Polls DB for queued backup jobs using `SELECT ... FOR UPDATE SKIP LOCKED`
2. Claims job atomically, sets `status=running`
3. Runs `mysqldump --single-transaction` via `asyncio.create_subprocess_exec`
4. Archives `/app/uploads` with `tar`
5. Encrypts with `age`
6. Calculates SHA-256 checksum
7. Updates `backups` DB record throughout (progress, stage, final status)
8. Cleans up backups older than `BACKUP_RETENTION_DAYS`

**Stale job detection**: On startup and periodically, reset any `running` jobs older than 2 hours to `failed` (these are from a previous worker crash).

---

### Phase 4: Restore Worker Service (2 days)

**File**: `app/workers/restore_worker.py`

Polling worker that:
1. Polls DB for queued restore jobs
2. Creates state file: `/app/backups/restore_<id>.state.json`
3. Takes pre-restore safety snapshot: `mysqldump` → `/app/backups/safety_<id>.sql`
4. Enables maintenance mode: `touch /app/flags/maintenance.flag`
5. Decrypts and verifies backup checksum
6. Restores database via `mysql` CLI
7. Restores file tree from tar archive
8. Runs Alembic migrations
9. Validates restore (smoke-check DB connectivity, row counts)
10. Disables maintenance mode: `rm /app/flags/maintenance.flag`
11. Updates state file: `status=completed`

**On failure at any step**:
```
→ Run safety snapshot restore (mysql < safety_<id>.sql)
→ Restore original file tree if partially overwritten
→ Disable maintenance mode
→ Update state file: status=failed, error_message=...
→ If rollback also fails: leave maintenance mode ON, alert admin
```

**Note**: After restore, the DB has been replaced with the backup's state. The `restores` table in the DB no longer contains the current restore job record. The state file is the authoritative outcome record.

---

### Phase 5: Docker Integration (0.5 day)

Update `docker-compose.yml` and `Dockerfile` to:
- Add `backup-worker` service
- Add `restore-worker` service
- Add `backups` and `flags` named volumes
- Mount `flags` volume into both `api` and `restore-worker`
- Install `age`, `mysqldump`, `mysql` client in Dockerfile
- Add `backup-private-key` secret for restore-worker only
- Add maintenance mode middleware to `app/main.py`

---

### Phase 6: Testing & Documentation (1 day)

- Integration tests for backup creation flow
- Integration tests for restore flow (including maintenance mode verification)
- Integration tests for rollback on simulated failure
- Manual testing guide
- API documentation updates

---

## Key Adaptations from Generic Strategy

| Generic Strategy | Our Implementation |
|-----------------|-------------------|
| **Job Queue** | Celery/RQ with Redis → Database-backed polling (5s interval) |
| **Database** | Generic RDBMS → MySQL 8.4 with `mysqldump` |
| **File Storage** | Generic uploads → UUID-based structure (`products/{uuid}/`) |
| **Worker Architecture** | Heavy Celery workers → Lightweight Python polling containers |
| **Job Claiming** | Push-based (instant) → Poll-based (5s delay acceptable) |
| **Orchestration** | Complex job queuing → Simple status-based state machine |
| **Encryption** | Generic (GPG/KMS) → Age encryption (modern, simple) |
| **Deployment** | Kubernetes/complex → Docker Compose (fits existing infra) |
| **Restore metadata** | Application DB → Filesystem state file (survives DB restore) |
| **Maintenance mode** | In-memory/Redis → File flag on shared volume (zero DB overhead) |

---

## Security Considerations

### 1. Encryption Keys

- ✅ Public key: Environment variable (safe to expose)
- ✅ Private key: Docker secret (never in code/database)
- ✅ Private key only on restore worker, not API or backup worker
- ✅ Use different keys per environment
- ⚠️ Key rotation procedure needed (document separately)

### 2. Database Credentials

- ✅ Backup worker: can use read-only DB credentials (only reads application tables)
- ⚠️ Restore worker: needs full write access (destructive by nature)
- ✅ Credentials in environment variables
- ⚠️ Consider Docker secrets for production DB passwords

### 3. Access Control

- ✅ Backup endpoints: Admin-only
- ✅ Restore endpoints: Admin-only
- ✅ Maintenance mode status: Public read (system status), admin write
- ⚠️ Consider requiring a confirmation token for restore operations (separate UX flow)

### 4. No Docker Socket

- ✅ `pool_pre_ping=True` is already configured — no API restart needed post-restore
- ✅ No privileged container access required

---

## Production Readiness Checklist

### Before Deploying

- [ ] Generate production encryption keys (`age-keygen`)
- [ ] Store private key securely (Docker secret or secret manager)
- [ ] Test full backup → restore → validate cycle end-to-end
- [ ] Test rollback on simulated mid-restore failure
- [ ] Test maintenance mode blocks requests correctly
- [ ] Configure backup retention policy (`BACKUP_RETENTION_DAYS`)
- [ ] Document disaster recovery runbook
- [ ] Set up scheduled automated backups (cron or scheduler)
- [ ] Configure alerting for failed backups
- [ ] Set up audit logging for backup/restore operations
- [ ] Configure external sync for backup files (out of scope for this system)

---

## Questions & Decisions Still Open

1. **Backup Frequency**: How often should automated backups run?
2. **Retention Policy**: How long to keep backups? (default: 30 days)
3. **Restore Safeguards**: Require a confirmation token in addition to admin auth?
4. **Notification Requirements**: Email/webhook on backup completion or failure?
5. **Safety Snapshot Retention**: How long to keep pre-restore safety snapshots?

---

## References

- [Original Strategy Document](api_backup_restore_strategy.md)
- [Existing Synchronous Plan](BACKUP_RESTORE_IMPLEMENTATION_PLAN.md)
- [Age Encryption](https://github.com/FiloSottile/age)
- [MySQL Backup Best Practices](https://dev.mysql.com/doc/refman/8.0/en/backup-types.html)
- [SQLAlchemy Row Locking](https://docs.sqlalchemy.org/en/14/orm/queryguide.html#orm-queryguide-selecting-locking)
