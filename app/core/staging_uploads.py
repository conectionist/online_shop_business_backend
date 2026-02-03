import json
import os
import uuid
from pathlib import Path
from typing import Dict, Tuple

from fastapi import HTTPException, UploadFile, status

from app.core.file_upload import get_upload_dir, is_valid_image
from app.core.image_errors import image_validation_detail


STAGING_SUBDIR = "staging"


def _get_staging_root() -> Path:
    """
    Return the absolute path to the staging uploads root directory,
    creating it if necessary.
    """
    root = get_upload_dir() / STAGING_SUBDIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_staged_image(upload_file: UploadFile) -> str:
    """
    Validate and persist an image to a temporary staging directory.

    Returns:
        upload_id: Opaque identifier that can later be used to resolve the
        staged image when creating an entity.
    """
    # Reuse existing validation logic (extension, content-type, size)
    is_valid, error_detail = is_valid_image(upload_file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=image_validation_detail(
                error_detail["type"], error_detail["msg"], ["body", "file"]
            ),
        )

    upload_id = uuid.uuid4().hex
    root = _get_staging_root()
    upload_dir = root / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_filename = upload_file.filename or "uploaded"
    stored_filename = original_filename

    # To avoid collisions or path issues, normalize the stored filename to just the basename
    stored_filename = os.path.basename(stored_filename)

    file_path = upload_dir / stored_filename

    try:
        # Persist the raw file bytes; is_valid_image has already rewound the file pointer.
        with open(file_path, "wb") as buffer:
            while True:
                chunk = upload_file.file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
    except Exception as exc:  # pragma: no cover - safety net
        # Best-effort cleanup
        try:
            if upload_dir.exists():
                for child in upload_dir.iterdir():
                    child.unlink(missing_ok=True)  # type: ignore[arg-type]
                upload_dir.rmdir()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving staged image: {exc}",
        )

    # Store minimal metadata to help when converting back to an UploadFile later
    meta = {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "content_type": (upload_file.content_type or "").strip() or None,
    }
    meta_path = upload_dir / "meta.json"
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)
    except Exception:
        # If metadata write fails, we can still use the staged file using defaults.
        pass

    return upload_id


def resolve_staged_image(upload_id: str) -> Tuple[Path, Dict]:
    """
    Given an upload_id, return the directory path and metadata for the staged image.

    Raises HTTP 400 if the upload_id is invalid or the staged image no longer exists.
    """
    if not upload_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing upload_id for staged image",
        )

    root = _get_staging_root()
    # Prevent path traversal by only allowing hex UUID-like directory names
    if not all(c in "0123456789abcdef" for c in upload_id.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload_id",
        )

    upload_dir = root / upload_id
    if not upload_dir.exists() or not upload_dir.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staged image not found or has expired",
        )

    meta_path = upload_dir / "meta.json"
    meta: Dict = {}
    if meta_path.exists() and meta_path.is_file():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = {}

    return upload_dir, meta


def delete_staged_image(upload_id: str) -> None:
    """
    Best-effort delete of a staged image directory.
    """
    if not upload_id:
        return

    root = _get_staging_root()
    upload_dir = root / upload_id
    try:
        if upload_dir.exists() and upload_dir.is_dir():
            for child in upload_dir.iterdir():
                try:
                    if child.is_file():
                        child.unlink()
                    elif child.is_dir():
                        # Should not happen, but handle defensively
                        for nested in child.iterdir():
                            if nested.is_file():
                                nested.unlink()
                        child.rmdir()
                except Exception:
                    # Ignore individual file errors; this is best-effort cleanup
                    pass
            upload_dir.rmdir()
    except Exception:
        # Swallow errors; this is non-critical cleanup
        pass

