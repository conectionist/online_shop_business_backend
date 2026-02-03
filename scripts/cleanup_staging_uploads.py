#!/usr/bin/env python
"""
Utility script to clean up old staged image uploads.

This can be run periodically (e.g., via cron or a Kubernetes CronJob) to remove
directories under the staging uploads root that are older than a configured TTL.
"""

import os
import sys
import time
from pathlib import Path

from app.core.file_upload import get_upload_dir


def cleanup_staging_uploads(ttl_hours: int = 24) -> int:
    """
    Delete staging subdirectories older than the given TTL.

    Args:
        ttl_hours: Time-to-live in hours for staged uploads. Directories older
            than this will be removed.

    Returns:
        Number of directories deleted.
    """
    from app.core.staging_uploads import STAGING_SUBDIR

    now = time.time()
    ttl_seconds = ttl_hours * 60 * 60

    root = Path(get_upload_dir()) / STAGING_SUBDIR
    if not root.exists() or not root.is_dir():
        return 0

    deleted_count = 0
    for child in root.iterdir():
        if not child.is_dir():
            continue

        try:
            # Use directory mtime as an approximation for age
            mtime = child.stat().st_mtime
            age_seconds = now - mtime
            if age_seconds > ttl_seconds:
                # Best-effort recursive delete
                for nested in child.rglob("*"):
                    if nested.is_file():
                        try:
                            nested.unlink()
                        except Exception:
                            pass
                try:
                    child.rmdir()
                except OSError:
                    # If non-empty, try a second pass
                    for nested in child.rglob("*"):
                        if nested.is_file():
                            try:
                                nested.unlink()
                            except Exception:
                                pass
                    try:
                        child.rmdir()
                    except Exception:
                        pass
                deleted_count += 1
        except Exception:
            # Ignore errors for individual directories
            continue

    return deleted_count


if __name__ == "__main__":
    ttl_env = os.getenv("STAGING_UPLOAD_TTL_HOURS")
    ttl = int(ttl_env) if ttl_env and ttl_env.isdigit() else 24
    removed = cleanup_staging_uploads(ttl_hours=ttl)
    print(f"Removed {removed} old staged upload directories.")

