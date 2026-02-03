from fastapi import APIRouter, Depends, File, UploadFile, status

from app.core.staging_uploads import save_staged_image
from app.models.admin import Admin
from app.services.auth import get_current_admin


router = APIRouter()


@router.post(
    "/images",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Image uploaded and staged successfully"},
        400: {"description": "Invalid image (extension, size, or content)"},
        401: {"description": "Unauthorized - Authentication required"},
    },
)
async def upload_image_for_staging(
    file: UploadFile = File(
        ...,
        description=(
            "Image file to upload (JPEG, PNG, GIF, WEBP; "
            "max size configurable via MAX_IMAGE_SIZE_MB, default 15 MB)"
        ),
    ),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    Upload an image to temporary staging storage.

    This endpoint performs full validation (extension, size, content) and,
    on success, returns an opaque `upload_id` that can later be supplied to
    entity creation endpoints (e.g. products, categories) as
    `primary_image_upload_id`.
    """
    # current_admin is injected to enforce admin-only access
    _ = current_admin

    upload_id = save_staged_image(file)
    return {"upload_id": upload_id}

