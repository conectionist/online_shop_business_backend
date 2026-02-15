# Backup & Restore - Async Worker Implementation Plan

## Overview

This document outlines the plan to implement the backup and restore strategy described in [api_backup_restore_strategy.md](api_backup_restore_strategy.md) for this FastAPI backend application using an **asynchronous worker-based architecture**.

**Status**: Planning Phase
**Last Updated**: 2026-02-12
**Target**: Production-ready backup/restore system with async job workers

---

## Comparison with Existing Plan

This codebase already has a [synchronous implementation plan](BACKUP_RESTORE_IMPLEMENTATION_PLAN.md). Here's how this async worker approach differs:

| Aspect | Existing Plan (Synchronous) | This Plan (Async Workers) |
|--------|---------------------------|--------------------------|
| **Execution** | Direct API execution | Background workers poll jobs |
| **Progress Tracking** | Not available (blocking request) | Real-time progress in database |
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

**Estimated Effort**: 2-3 days for MVP, 1 week for production-ready implementation

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
  Connection Pooling: Configured (size=5, max_overflow=5)
```

**Backup Strategy Fit**:
- Can use `mysqldump` for consistent backups
- Database credentials already configured
- Connection settings optimized for production

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
- Easy to archive with tar/rsync

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
- Easy to add backup-worker service
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

## What Needs Adaptation

### 1. Job Queue Architecture

#### Strategy Assumption
The generic strategy assumes a heavy job queue (Celery + Redis):
```
API → Redis Queue → Celery Worker → Execution
```

#### Our Adaptation: Database-Backed Polling
```
API → Database (backups table) → Python Worker (polls) → Execution
```

**Implementation**:
```python
# Worker polling loop
async def backup_worker_loop():
    while True:
        # Atomic job claiming with database transaction
        async with db.transaction():
            job = await db.query(Backup)\
                .filter(Backup.status == 'queued')\
                .with_for_update(skip_locked=True)\
                .first()

            if job:
                job.status = 'running'
                await db.commit()
                await execute_backup(job)

        await asyncio.sleep(5)  # Poll interval
```

**Pros**:
- ✅ No new dependencies (Redis, Celery)
- ✅ Simple to implement and maintain
- ✅ Fits lightweight architecture
- ✅ Database handles concurrency with row-level locks

**Cons**:
- ⚠️ Polling delay (5s typical)
- ⚠️ Less scalable for high-frequency jobs (fine for backups)

**Alternative**: Add Celery later if needed for other background tasks

---

### 2. Maintenance Mode (New Feature)

#### Requirement
During restore operations, the API must enter maintenance mode to:
- Block all incoming requests
- Prevent data modifications during restore
- Display maintenance message to users

#### Implementation Options

**Option A: Database Flag** (Recommended)
```python
# Model
class SystemSettings(Base):
    __tablename__ = 'system_settings'
    id = Column(Integer, primary_key=True)
    maintenance_mode = Column(Boolean, default=False)
    maintenance_message = Column(String(500))

# Middleware
@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    # Skip for admin/health endpoints
    if request.url.path in ["/health", "/api/v1/system/status"]:
        return await call_next(request)

    db = next(get_db())
    settings = db.query(SystemSettings).first()

    if settings and settings.maintenance_mode:
        return JSONResponse(
            status_code=503,
            content={
                "detail": settings.maintenance_message or "System under maintenance",
                "retry_after": 300  # 5 minutes
            }
        )

    return await call_next(request)
```

**Option B: Redis Flag** (if Redis available)
```python
# Fast in-memory check
if await redis.get("maintenance_mode") == "true":
    raise ServiceUnavailable()
```

**Option C: File Flag** (simplest, no DB hit)
```python
# Check for maintenance file
if os.path.exists("/tmp/maintenance.flag"):
    raise ServiceUnavailable()
```

**Recommendation**: Start with Option A (database), migrate to Redis if performance needed

---

### 3. Backup Encryption (New Capability)

#### Requirement
Backups must be encrypted before storage to protect sensitive data.

#### Recommended: Age Encryption
[Age](https://github.com/FiloSottile/age) is modern, simple, and secure.

**Installation**:
```dockerfile
# In Dockerfile
RUN apt-get update && apt-get install -y age
```

**Key Generation** (one-time):
```bash
# Generate key pair
age-keygen -o /secrets/backup-key.txt

