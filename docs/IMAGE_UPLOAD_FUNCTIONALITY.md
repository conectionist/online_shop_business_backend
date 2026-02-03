# Image Upload Functionality

This document describes the image upload functionality implemented for the Online Shop Business Backend API.

## Overview

The image upload functionality allows storing and managing images for entities in the system. It is implemented for Categories and Products, and now supports an **upload-first staging flow** where images are uploaded and validated before the corresponding entity is created.

## Technical Implementation

### Storage Configuration

Images are stored in the filesystem with the following setup:

- **Storage Location**: `/app/uploads` directory inside the Docker container
- **Persistence**: Docker volumes are configured to persist uploaded files:
  - Production: `uploads_data:/app/uploads` in `docker-compose.yml`
  - Testing: `test_uploads_data:/app/uploads` in `docker-compose.test.yml`
- **Environment Variable**: `UPLOAD_FOLDER=/app/uploads` defines the base upload directory

### File Upload Utilities

Core utilities for file handling are implemented in `app/core/file_upload.py`:

1. **File Validation** (product and category image uploads enforce):
   - **Allowed extensions**: .jpg, .jpeg, .png, .gif, .webp
   - **Max file size**: configurable via `MAX_IMAGE_SIZE_MB` (default 15 MB)
   - **Content-Type**: optional check when present (allowed: image/jpeg, image/png, image/gif, image/webp)
   - **Server-side content validation**: image bytes are validated with PIL before save; non-image payloads are rejected with 400. Uploads are read with a size cap to avoid memory DoS.

2. **Secure Filename Generation**:
   - Uses UUID to generate unique filenames
   - Preserves original file extension
   - Prevents path traversal attacks

3. **File Operations**:
   - `save_upload_file()`: Saves uploaded file with validation
   - `delete_file()`: Safely removes files from storage
   - Directory management (auto-creates subdirectories)

### Entity-Specific Implementation

#### Categories

Categories can have a single image associated with them:

- **Database Field**: `image_path` in the `category` table stores the relative path
- **API Endpoints**:
  - `POST /api/v1/categories/{category_id}/image` – upload/replace image for an existing category
  - `POST /api/v1/categories/` – can accept a `primary_image_upload_id` from the staging upload endpoint to set the initial image during creation
- **Storage Location**: Files are stored in the `categories` subdirectory
- **Image Replacement**: When uploading a new image (either via `/image` or via update), any existing image directory is automatically deleted
- **Deletion Behavior**:
  - Soft Delete: Image files are preserved to allow restoration
  - Hard Delete: Image files are permanently deleted along with the category

#### Products

Products can have multiple images associated with them via a `product_images` table:

- **Database Model**: `ProductImage` stores `path`, `position`, and `is_primary`
- **API Endpoints**:
  - `POST /api/v1/products/`:
    - Optional `primary_image` (legacy) – direct file upload on create (now deprecated)
    - Optional `primary_image_upload_id` – preferred upload-first flow using staged image
  - `POST /api/v1/products/{product_id}/images` – upload additional images or manage galleries
- **Storage Location**: Files are stored in the `products` subdirectory, with one directory per image set (original, medium, thumbnail).

### Staging Uploads

To support upload-first workflows and eliminate orphan entities when uploads fail, a staging mechanism is provided:

- **Endpoint**: `POST /api/v1/uploads/images`
- **Purpose**: Upload and validate an image **before** creating or updating an entity.
- **Behavior**:
  - Validates extension, size, content-type (optional), and image content.
  - Saves the raw file into a staging directory under `uploads/staging/{upload_id}/`.
  - Returns an opaque `upload_id` that can be used by entity creation endpoints as `primary_image_upload_id`.
- **Consumers**:
  - `POST /api/v1/products/` – accepts `primary_image_upload_id` and processes the staged image into final product image versions.
  - `POST /api/v1/categories/` – accepts `primary_image_upload_id` and processes the staged image into the category image directory.

## API Usage

### Upload Category Image

**Endpoint**: `POST /api/v1/categories/{category_id}/image`

**Request**:
- Content-Type: `multipart/form-data`
- Required Field: `file` (image file)

**Constraints**:
- Supported formats: JPEG, PNG, GIF, WEBP
- Maximum file size: configurable via `MAX_IMAGE_SIZE_MB` (default 15 MB)

**Response**:
```json
{
  "id": 1,
  "name": "Electronics",
  "description": "Electronic devices and accessories",
  "image_path": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg",
  "is_deleted": false
}
```

**Error Responses**:
- 400: Bad request (invalid file format or size) — see **Image validation error response** below for body shape
- 404: Category not found
- 422: Validation error
- 500: Internal server error

### Image validation error response

Image validation 400 responses use the **same structure as 422 validation errors**, so the frontend can use one handler (e.g. loop over `detail`, show each `msg` or map `type` to a message).

**Response body** (HTTP 400):

```json
{
  "detail": [
    {
      "loc": ["body", "file"],
      "msg": "File extension not allowed. Allowed extensions: jpg, jpeg, png, gif, webp",
      "type": "image_extension_not_allowed"
    }
  ]
}
```

- `detail` is a **list** of objects (one item per validation failure).
- Each item has: `loc` (field location, e.g. `["body", "primary_image"]` or `["body", "file"]`), `msg` (human-readable message), `type` (machine-readable code).

**Type values** (frontend can switch on `detail[0].type` to show the right message):

| type | When |
|------|------|
| `image_extension_not_allowed` | File extension is not allowed (e.g. .exe, .txt). |
| `image_content_type_not_allowed` | Content-Type header is set and not in the allowed set. |
| `image_too_large` | File size exceeds the configured limit. |
| `image_invalid_content` | File bytes are not a valid image or format not allowed. |
| `image_processing_error` | Generic processing failure (e.g. I/O or decode error). |

All image upload endpoints (category image, product images, staging upload, product/category create with image) use this shape for validation failures.

## Testing

Integration tests for image upload functionality are available in:
- `tests/integration/test_category_image_upload.py`

These tests cover:
- Uploading an image to a category
- Replacing an existing image
- Handling invalid file types
- Validation for non-existent categories

## Future Enhancements

Potential improvements for future versions:

1. **Image Processing**:
   - Automatic resizing/compression
   - Thumbnail generation
   - Image optimization

2. **Storage Options**:
   - Cloud storage integration (S3, Azure Blob Storage)
   - CDN integration

3. **Additional Features**:
   - Multiple images per entity
   - Image metadata storage
   - Image categorization and tagging

4. **Monitoring**:
   - Storage usage tracking
   - Orphaned file cleanup
