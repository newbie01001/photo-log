"""
Pydantic and SQLAlchemy models for user-related operations.
"""
from sqlalchemy import Column, String, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

from app.database import Base

# SQLAlchemy ORM Model
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # Corresponds to Firebase UID
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    events = relationship("Event", back_populates="host")

# Pydantic Models
class UserProfile(BaseModel):
    """User profile model (from Firebase token for now)."""
    uid: str = Field(..., description="The unique Firebase user ID.")
    email: Optional[EmailStr] = Field(None, description="The user's email address.")
    email_verified: bool = Field(False, description="Indicates if the user's email address has been verified.")
    name: Optional[str] = Field(None, description="The user's display name.")
    
    class Config:
        from_attributes = True