# Output:
# Public key: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
# (Keep private key secure!)
```

**Encryption Workflow**:
```python
import subprocess

async def encrypt_backup(backup_path: str, public_key: str) -> str:
    """Encrypt backup file using age."""
    encrypted_path = f"{backup_path}.age"

    cmd = [
        "age",
        "-e",                          # encrypt
        "-r", public_key,              # recipient public key
        "-o", encrypted_path,          # output file
        backup_path                    # input file
    ]

    result = subprocess.run(cmd, capture_output=True, check=True)

    # Remove unencrypted backup
    os.remove(backup_path)

    return encrypted_path

async def decrypt_backup(encrypted_path: str, private_key_path: str) -> str:
    """Decrypt backup file using age."""
    decrypted_path = encrypted_path.replace(".age", "")

    cmd = [
        "age",
        "-d",                          # decrypt
        "-i", private_key_path,        # identity (private key)
        "-o", decrypted_path,          # output file
        encrypted_path                 # input file
    ]

    result = subprocess.run(cmd, capture_output=True, check=True)

    return decrypted_path
```

**Key Management**:
```yaml
# docker-compose.yml
services:
  backup-worker:
    environment:
      - BACKUP_PUBLIC_KEY=age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
    secrets:
      - backup-private-key

secrets:
  backup-private-key:
    file: ./secrets/backup-key.txt
```

**Security**:
- ✅ Public key can be in environment variables
- ✅ Private key ONLY in secrets, never in database/code
- ✅ Private key ONLY available to restore worker, not API
- ✅ Use different keys for different environments

**Alternative**: GPG, AWS KMS, or HashiCorp Vault for enterprise

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
│  POST /api/v1/backups                      │
│    → Create backup record (status=queued)  │
│                                             │
│  GET /api/v1/backups                       │
│    → List all backups with status          │
│                                             │
│  GET /api/v1/backups/{id}                  │
│    → Get backup status & progress          │
│                                             │
│  POST /api/v1/restores                     │
│    → Initiate restore (status=queued)      │
│                                             │
│  POST /api/v1/system/maintenance           │
│    → Enable/disable maintenance mode       │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MySQL Database                             │
│                                             │
│  Tables:                                    │
│    - backups (id, status, progress, ...)   │
│    - restores (id, backup_id, status, ...) │
│    - system_settings (maintenance_mode)    │
│    - [23 existing tables]                  │
└────────┬────────────────────────────────────┘
         │
         │ Polls every 5s
         ▼
┌─────────────────────────────────────────────┐
│  Backup Worker Container                    │
│                                             │
│  while True:                                │
│    job = poll_queued_backups()             │
│    if job:                                  │
│      1. mysqldump database                 │
│      2. tar /uploads directory             │
│      3. encrypt archive                    │
│      4. calculate checksum                 │
│      5. update progress                    │
│      6. mark completed                     │
│    sleep(5)                                 │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Restore Worker Container                   │
│                                             │
│  while True:                                │
│    job = poll_queued_restores()            │
│    if job:                                  │
│      1. enable maintenance mode            │
│      2. download & decrypt backup          │
│      3. verify checksum                    │
│      4. restore database                   │
│      5. restore files                      │
│      6. run migrations                     │
│      7. validate restore                   │
│      8. disable maintenance mode           │
│      9. mark completed                     │
│    sleep(5)                                 │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Backup Storage Volume                      │
│                                             │
│  /backups/                                  │
│    ├── backup_20260212_120000.tar.gz.age  │
│    ├── backup_20260212_120000.meta.json   │
│    ├── backup_20260211_180000.tar.gz.age  │
│    └── backup_20260211_180000.meta.json   │
└─────────────────────────────────────────────┘
```

### Docker Compose Configuration

