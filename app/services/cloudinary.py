"""
Cloudinary service for handling image uploads.
"""
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def _configure_cloudinary():
    """Configure Cloudinary if not already configured."""
    if not settings.cloudinary_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary is not configured. Please set CLOUDINARY_URL environment variable."
        )
    
    try:
        # Try configuring with the URL string first
        cloudinary.config(cloudinary_url=settings.cloudinary_url)
        
        # Verify configuration by checking if api_key is set
        if not cloudinary.config().api_key:
            # If URL format didn't work, try parsing it manually
            # Format: cloudinary://api_key:api_secret@cloud_name
            url = settings.cloudinary_url.replace("cloudinary://", "")
            if "@" in url:
                credentials, cloud_name = url.split("@", 1)
                if ":" in credentials:
                    api_key, api_secret = credentials.split(":", 1)
                    cloudinary.config(
                        cloud_name=cloud_name,
                        api_key=api_key,
                        api_secret=api_secret
                    )
                    logger.info("Cloudinary configured using parsed URL parameters")
                else:
                    raise ValueError("Invalid Cloudinary URL format: missing api_key or api_secret")
            else:
                raise ValueError("Invalid Cloudinary URL format: missing cloud_name")
        else:
            logger.info("Cloudinary configured successfully using URL")
    except Exception as e:
        logger.error(f"Failed to configure Cloudinary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure Cloudinary: {str(e)}. Please check your CLOUDINARY_URL format."
        )

# Configure Cloudinary on module import
if settings.cloudinary_url:
    _configure_cloudinary()


def upload_image(file: UploadFile, public_id: str = None) -> dict:
    """
    Uploads an image to Cloudinary.

    Args:
        file: The image file to upload (FastAPI UploadFile).
        public_id: Optional public ID for the image in Cloudinary.

    Returns:
        A dictionary containing the upload result from Cloudinary.
    
    Raises:
        HTTPException: If Cloudinary is not configured or upload fails.
    """
    # Ensure Cloudinary is configured before upload
    _configure_cloudinary()
    
    if not file:
        return None
    
    try:
        # The file needs to be read into memory before uploading
        # Reset file pointer to beginning in case it was already read
        file.file.seek(0)
        file_content = file.file.read()
        
        upload_result = cloudinary.uploader.upload(
            file_content,
            public_id=public_id,
            overwrite=True  # Overwrite if an image with the same public_id exists
        )
        return upload_result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Cloudinary upload error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image to Cloudinary: {error_msg}"
        )

def delete_image(public_id: str) -> dict:
    """
    Deletes an image from Cloudinary by its public ID.

    Args:
        public_id: The public ID of the image to delete.

    Returns:
        A dictionary containing the deletion result from Cloudinary.
    """
    if not public_id:
        return {"result": "not found"} # Or raise an error, depending on desired behavior
    
    deletion_result = cloudinary.uploader.destroy(public_id)
    return deletion_result
