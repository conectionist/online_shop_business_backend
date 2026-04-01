from __future__ import annotations

import os

from app.core.file_upload import get_upload_dir

_KNOWN_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def resolve_image_versions(image_path: str | None, placeholder_url: str) -> dict[str, str]:
    """Resolve image version paths with dynamic extension detection.

    Returns placeholder URLs when ``image_path`` is empty.
    """
    if not image_path:
        return {
            "original": placeholder_url,
            "medium": placeholder_url,
            "thumbnail": placeholder_url,
        }

    image_id = os.path.basename(image_path)
    full_path = os.path.join(get_upload_dir(), image_path)

    if os.path.exists(full_path):
        for ext in _KNOWN_EXTENSIONS:
            original_file = os.path.join(full_path, f"{image_id}{ext}")
            if os.path.exists(original_file):
                return {
                    "original": f"{image_path}/{image_id}{ext}",
                    "medium": f"{image_path}/{image_id}-medium{ext}",
                    "thumbnail": f"{image_path}/{image_id}-thumbnail{ext}",
                }

    # Fallback keeps the current API behavior when files are missing.
    return {
        "original": f"{image_path}/{image_id}.jpg",
        "medium": f"{image_path}/{image_id}-medium.jpg",
        "thumbnail": f"{image_path}/{image_id}-thumbnail.jpg",
    }
