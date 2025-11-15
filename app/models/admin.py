"""
Pydantic models for Admin Dashboard endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.models.event import EventResponse
from app.models.user import UserProfile
from app.models.photo import PhotoResponse

class OverviewStats(BaseModel):
    """Model for overall system statistics."""
    total_events: int = Field(..., description="Total number of events in the system.")
    total_users: int = Field(..., description="Total number of registered users (hosts).")
    total_photos: int = Field(..., description="Total number of photos uploaded across all events.")
    total_storage_gb: float = Field(..., description="Total storage used in gigabytes (placeholder).")

class RecentUpload(PhotoResponse):
    """Model for a recent upload, extending PhotoResponse with user info."""
    host_email: Optional[str] = Field(None, description="Email of the host of the event where photo was uploaded.")

class RecentUploadsResponse(BaseModel):
    """Paginated list of recent uploads."""
    uploads: List[RecentUpload]
    total: int
    page: int
    page_size: int

class AdminEventResponse(EventResponse):
    """Extended event response for admins, including host info."""
    host: Optional[UserProfile] = Field(None, description="The profile of the user who owns the event.")

class AdminEventListResponse(BaseModel):
    """Paginated list of all events for admins."""
    events: List[AdminEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool

class AdminUserResponse(UserProfile):
    """Extended user profile for admins, including event count."""
    event_count: int = Field(..., description="The number of events created by this user.")
    is_suspended: bool = Field(False, description="Indicates if the user's account is suspended.")

class AdminUserListResponse(BaseModel):
    """Paginated list of all users for admins."""
    users: List[AdminUserResponse]
    total: int
    page: int
    page_size: int
    has_more: bool

class SystemExportResponse(BaseModel):
    """Response model for a system data export request."""
    message: str = Field("System data export initiated. A download link will be sent to your email.", description="Confirmation message for the export request.")
    export_job_id: str = Field(..., description="The ID of the background job handling the export.")