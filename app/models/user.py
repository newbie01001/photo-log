"""
Pydantic models for user-related operations.
Currently simplified since we're not using a database yet.
Note: This model is very similar to `UserResponse` in `app.models.auth`.
Consider consolidating them into a single model (e.g., `UserBase`) if their purposes fully align.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class UserProfile(BaseModel):
    """User profile model (from Firebase token for now)."""
    uid: str = Field(..., description="The unique Firebase user ID.")
    email: Optional[EmailStr] = Field(None, description="The user's email address.")
    email_verified: bool = Field(False, description="Indicates if the user's email address has been verified.")
    name: Optional[str] = Field(None, description="The user's display name.")
    
    # These will be added when database is implemented:
    # plan: Optional[str] = None
    # limits: Optional[Dict[str, int]] = None