```yaml
# docker-compose.yml additions
services:
  # Existing services: api, db

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
      - ./uploads:/app/uploads:ro           # Read-only access
      - ./backups:/app/backups              # Write access
      - mysql_data:/var/lib/mysql:ro        # Optional: for LVM snapshots
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
      - ./uploads:/app/uploads              # Write access
      - ./backups:/app/backups:ro           # Read-only access
      - /var/run/docker.sock:/var/run/docker.sock  # For restarting API
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

secrets:
  backup-private-key:
    file: ./secrets/backup-key.txt
```

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
from datetime import datetime

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

    # Backup metadata
    backup_filename = Column(String(255))
    backup_path = Column(String(500))
    size_bytes = Column(BigInteger)
    checksum = Column(String(64))  # SHA-256

    # Metadata JSON
    metadata = Column(JSON)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Admin tracking
    created_by = Column(Integer, nullable=True)

class RestoreStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class RestoreStage(str, enum.Enum):
    INITIALIZED = "initialized"
    MAINTENANCE_MODE = "maintenance_mode"
    DOWNLOAD = "download"
    DECRYPT = "decrypt"
    VERIFY = "verify"
    RESTORE_DB = "restore_db"
    RESTORE_FILES = "restore_files"
    MIGRATE = "migrate"
    VALIDATE = "validate"
    RESTART_API = "restart_api"
    COMPLETED = "completed"

