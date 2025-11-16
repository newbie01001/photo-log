"""
Cloudinary service for handling image uploads.
"""
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from app.config import settings

# Configure Cloudinary using the URL from settings
cloudinary.config(cloudinary_url=settings.cloudinary_url)


def upload_image(file: UploadFile, public_id: str = None) -> dict:
    """
    Uploads an image to Cloudinary.

    Args:
        file: The image file to upload (FastAPI UploadFile).
        public_id: Optional public ID for the image in Cloudinary.

    Returns:
        A dictionary containing the upload result from Cloudinary.
    """
    if not file:
        return None
    
    # The file needs to be read into memory before uploading
    file_content = file.file.read()
    
    upload_result = cloudinary.uploader.upload(
        file_content,
        public_id=public_id,
        overwrite=True  # Overwrite if an image with the same public_id exists
    )
    return upload_result

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
