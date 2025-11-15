"""
Pydantic models for photo-related operations.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# Request models (what the frontend sends)
class UpdatePhotoRequest(BaseModel):
    """Request to update photo metadata."""
    caption: Optional[str] = Field(None, max_length=255, description="New caption for the photo.")
    approved: Optional[bool] = Field(None, description="Set to true to approve the photo, false to unapprove.")

class BulkDeleteRequest(BaseModel):
    """Request to delete multiple photos."""
    photo_ids: List[str] = Field(..., description="List of photo IDs to delete.")

class BulkDownloadRequest(BaseModel):
    """Request to download multiple photos."""
    photo_ids: List[str] = Field(..., description="List of photo IDs to download.")

# Response models (what the backend returns)
class PhotoResponse(BaseModel):
    """Photo information response."""
    id: str = Field(..., description="The unique identifier for the photo.")
    event_id: str = Field(..., description="The ID of the event this photo belongs to.")
    url: str = Field(..., description="The URL to the full-size photo.")
    thumbnail_url: Optional[str] = Field(None, description="The URL to the photo's thumbnail.")
    caption: Optional[str] = Field(None, description="The caption for the photo.")
    approved: bool = Field(False, description="Indicates if the photo has been approved for public viewing.")
    uploaded_at: datetime = Field(..., description="The timestamp when the photo was uploaded.")
    uploaded_by: Optional[str] = Field(None, description="Identifier of the user who uploaded the photo (e.g., email or anonymous ID).")

    class Config:
        from_attributes = True

class PhotoListResponse(BaseModel):
    """Paginated list of photos."""
    photos: List[PhotoResponse] = Field(..., description="The list of photos for the current page.")
    total: int = Field(..., description="The total number of photos matching the criteria.")
    page: int = Field(..., description="The current page number.")
    page_size: int = Field(..., description="The number of photos per page.")
    has_more: bool = Field(..., description="Indicates if there are more pages of photos available.")