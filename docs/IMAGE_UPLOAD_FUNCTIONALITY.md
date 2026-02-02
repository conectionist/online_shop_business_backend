# Image Upload Functionality

This document describes the image upload functionality implemented for the Online Shop Business Backend API.

## Overview

The image upload functionality allows storing and managing images for entities in the system. Currently, it is implemented for the Categories entity, with plans to extend to other entities like Products in the future.

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
- **API Endpoint**: `POST /api/v1/categories/{category_id}/image`
- **Storage Location**: Files are stored in the `categories` subdirectory
- **Image Replacement**: When uploading a new image, any existing image is automatically deleted
- **Deletion Behavior**:
  - Soft Delete: Image file is preserved to allow restoration
  - Hard Delete: Image file is permanently deleted along with the category

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
- 400: Bad request (invalid file format or size)
- 404: Category not found
- 422: Validation error
- 500: Internal server error

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
