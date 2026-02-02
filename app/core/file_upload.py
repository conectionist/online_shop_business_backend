import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Set, Tuple

from fastapi import HTTPException, UploadFile, status

from app.core.config import MAX_IMAGE_SIZE_MB


# Configuration
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def get_upload_dir() -> Path:
    """Get the upload directory from environment variable or use default"""
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./uploads")
    upload_dir = Path(upload_folder)
    
    # Ensure the upload directory exists
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    return upload_dir


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def is_valid_image(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """
    Validate if the uploaded file is a valid image
    Returns a tuple of (is_valid, error_message)
    """
    # Check file extension
    extension = get_file_extension(file.filename or "")
    if not extension or extension not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"File extension not allowed. Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
    
    # Optional MIME check: if Content-Type is set, it must be in the allowed set
    content_type = (file.content_type or "").strip().lower()
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        return False, f"Content-Type not allowed. Allowed: {', '.join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))}"
    
    # Check file size (FastAPI's UploadFile has file.file.seek and file.file.tell)
    try:
        file.file.seek(0, 2)  # Seek to the end of the file
        file_size = file.file.tell()  # Get the file size
        file.file.seek(0)  # Reset file pointer to the beginning
        
        if file_size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            return False, f"File size exceeds the {MAX_IMAGE_SIZE_MB}MB limit"
    except Exception as e:
        return False, f"Error validating file: {str(e)}"
    
    return True, None


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure filename with UUID to prevent path traversal attacks
    and filename collisions
    """
    extension = get_file_extension(original_filename)
    unique_filename = f"{uuid.uuid4().hex}"
    
    if extension:
        unique_filename = f"{unique_filename}.{extension}"
    
    return unique_filename


def save_upload_file(upload_file: UploadFile, subdirectory: str = "") -> str:
    """
    Save an uploaded file to the upload directory
    Returns the relative path to the saved file
    """
    # Validate the file
    is_valid, error_message = is_valid_image(upload_file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Generate a secure filename
    secure_filename = generate_secure_filename(upload_file.filename or "untitled")
    
    # Create subdirectory if provided
    upload_dir = get_upload_dir()
    if subdirectory:
        upload_path = upload_dir / subdirectory
        upload_path.mkdir(parents=True, exist_ok=True)
    else:
        upload_path = upload_dir
    
    # Save the file
    file_path = upload_path / secure_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Return the relative path that can be stored in the database
    if subdirectory:
        return f"{subdirectory}/{secure_filename}"
    return secure_filename


def delete_file(file_path: str) -> bool:
    """
    Delete a file from the upload directory
    Returns True if successful, False otherwise
    """
    if not file_path:
        return False
    
    upload_dir = get_upload_dir()
    full_path = upload_dir / file_path
    
    try:
        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            
            # Remove empty parent directories
            parent_dir = full_path.parent
            if parent_dir != upload_dir and parent_dir.exists() and not any(parent_dir.iterdir()):
                parent_dir.rmdir()
                
            return True
    except Exception:
        # Log the error if logging is configured
        pass
    
    return False
