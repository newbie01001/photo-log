"""
Pydantic and SQLAlchemy models for photo-related operations.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

# SQLAlchemy ORM Model
class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    caption = Column(Text, nullable=True)
    approved = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String, nullable=True) # Stores the host's ID for public uploads, or the user's ID for authenticated uploads.
    public_uploader_identifier = Column(String, nullable=True) # Unique identifier for anonymous public uploader
    file_size = Column(String, nullable=True)

    event = relationship("Event", back_populates="photos")

# Pydantic Models
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

class PhotoResponse(BaseModel):
    """Photo information response."""
    id: str = Field(..., description="The unique identifier for the photo.")
    event_id: str = Field(..., description="The ID of the event this photo belongs to.")
    url: str = Field(..., description="The URL to the full-size photo.")
    thumbnail_url: Optional[str] = Field(None, description="The URL to the photo's thumbnail.")
    caption: Optional[str] = Field(None, description="The caption for the photo.")
    approved: bool = Field(False, description="Indicates if the photo has been approved for public viewing.")
    uploaded_at: datetime = Field(..., description="The timestamp when the photo was uploaded.")
    uploaded_by: Optional[str] = Field(None, description="Identifier of the user who uploaded the photo (for authenticated uploads) or the host (for public uploads).")
    public_uploader_identifier: Optional[str] = Field(None, description="Unique identifier for the anonymous public uploader.")
    file_size: Optional[int] = Field(None, description="The size of the photo in bytes.")

    class Config:
        from_attributes = True

class PhotoListResponse(BaseModel):
    """Paginated list of photos."""
    photos: List[PhotoResponse] = Field(..., description="The list of photos for the current page.")
    total: int = Field(..., description="The total number of photos matching the criteria.")
    page: int = Field(..., description="The current page number.")
    page_size: int = Field(..., description="The number of photos per page.")
    has_more: bool = Field(..., description="Indicates if there are more pages of photos available.")