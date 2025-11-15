from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, func, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

# SQLAlchemy ORM Model
class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    host_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    password = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    host = relationship("User", back_populates="events")
    photos = relationship("Photo", back_populates="event", cascade="all, delete-orphan")

# Pydantic Models
class EventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The name of the event.")
    description: Optional[str] = Field(None, max_length=500, description="A short description of the event.")
    date: datetime = Field(..., description="The date and time of the event.")
    password: Optional[str] = Field(None, min_length=4, max_length=50, description="Optional password for public access to the event.")
    cover_image_url: Optional[str] = Field(None, description="URL to the event's cover image.")

class EventCreate(EventBase):
    """Model for creating a new event."""
    pass

class EventUpdate(BaseModel):
    """Model for updating an existing event."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="The new name of the event.")
    description: Optional[str] = Field(None, max_length=500, description="The new description of the event.")
    date: Optional[datetime] = Field(None, description="The new date and time of the event.")
    password: Optional[str] = Field(None, min_length=4, max_length=50, description="The new password for the event.")
    cover_image_url: Optional[str] = Field(None, description="The new cover image URL for the event.")
    is_active: Optional[bool] = Field(None, description="Set to true to make the event active, false to deactivate.")
    is_archived: Optional[bool] = Field(None, description="Set to true to archive the event.")

class EventResponse(EventBase):
    """Model for representing an event in API responses."""
    id: str = Field(..., description="The unique identifier for the event.")
    host_id: str = Field(..., description="The ID of the user who owns the event.")
    created_at: datetime = Field(..., description="The timestamp when the event was created.")
    updated_at: datetime = Field(..., description="The timestamp when the event was last updated.")
    is_active: bool = Field(..., description="Indicates if the event is currently active.")
    is_archived: bool = Field(..., description="Indicates if the event is archived.")
    photo_count: int = Field(0, description="The number of photos in the event.")
    share_link: Optional[str] = Field(None, description="The public, shareable link for the event.")

    class Config:
        from_attributes = True

class PublicEventResponse(BaseModel):
    """Model for public event information (no sensitive data)."""
    id: str = Field(..., description="The unique identifier for the event.")
    name: str = Field(..., description="The name of the event.")
    description: Optional[str] = Field(None, description="A short description of the event.")
    date: datetime = Field(..., description="The date and time of the event.")
    cover_image_url: Optional[str] = Field(None, description="URL to the event's cover image.")
    has_password: bool = Field(..., description="Indicates if the event requires a password.")
    photo_count: int = Field(0, description="The number of approved photos in the event.")
    is_active: bool = Field(..., description="Indicates if the event is currently active.")

    class Config:
        from_attributes = True

class EventListResponse(BaseModel):
    """Model for a paginated list of events."""
    events: List[EventResponse] = Field(..., description="The list of events for the current page.")
    total: int = Field(..., description="The total number of events.")
    page: int = Field(..., description="The current page number.")
    page_size: int = Field(..., description="The number of events per page.")
    has_more: bool = Field(..., description="Indicates if there are more pages of events available.")

class MessageResponse(BaseModel):
    """A generic message response model."""
    message: str

class BulkActionRequest(BaseModel):
    """Model for performing bulk actions on events."""
    event_ids: List[str] = Field(..., description="A list of event IDs to perform the action on.")
    action: str = Field(..., description="The action to perform (e.g., 'archive', 'activate', 'deactivate').")
