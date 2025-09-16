"""Image processing utilities for the application"""

import io
import os
import uuid
from typing import Tuple, Optional, Dict, List

from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException, status

from app.core.file_upload import get_upload_dir


def resize_image(
    image_content: bytes,
    max_size: Tuple[int, int] = (1200, 1200),
    format: Optional[str] = None
) -> bytes:
    """
    Resize an image while maintaining aspect ratio.
    
    Args:
        image_content: Raw image bytes
        max_size: Maximum width and height
        format: Output format (if None, keeps original format)
    
    Returns:
        Bytes of resized image
    """
    try:
        # Open the image from bytes
        img = Image.open(io.BytesIO(image_content))
        
        # Store original format before EXIF transpose (which may clear it)
        original_format = img.format

        # Normalize orientation using EXIF data so pixels are physically upright
        img = ImageOps.exif_transpose(img)
        
        # Keep original format if not specified
        img_format = format or original_format
        
        # Only resize if image is larger than max_size
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format=img_format)
        return output.getvalue()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing image: {str(e)}"
        )


def create_thumbnail(
    image_content: bytes,
    size: Tuple[int, int] = (200, 200),
    format: Optional[str] = None
) -> bytes:
    """
    Create a thumbnail of the image.
    
    Args:
        image_content: Raw image bytes
        size: Thumbnail size (width, height)
        format: Output format (if None, keeps original format)
    
    Returns:
        Bytes of thumbnail image
    """
    return resize_image(image_content, size, format)


def process_and_save_image_versions(
    upload_file: UploadFile,
    subdirectory: str = "categories",
    versions: Dict[str, Tuple[int, int]] = {
        "original": None,  # No resizing for original
        "medium": (800, 800),
        "thumbnail": (200, 200)
    }
) -> str:
    """
    Process an uploaded image and save multiple versions in a single directory.
    
    Args:
        upload_file: The uploaded file
        subdirectory: Subdirectory to save in
        versions: Dictionary of version name to size tuple
                 (None means keep original size)
    
    Returns:
        Path to the image directory (relative to upload folder)
    """
    try:
        # Read file content
        file_content = upload_file.file.read()
        
        # Get file extension from content type or filename
        ext = os.path.splitext(upload_file.filename)[1].lower()
        if not ext:
            ext = ".jpg"  # Default to jpg if no extension
            
        # Generate a secure unique ID for the image directory
        # Just use UUID directly since we only need the ID, not a filename
        image_id = str(uuid.uuid4().hex)
        
        # Create image directory
        image_dir = os.path.join(subdirectory, image_id)
        full_dir = os.path.join(get_upload_dir(), image_dir)
        os.makedirs(full_dir, exist_ok=True)
        
        # Process and save each version
        for version_name, size in versions.items():
            # Process image if size is specified
            if size:
                processed_content = resize_image(file_content, size)
            else:
                processed_content = file_content
                
            # Save the processed image with version in filename
            if version_name == "original":
                filename = f"{image_id}{ext}"  # original doesn't have suffix
            else:
                filename = f"{image_id}-{version_name}{ext}"
                
            file_path = os.path.join(full_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(processed_content)
        
        # Return the relative path to the image directory
        return image_dir
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing image versions: {str(e)}"
        )
