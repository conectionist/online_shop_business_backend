# Backup and Restore Implementation Plan

## Table of Contents
1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Architecture and Design Decisions](#architecture-and-design-decisions)
4. [File Structure](#file-structure)
5. [Implementation Steps](#implementation-steps)
6. [Detailed Component Specifications](#detailed-component-specifications)
7. [Configuration](#configuration)
8. [Error Handling](#error-handling)
9. [Security Considerations](#security-considerations)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Considerations](#deployment-considerations)

---

## Overview

This document outlines the complete implementation plan for backup and restore functionality in the Online Shop Business Backend. The system will allow administrators to:

- Create backups of database and uploaded files via API endpoints
- Restore backups to the same or different server instances
- Optionally encrypt backups for security
- Automatically handle maintenance mode during operations
- Ensure data integrity with safety backups and rollback mechanisms

### Key Principles

1. **Application Data Only**: Backups contain only application-specific data (database, uploads). No Docker configuration, environment variables, or infrastructure details.
2. **Database User Agnostic**: Backups can be restored regardless of MySQL username/password changes between backup and restore.
3. **All-or-Nothing Restore**: Restore operations are atomic - either fully succeed or fully rollback.
4. **Maintenance Mode**: System enters maintenance mode during backup/restore to prevent data inconsistencies.
5. **Safety First**: Always create safety backup before restore, with automatic rollback on failure.

---

## Requirements

### Functional Requirements

1. **Backup Creation**
   - Create backup via `POST /api/v1/admin/backup` endpoint
   - Include MySQL database dump (all tables and data)
   - Include all uploaded files (product images, category images, etc.)
   - Optional encryption with user-provided password
   - Return backup as downloadable archive
   - Include metadata (API version, timestamp, database name, size)

2. **Backup Restoration**
   - Restore backup via `POST /api/v1/admin/restore` endpoint
   - Accept backup archive file upload
   - Validate backup format before restoration
   - Create safety backup before restore
   - Drop all existing data (clean slate restore)
   - Restore database from SQL dump
   - Restore uploaded files
   - Rollback on any failure
   - Return detailed success/error information

3. **Maintenance Mode**
   - Automatically enable during backup operations
   - Automatically enable during restore operations
   - Block all write operations (POST, PUT, PATCH, DELETE)
   - Allow read operations (GET)
   - Allow backup/restore endpoints (admin-only)
   - Return 503 Service Unavailable with message during maintenance

4. **Concurrent Operations Protection**
   - Prevent multiple backup/restore operations simultaneously
   - File-based locking mechanism
   - Configurable timeout (default: 10 minutes)
   - Clear error messages when operation in progress

### Non-Functional Requirements

1. **Performance**
   - Support backups up to 2GB (configurable, default)
   - Stream large files to avoid memory issues
   - Complete backup in reasonable time (< 10 minutes for typical size)

2. **Security**
   - Admin-only access (JWT authentication required)
   - Optional encryption for backups
   - No sensitive data in logs
   - Generic error messages to users, detailed in logs

3. **Reliability**
   - All-or-nothing restore operations
   - Automatic rollback on failure
   - Safety backup before restore
   - Transaction support where possible

4. **Usability**
   - Simple API interface
   - Clear error messages
   - Progress indication (via logs)
   - Configurable limits and timeouts

---

## Architecture and Design Decisions

### Backup Archive Structure

```
backup_YYYYMMDD_HHMMSS.tar.gz
├── database.sql          # MySQL dump (processed to be user-agnostic)
├── uploads/             # Uploaded files directory (preserves structure)
│   ├── categories/
│   ├── products/
│   └── ...
└── metadata.json        # Backup metadata
```

### Metadata Structure

```json
{
  "api_version": "5.3.0",
  "backup_timestamp": "2026-01-15T10:30:00Z",
  "backup_format_version": "1.0",
  "database_name": "shopdb1",
  "backup_size_bytes": 524288000,
  "encrypted": false
}
```

### Database Dump Strategy

**mysqldump Flags:**
- `--single-transaction`: Consistent snapshot (InnoDB)
- `--routines`: Include stored procedures/functions
- `--triggers`: Include triggers
- `--no-create-db`: Don't include CREATE DATABASE
- `--skip-add-drop-database`: Don't include DROP DATABASE
- `--skip-lock-tables`: Don't lock tables (single-transaction handles this)
- `--skip-tz-utc`: Avoid timezone issues

**Database Name Handling:**
1. Check if original DB name (from backup) matches current DB name (from env)
2. If match: Strip all `USE database_name;` statements (connection already targets correct DB)
3. If different: Replace `USE old_db;` with `USE current_db;` (from environment)
4. Add `SET FOREIGN_KEY_CHECKS=0;` at start, `SET FOREIGN_KEY_CHECKS=1;` at end

### Restore Process Flow

```
1. Validate backup file format
2. Check maintenance mode (should be enabled)
3. Create safety backup (database + uploads)
4. Extract backup archive to temp location
5. Process database.sql (handle USE statements)
6. Start database transaction
7. Drop all tables (or truncate)
8. Restore database from processed SQL
9. Commit transaction (or rollback on error)
10. Backup existing uploads directory
11. Restore uploads directory
12. If any step fails → rollback from safety backup
13. Clean up temp files
14. Return success/error response
```

### Maintenance Mode Strategy

**State Management:**
- Thread-safe flag (in-memory with file-based persistence for multi-worker)
- File lock: `/tmp/backup_restore.lock`
- Maintenance flag file: `/tmp/maintenance_mode.flag`

**Middleware Behavior:**
- Check maintenance flag before processing request
- Allow: GET requests (read-only)
- Allow: `/api/v1/admin/backup` and `/api/v1/admin/restore` (admin-only)
- Block: All other POST/PUT/PATCH/DELETE requests
- Return: `503 Service Unavailable` with message

**Activation:**
- Enable at start of backup operation
- Enable at start of restore operation
- Disable after operation completes (success or failure)

### Safety Backup Strategy

**Location:** `/tmp/backup_safety_YYYYMMDD_HHMMSS/`

**Contents:**
- Database dump (same format as regular backup)
- Uploads directory copy

**Cleanup:**
- Delete immediately after successful restore
- Keep on failure for troubleshooting (manual cleanup required)
- Maximum age: 24 hours (auto-cleanup on next operation)

### Encryption Strategy

**Library:** Python `cryptography` (Fernet symmetric encryption)

**Process:**
1. User provides password during backup creation
2. Generate encryption key from password (using PBKDF2)
3. Encrypt entire backup archive
4. Store encrypted archive
5. User provides same password during restore
6. Decrypt and verify before restore

**Security:**
- Password never stored
- Encryption key derived from password
- Salt included in encrypted data

### File Size Handling

**Configuration:**
- Environment variable: `BACKUP_MAX_SIZE_MB` (default: 2048 = 2GB)
- Validated on upload
- Documented in README

**Streaming:**
- Use `tempfile.SpooledTemporaryFile` for uploads
- Stream tar.gz creation (don't load entire archive in memory)
- Process database restore in chunks where possible

### Concurrent Operations Lock

**Implementation:**
- File-based lock: `/tmp/backup_restore.lock`
- Lock file contains: PID, timestamp, operation type
- Check lock before starting operation
- Create lock at start, release on completion/error
- Timeout: Configurable (default: 10 minutes)
- Auto-release if lock is stale (PID not running, timestamp expired)

---

## File Structure

### New Files to Create

```
app/
├── core/
│   ├── maintenance.py          # Maintenance mode flag & utilities
│   └── backup_config.py        # Backup configuration (max size, timeout)
├── services/
│   └── backup.py               # Core backup/restore logic
├── api/
│   └── endpoints/
│       └── backup.py           # Backup/restore API endpoints
└── schemas/
    └── backup.py              # Pydantic models for backup operations
```

### Files to Modify

```
app/
├── main.py                     # Add maintenance mode middleware
├── core/
│   └── config.py              # Add backup configuration variables
└── api/
    └── api.py                  # Include backup router

requirements.txt                # Add cryptography dependency
```

---

## Implementation Steps

### Phase 1: Core Infrastructure

#### Step 1.1: Add Dependencies
- [ ] Add `cryptography` to `requirements.txt`
- [ ] Update Dockerfile if needed (should already have mysql-client)

#### Step 1.2: Backup Configuration Module
**File:** `app/core/backup_config.py`

**Purpose:** Centralized backup configuration

**Content:**
```python
"""Backup and restore configuration"""
import os
import logging

logger = logging.getLogger(__name__)

def get_optional_env_var(var_name: str, default: str, description: str) -> str:
    """Get an optional environment variable with a default"""
    return os.getenv(var_name, default)

# Backup file size limit (in MB)
BACKUP_MAX_SIZE_MB = int(get_optional_env_var(
    "BACKUP_MAX_SIZE_MB",
    "2048",
    "Maximum backup file size in MB (default: 2048 = 2GB)"
))

# Operation timeout (in seconds)
BACKUP_OPERATION_TIMEOUT_SECONDS = int(get_optional_env_var(
    "BACKUP_OPERATION_TIMEOUT_SECONDS",
    "600",  # 10 minutes
    "Maximum time for backup/restore operations in seconds (default: 600 = 10 minutes)"
))

# Lock file path
BACKUP_LOCK_FILE = "/tmp/backup_restore.lock"

# Maintenance flag file path
MAINTENANCE_FLAG_FILE = "/tmp/maintenance_mode.flag"

# Safety backup base directory
SAFETY_BACKUP_BASE_DIR = "/tmp/backup_safety"
```

#### Step 1.3: Maintenance Mode Module
**File:** `app/core/maintenance.py`

**Purpose:** Maintenance mode state management and middleware

**Key Functions:**
- `enable_maintenance_mode()`: Set maintenance flag
- `disable_maintenance_mode()`: Clear maintenance flag
- `is_maintenance_mode()`: Check if maintenance mode is active
- `maintenance_mode_middleware()`: FastAPI middleware function

**Implementation Details:**
- Use file-based flag for multi-worker compatibility
- Thread-safe operations
- Clear error messages

#### Step 1.4: Backup Schemas
**File:** `app/schemas/backup.py`

**Purpose:** Pydantic models for backup operations

**Models:**
- `BackupMetadata`: Metadata structure
- `BackupResponse`: Response for backup creation
- `RestoreResponse`: Response for restore operation
- `BackupStatus`: Status information

### Phase 2: Core Backup Service

#### Step 2.1: Backup Service - Database Dump
**File:** `app/services/backup.py`

**Function:** `_create_database_dump() -> bytes`

**Implementation:**
- Use subprocess to call `mysqldump`
- Use environment variables for connection (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
- Apply all mysqldump flags
- Capture output to bytes
- Handle errors gracefully

#### Step 2.2: Backup Service - Uploads Archive
**Function:** `_create_uploads_archive() -> bytes`

**Implementation:**
- Use Python `tarfile` module
- Stream creation (don't load all files in memory)
- Preserve directory structure
- Handle missing uploads directory gracefully

#### Step 2.3: Backup Service - Metadata Creation
**Function:** `_create_backup_metadata(database_name: str, backup_size: int, encrypted: bool) -> dict`

**Implementation:**
- Get API version from config
- Get current timestamp (ISO 8601)
- Create metadata dictionary
- Return as dict (will be serialized to JSON)

#### Step 2.4: Backup Service - Archive Creation
**Function:** `_create_backup_archive(database_dump: bytes, uploads_archive: bytes, metadata: dict) -> bytes`

**Implementation:**
- Create tar.gz archive in memory (streaming)
- Add database.sql
- Add uploads/ directory (extract from uploads archive first)
- Add metadata.json
- Return archive as bytes

#### Step 2.5: Backup Service - Encryption
**Function:** `_encrypt_backup(backup_data: bytes, password: str) -> bytes`

**Implementation:**
- Use `cryptography.fernet.Fernet`
- Derive key from password using PBKDF2
- Encrypt backup data
- Return encrypted bytes

**Function:** `_decrypt_backup(encrypted_data: bytes, password: str) -> bytes`

**Implementation:**
- Derive key from password
- Decrypt data
- Return decrypted bytes
- Handle decryption errors

#### Step 2.6: Backup Service - Main Backup Function
**Function:** `create_backup(encrypt: bool = False, password: Optional[str] = None) -> bytes`

**Implementation:**
- Create database dump
- Create uploads archive
- Create metadata
- Create backup archive
- Optionally encrypt
- Return backup archive bytes

### Phase 3: Core Restore Service

#### Step 3.1: Restore Service - Backup Validation
**Function:** `_validate_backup_file(backup_data: bytes) -> dict`

**Implementation:**
- Check if valid tar.gz
- Extract to temp location
- Verify structure (database.sql, uploads/, metadata.json)
- Validate metadata.json format
- Return metadata dict
- Clean up temp files on error

#### Step 3.2: Restore Service - Database SQL Processing
**Function:** `_process_database_sql(sql_content: bytes, current_db_name: str, original_db_name: str) -> bytes`

**Implementation:**
- Decode SQL to string
- Check if DB names match
- If match: Remove all `USE database_name;` statements
- If different: Replace `USE old_db;` with `USE current_db;`
- Add `SET FOREIGN_KEY_CHECKS=0;` at start
- Add `SET FOREIGN_KEY_CHECKS=1;` at end
- Return processed SQL as bytes

#### Step 3.3: Restore Service - Safety Backup Creation
**Function:** `_create_safety_backup() -> str`

**Implementation:**
- Create temp directory with timestamp
- Create database dump
- Copy uploads directory
- Return safety backup path
- Handle errors (if safety backup fails, abort restore)

#### Step 3.4: Restore Service - Database Restore
**Function:** `_restore_database(sql_content: bytes) -> None`

**Implementation:**
- Create separate database connection (not from pool)
- Start transaction
- Drop all tables (or truncate)
- Execute SQL statements
- Commit transaction
- Handle errors (rollback transaction, raise exception)

#### Step 3.5: Restore Service - Uploads Restore
**Function:** `_restore_uploads(uploads_path: str) -> None`

**Implementation:**
- Try to rename existing uploads directory
- If rename fails (file in use), raise detailed error
- Extract uploads from backup
- If rename succeeded, delete old directory
- Handle errors (restore old directory if needed)

#### Step 3.6: Restore Service - Safety Backup Rollback
**Function:** `_rollback_from_safety_backup(safety_backup_path: str) -> None`

**Implementation:**
- Extract safety backup
- Restore database from safety backup
- Restore uploads from safety backup
- Log detailed rollback information

#### Step 3.7: Restore Service - Main Restore Function
**Function:** `restore_backup(backup_data: bytes, encrypted: bool = False, password: Optional[str] = None) -> dict`

**Implementation:**
- Validate backup file
- Optionally decrypt
- Create safety backup
- Process database SQL
- Restore database
- Restore uploads
- Clean up safety backup (on success)
- Return success status
- On any error: rollback from safety backup, return error details

### Phase 4: Concurrent Operations Lock

#### Step 4.1: Lock Management Functions
**File:** `app/services/backup.py` (or separate utility)

**Functions:**
- `acquire_operation_lock(operation_type: str, timeout: int) -> bool`
- `release_operation_lock() -> None`
- `check_operation_lock() -> Optional[dict]`
- `is_lock_stale(lock_info: dict) -> bool`

**Implementation:**
- File-based locking
- Lock file format: JSON with PID, timestamp, operation type
- Check if PID is still running
- Check if timestamp expired
- Auto-release stale locks

### Phase 5: API Endpoints

#### Step 5.1: Backup Endpoint
**File:** `app/api/endpoints/backup.py`

**Endpoint:** `POST /api/v1/admin/backup`

**Query Parameters:**
- `encrypt` (bool, optional): Enable encryption (default: false)
- `password` (str, optional): Encryption password (required if encrypt=true)

**Implementation:**
- Check authentication (admin only)
- Check operation lock
- Acquire operation lock
- Enable maintenance mode
- Create backup
- Release operation lock
- Disable maintenance mode
- Return backup as downloadable file
- Handle errors (release lock, disable maintenance mode)

**Response:**
- Content-Type: `application/gzip` or `application/octet-stream`
- Content-Disposition: `attachment; filename="backup_YYYYMMDD_HHMMSS.tar.gz"`
- Body: Backup archive bytes

#### Step 5.2: Restore Endpoint
**File:** `app/api/endpoints/backup.py`

**Endpoint:** `POST /api/v1/admin/restore`

**Request Body:**
- `file` (UploadFile): Backup archive file
- `password` (str, optional): Decryption password (required if encrypted)

**Implementation:**
- Check authentication (admin only)
- Check operation lock
- Validate file size
- Acquire operation lock
- Enable maintenance mode
- Read uploaded file
- Restore backup
- Release operation lock
- Disable maintenance mode
- Return success/error response
- Handle errors (rollback, release lock, disable maintenance mode)

**Response:**
```json
{
  "status": "success" | "error",
  "message": "Restore completed successfully" | "Restore failed: ...",
  "details": {
    "tables_restored": 25,
    "files_restored": 120,
    "backup_timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Phase 6: Middleware Integration

#### Step 6.1: Add Maintenance Mode Middleware
**File:** `app/main.py`

**Implementation:**
- Import maintenance mode functions
- Add middleware before other middleware
- Check maintenance flag
- Allow GET requests
- Allow backup/restore endpoints (check path)
- Block other write operations
- Return 503 with message

### Phase 7: Error Handling and Logging

#### Step 7.1: Error Handling Strategy
- Generic messages to users
- Detailed errors in logs
- Never log sensitive data (passwords, connection strings)
- Include operation context in logs
- Include error codes and stack traces in logs

#### Step 7.2: Logging Points
- Operation start/end
- Each major step (dump, archive, encrypt, etc.)
- Errors with full context
- Rollback operations
- Lock acquisition/release

### Phase 8: Testing

#### Step 8.1: Unit Tests
- Backup service functions
- Restore service functions
- Maintenance mode functions
- Lock management functions
- SQL processing functions

#### Step 8.2: Integration Tests
- Full backup creation
- Full restore operation
- Encrypted backup/restore
- Error scenarios (failed restore, rollback)
- Concurrent operation prevention
- Maintenance mode behavior

#### Step 8.3: Manual Testing Checklist
- [ ] Create backup (unencrypted)
- [ ] Create backup (encrypted)
- [ ] Restore backup (same server)
- [ ] Restore backup (different server, different DB name)
- [ ] Restore backup (different server, different DB user)
- [ ] Test maintenance mode activation
- [ ] Test concurrent operation prevention
- [ ] Test error handling and rollback
- [ ] Test file size limits
- [ ] Test timeout handling

---

## Detailed Component Specifications

### Maintenance Mode Module

**File:** `app/core/maintenance.py`

```python
"""Maintenance mode management for backup/restore operations"""
import os
import fcntl
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MAINTENANCE_FLAG_FILE = "/tmp/maintenance_mode.flag"

def enable_maintenance_mode() -> None:
    """Enable maintenance mode by creating flag file"""
    try:
        Path(MAINTENANCE_FLAG_FILE).touch()
        logger.info("Maintenance mode enabled")
    except Exception as e:
        logger.error(f"Failed to enable maintenance mode: {e}")
        raise

def disable_maintenance_mode() -> None:
    """Disable maintenance mode by removing flag file"""
    try:
        flag_file = Path(MAINTENANCE_FLAG_FILE)
        if flag_file.exists():
            flag_file.unlink()
        logger.info("Maintenance mode disabled")
    except Exception as e:
        logger.error(f"Failed to disable maintenance mode: {e}")
        raise

def is_maintenance_mode() -> bool:
    """Check if maintenance mode is active"""
    return Path(MAINTENANCE_FLAG_FILE).exists()

# Middleware function to be added to FastAPI app
async def maintenance_mode_middleware(request, call_next):
    """Middleware to handle maintenance mode"""
    if is_maintenance_mode():
        # Allow GET requests
        if request.method == "GET":
            return await call_next(request)
        
        # Allow backup/restore endpoints (admin-only, so auth will be checked)
        if request.url.path in ["/api/v1/admin/backup", "/api/v1/admin/restore"]:
            return await call_next(request)
        
        # Block all other requests
        from fastapi import Response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Service temporarily unavailable. Maintenance in progress."
            }
        )
    
    return await call_next(request)
```

### Backup Service - Database Dump

**Function:** `_create_database_dump() -> bytes`

**Implementation Details:**
- Use `subprocess.run()` to execute mysqldump
- Capture stdout to bytes
- Handle stderr (log errors)
- Use environment variables for connection
- Apply all mysqldump flags
- Return dump as bytes

**Error Handling:**
- Check mysqldump exit code
- Log detailed error messages
- Raise exception with context

### Backup Service - Uploads Archive

**Function:** `_create_uploads_archive() -> bytes`

**Implementation Details:**
- Get upload directory from environment
- Use `tarfile.open()` with mode 'w:gz' and fileobj=BytesIO
- Walk directory tree
- Add files to archive (preserve paths)
- Handle missing directory gracefully
- Return archive as bytes

**Error Handling:**
- Check if upload directory exists
- Handle permission errors
- Log file access errors
- Raise exception with context

### Restore Service - Database SQL Processing

**Function:** `_process_database_sql(sql_content: bytes, current_db_name: str, original_db_name: str) -> bytes`

**Implementation Details:**
- Decode SQL to string (UTF-8)
- Use regex to find `USE database_name;` statements
- Compare database names
- If match: Remove all USE statements
- If different: Replace USE statements
- Add FOREIGN_KEY_CHECKS statements
- Return processed SQL as bytes

**Regex Pattern:**
```python
import re
# Pattern to match USE statements (case-insensitive, optional whitespace)
use_pattern = re.compile(r'^\s*USE\s+[`"]?(\w+)[`"]?\s*;?\s*$', re.IGNORECASE | re.MULTILINE)
```

### Restore Service - Database Restore

**Function:** `_restore_database(sql_content: bytes) -> None`

**Implementation Details:**
- Create new database connection (not from pool)
- Use connection string from environment
- Start transaction
- Get list of all tables
- Drop all tables (or use DROP DATABASE + CREATE DATABASE)
- Execute SQL statements (split by semicolon, handle multi-line)
- Commit transaction
- Close connection

**SQL Execution:**
- Split SQL by semicolon (handle strings carefully)
- Execute each statement
- Handle errors (rollback, raise exception)

**Error Handling:**
- Wrap in try/except
- Rollback transaction on error
- Log detailed SQL errors
- Raise exception with context

### Restore Service - Uploads Restore

**Function:** `_restore_uploads(uploads_path: str) -> None`

**Implementation Details:**
- Get upload directory from environment
- Try to rename existing directory to backup location
- If rename fails, check if files are in use
- Extract uploads from backup archive
- If rename succeeded, delete old directory
- Set appropriate file permissions

**File In Use Detection:**
- Try rename operation
- If fails with OSError, check errno
- Log detailed error (which file if possible)
- Raise exception with context

### Lock Management

**Function:** `acquire_operation_lock(operation_type: str, timeout: int) -> bool`

**Implementation Details:**
- Check if lock file exists
- If exists, read lock info
- Check if lock is stale (PID not running, timestamp expired)
- If stale, remove lock file
- Create new lock file with current PID, timestamp, operation type
- Use file locking (fcntl) to prevent race conditions
- Return True if acquired, False if already locked

**Lock File Format (JSON):**
```json
{
  "pid": 12345,
  "timestamp": "2026-01-15T10:30:00Z",
  "operation_type": "backup",
  "timeout_seconds": 600
}
```

**Stale Lock Detection:**
- Check if PID is running (use `os.kill(pid, 0)`)
- Check if timestamp + timeout < current time
- If stale, remove lock file

---

## Configuration

### Environment Variables

Add to `.env.example` and document in README:

```bash
# Backup and Restore Configuration
BACKUP_MAX_SIZE_MB=2048                    # Maximum backup file size in MB (default: 2048 = 2GB)
BACKUP_OPERATION_TIMEOUT_SECONDS=600       # Maximum time for backup/restore operations in seconds (default: 600 = 10 minutes)
```

### Configuration Module

**File:** `app/core/backup_config.py`

See Step 1.2 for full implementation.

---

## Error Handling

### Error Categories

1. **Validation Errors**
   - Invalid backup format
   - Missing required files
   - Invalid metadata
   - File size exceeds limit

2. **Operation Errors**
   - Database connection failure
   - File system errors
   - Permission errors
   - Timeout errors

3. **Restore Errors**
   - SQL execution errors
   - File restore errors
   - Rollback errors

### Error Response Format

**User-Facing (API Response):**
```json
{
  "status": "error",
  "message": "Restore failed. Please contact administrator.",
  "error_code": "RESTORE_FAILED"
}
```

**Log Entry:**
```
ERROR: Restore operation failed
Operation: restore_backup
Error: Database connection failed
Details: Connection refused (errno: 111)
SQL Error: [Error code if applicable]
Stack trace: [Full stack trace]
Context: {
  "backup_timestamp": "2026-01-15T10:30:00Z",
  "database_name": "shopdb1",
  "operation_step": "database_restore"
}
```

### Error Handling Best Practices

1. **Never log sensitive data:**
   - Passwords
   - Connection strings with passwords
   - Encryption keys

2. **Always include context:**
   - Operation type
   - Operation step
   - Timestamp
   - Relevant IDs or names

3. **Provide actionable information:**
   - What failed
   - Why it failed (if known)
   - What was attempted
   - What to do next

---

## Security Considerations

### Authentication and Authorization

- All backup/restore endpoints require admin authentication
- Use existing `get_current_admin` dependency
- Verify JWT token validity

### Data Protection

- Optional encryption for backups
- Password never stored
- Encryption key derived from password
- No sensitive data in logs

### Input Validation

- Validate backup file format
- Validate file size
- Validate metadata structure
- Sanitize file paths (prevent path traversal)

### File System Security

- Use secure temp directories
- Set appropriate file permissions
- Clean up temp files
- Prevent symlink attacks

### Network Security

- Use HTTPS in production
- Validate file uploads
- Limit file size
- Timeout long operations

---

## Testing Strategy

### Unit Tests

**File:** `tests/unit/test_backup_service.py`

**Test Cases:**
- Database dump creation
- Uploads archive creation
- Metadata creation
- Encryption/decryption
- SQL processing (USE statement handling)
- Lock management
- Maintenance mode functions

### Integration Tests

**File:** `tests/integration/test_backup_restore_api.py`

**Test Cases:**
- Full backup creation (unencrypted)
- Full backup creation (encrypted)
- Full restore operation
- Restore with different DB name
- Restore with different DB user
- Error scenarios
- Rollback on failure
- Concurrent operation prevention
- Maintenance mode activation

### Manual Testing Checklist

1. **Backup Creation**
   - [ ] Create unencrypted backup
   - [ ] Create encrypted backup
   - [ ] Verify backup file structure
   - [ ] Verify metadata content
   - [ ] Test with large files (>500MB)

2. **Backup Restoration**
   - [ ] Restore to same server
   - [ ] Restore to different server (same DB name)
   - [ ] Restore to different server (different DB name)
   - [ ] Restore to different server (different DB user)
   - [ ] Test encrypted backup restore
   - [ ] Verify all data restored correctly

3. **Error Scenarios**
   - [ ] Invalid backup file format
   - [ ] Corrupted backup file
   - [ ] Wrong encryption password
   - [ ] Database connection failure during restore
   - [ ] File system errors during restore
   - [ ] Verify rollback on failure

4. **Concurrent Operations**
   - [ ] Try backup while restore in progress
   - [ ] Try restore while backup in progress
   - [ ] Verify lock mechanism works
   - [ ] Test timeout handling

5. **Maintenance Mode**
   - [ ] Verify maintenance mode enabled during backup
   - [ ] Verify maintenance mode enabled during restore
   - [ ] Test that GET requests still work
   - [ ] Test that write requests are blocked
   - [ ] Test that backup/restore endpoints still work

6. **File Size Limits**
   - [ ] Test with backup at limit
   - [ ] Test with backup exceeding limit
   - [ ] Verify error message

7. **Timeout Handling**
   - [ ] Test with operation exceeding timeout
   - [ ] Verify lock is released
   - [ ] Verify maintenance mode is disabled

---

## Deployment Considerations

### Docker Configuration

- `/tmp` directory is available in containers (no volume mapping needed)
- `mysqldump` is available (already in Dockerfile)
- Ensure sufficient disk space for safety backups

### Resource Requirements

- Disk space: Backup size × 2 (for safety backup)
- Memory: Sufficient for streaming operations (500MB+ should be fine)
- CPU: Minimal impact (mostly I/O bound)

### Monitoring

- Log all backup/restore operations
- Monitor disk space usage
- Alert on failed operations
- Track operation durations

### Backup Recommendations

- Regular automated backups (via cron calling API)
- Store backups off-site
- Test restore procedures regularly
- Document restore process

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Add cryptography dependency
- [ ] Create backup_config.py
- [ ] Create maintenance.py
- [ ] Create backup schemas
- [ ] Update config.py with backup settings

### Phase 2: Core Backup Service
- [ ] Implement database dump function
- [ ] Implement uploads archive function
- [ ] Implement metadata creation
- [ ] Implement archive creation
- [ ] Implement encryption functions
- [ ] Implement main backup function

### Phase 3: Core Restore Service
- [ ] Implement backup validation
- [ ] Implement SQL processing
- [ ] Implement safety backup creation
- [ ] Implement database restore
- [ ] Implement uploads restore
- [ ] Implement rollback function
- [ ] Implement main restore function

### Phase 4: Concurrent Operations
- [ ] Implement lock management functions
- [ ] Integrate locks into backup/restore

### Phase 5: API Endpoints
- [ ] Create backup endpoint
- [ ] Create restore endpoint
- [ ] Add to API router
- [ ] Add authentication

### Phase 6: Middleware
- [ ] Add maintenance mode middleware
- [ ] Integrate into main.py

### Phase 7: Error Handling
- [ ] Implement error handling strategy
- [ ] Add comprehensive logging
- [ ] Test error scenarios

### Phase 8: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Manual testing
- [ ] Document test results

### Phase 9: Documentation
- [ ] Update README with backup/restore instructions
- [ ] Document environment variables
- [ ] Document API endpoints
- [ ] Document troubleshooting

---

## Notes and Considerations

### Database Name Handling - Testing Required

The USE statement handling needs thorough testing:
1. Test with matching database names
2. Test with different database names
3. Verify SQL executes correctly in both cases
4. Test with various SQL statement formats

### Maintenance Mode - Multi-Worker Consideration

With uvicorn workers, maintenance mode flag must be file-based (not just in-memory) to work across workers. The file-based approach handles this.

### Safety Backup Cleanup

Safety backups are kept on failure for troubleshooting. Consider:
- Auto-cleanup after 24 hours
- Manual cleanup instructions
- Disk space monitoring

### Future Enhancements

Potential future improvements:
- Incremental backups
- Backup scheduling via API
- Backup listing endpoint
- Backup verification endpoint
- Cloud storage integration
- Backup compression optimization

---

## Conclusion

This implementation plan provides a comprehensive guide for implementing backup and restore functionality. Follow the phases sequentially, testing at each step. Pay special attention to error handling, security, and the all-or-nothing restore strategy.

For questions or clarifications, refer to this document or the code comments in the implementation.
