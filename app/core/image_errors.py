"""
Image validation error types and 422-like detail builder.

Image validation 400 responses use the same structure as 422 validation errors:
detail is a list of {"loc": [...], "msg": "...", "type": "..."} so the frontend
can use one handler and key off "type" to show the right message.
"""

from typing import List


# Type values (snake_case, Pydantic-style) — frontend can switch on these
TYPE_IMAGE_EXTENSION_NOT_ALLOWED = "image_extension_not_allowed"
TYPE_IMAGE_CONTENT_TYPE_NOT_ALLOWED = "image_content_type_not_allowed"
TYPE_IMAGE_TOO_LARGE = "image_too_large"
TYPE_IMAGE_INVALID_CONTENT = "image_invalid_content"
TYPE_IMAGE_PROCESSING_ERROR = "image_processing_error"


def image_validation_detail(
    error_type: str,
    message: str,
    loc: List[str],
) -> List[dict]:
    """
    Build 422-like detail list for image validation 400 responses.

    Returns:
        [{"loc": loc, "msg": message, "type": error_type}]
    """
    return [{"loc": loc, "msg": message, "type": error_type}]