class Restore(Base):
    __tablename__ = "restores"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_id = Column(CHAR(36), nullable=False, index=True)

    status = Column(Enum(RestoreStatus), nullable=False, default=RestoreStatus.QUEUED, index=True)
    stage = Column(Enum(RestoreStage), nullable=False, default=RestoreStage.INITIALIZED)
    progress = Column(Integer, default=0)

    # Pre-restore snapshot (for rollback)
    pre_restore_snapshot_id = Column(CHAR(36), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Admin tracking
    created_by = Column(Integer, nullable=True)

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    maintenance_mode = Column(Integer, default=0)  # 0=false, 1=true
    maintenance_message = Column(String(500), default="System under maintenance. Please try again later.")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 1.2 Create Pydantic Schemas

**File**: `app/schemas/backup.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.backup import BackupStatus, BackupStage, RestoreStatus, RestoreStage

class BackupCreate(BaseModel):
    """Request to create a backup."""
    pass

class BackupResponse(BaseModel):
    id: str
    status: BackupStatus
    stage: BackupStage
    progress: int = Field(ge=0, le=100)
    backup_filename: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
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

class MaintenanceModeUpdate(BaseModel):
    enabled: bool
    message: Optional[str] = "System under maintenance. Please try again later."

class SystemStatusResponse(BaseModel):
    maintenance_mode: bool
    maintenance_message: Optional[str] = None
```

**Deliverables**:
- ✅ Database models created
- ✅ Alembic migration generated and applied
- ✅ Pydantic schemas defined

---

### Phase 2: API Endpoints (1 day)

Create endpoints for backup/restore operations and system status.

**File**: `app/api/endpoints/backups.py`

See full implementation in Phase 2 of the detailed plan.

**Key Endpoints**:
- `POST /api/v1/backups` - Create backup job
- `GET /api/v1/backups` - List backups
- `GET /api/v1/backups/{id}` - Get backup status
- `DELETE /api/v1/backups/{id}` - Delete backup
- `POST /api/v1/restores` - Initiate restore
- `GET /api/v1/restores/{id}` - Get restore status
- `POST /api/v1/system/maintenance` - Toggle maintenance mode
- `GET /api/v1/system/status` - Get system status

---

### Phase 3: Backup Worker Service (2 days)

**File**: `app/workers/backup_worker.py`

Polling worker that:
1. Polls database for queued backup jobs
2. Claims jobs atomically using database locks
3. Executes backup (dump DB, archive files, encrypt, checksum)
4. Updates progress in database
5. Stores backup and metadata
6. Auto-cleanup of old backups

See full implementation in documentation.

---

### Phase 4: Restore Worker Service (2 days)

**File**: `app/workers/restore_worker.py`

Polling worker that:
1. Polls database for queued restore jobs
2. Enables maintenance mode
3. Decrypts and verifies backup
4. Creates safety backup (for rollback)
5. Restores database and files
6. Runs migrations
7. Validates restore
8. Disables maintenance mode

See full implementation in documentation.

---

### Phase 5: Docker Integration (0.5 day)

Update Docker Compose and Dockerfile to:
- Add backup-worker service
- Add restore-worker service
- Install required tools (mysqldump, rsync, age)
- Configure volumes and secrets
- Set up proper networking

---

### Phase 6: Testing & Documentation (1 day)

- Integration tests for backup/restore flow
- Manual testing guide
- API documentation updates
- README updates

---

## Key Adaptations from Generic Strategy

| Generic Strategy | Our Implementation |
|-----------------|-------------------|
| **Job Queue** | Celery/RQ with Redis | Database-backed polling (5s interval) |
| **Database** | Generic RDBMS | MySQL 8.4 with `mysqldump` |
| **File Storage** | Generic uploads | UUID-based structure (`products/{uuid}/`) |
| **Worker Architecture** | Heavy Celery workers | Lightweight Python polling containers |
| **Job Claiming** | Push-based (instant) | Poll-based (5s delay acceptable) |
| **Orchestration** | Complex job queuing | Simple status-based state machine |
| **Encryption** | Generic (GPG/KMS) | Age encryption (modern, simple) |
| **Deployment** | Kubernetes/complex | Docker Compose (fits existing infra) |

---

## Security Considerations

### 1. Encryption Keys

- ✅ Public key: Environment variable (safe to expose)
- ✅ Private key: Docker secret (never in code/database)
- ✅ Private key only on restore worker
- ✅ Different keys per environment
- ⚠️ Key rotation procedure needed

### 2. Database Credentials

- ✅ Workers have read-only DB credentials (backup)
- ⚠️ Restore worker needs write access (destructive)
- ✅ Credentials in environment variables
- ⚠️ Consider using Docker secrets for production

### 3. Access Control

- ✅ Backup endpoints: Admin-only
- ✅ Restore endpoints: Admin-only (super dangerous!)
- ✅ Maintenance mode: Admin-only
- ⚠️ Consider requiring 2FA for restore operations

---

## Production Readiness Checklist

### Before Deploying

- [ ] Generate production encryption keys
- [ ] Store private key in secure secret manager
- [ ] Configure offsite backup storage (S3/etc)
- [ ] Set up backup monitoring/alerting
- [ ] Test full restore procedure
- [ ] Document disaster recovery runbook
- [ ] Set up scheduled automated backups
- [ ] Configure backup retention policy
- [ ] Test maintenance mode behavior
- [ ] Add 2FA requirement for restores
- [ ] Set up audit logging
- [ ] Configure alerting for failed backups

---

## Estimated Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Database schema & models | 1 day |
| 2 | API endpoints | 1 day |
| 3 | Backup worker service | 2 days |
| 4 | Restore worker service | 2 days |
| 5 | Docker integration | 0.5 day |
| 6 | Testing & documentation | 1 day |
| **Total** | **MVP Implementation** | **7.5 days** |

---

## Next Steps

1. **Review both plans**: Compare this async plan with the [existing synchronous plan](BACKUP_RESTORE_IMPLEMENTATION_PLAN.md)
2. **Choose approach**: Decide based on your requirements:
   - Synchronous: Simpler, faster to implement, good for small databases
   - Async (this plan): More robust, better UX, good for large databases
3. **Generate encryption keys** for development
4. **Begin Phase 1** (database schema)

---

## Questions & Decisions Needed

1. **Backup Frequency**: How often should automated backups run?
2. **Retention Policy**: How long to keep backups? (default: 30 days)
3. **Storage Location**: Local volume or S3/remote storage?
4. **Restore Safeguards**: Require 2FA? Confirmation token?
5. **Notification Requirements**: Email/Slack on completion?

---

## References

- [Original Strategy Document](api_backup_restore_strategy.md)
- [Existing Synchronous Plan](BACKUP_RESTORE_IMPLEMENTATION_PLAN.md)
- [Age Encryption](https://github.com/FiloSottile/age)
- [MySQL Backup Best Practices](https://dev.mysql.com/doc/refman/8.0/en/backup-types.html)
- [SQLAlchemy Row Locking](https://docs.sqlalchemy.org/en/14/orm/queryguide.html#orm-queryguide-selecting-locking)
