"""
Pydantic models for authentication requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class TokenRequest(BaseModel):
    """Request model for endpoints that receive Firebase ID token."""
    token: str = Field(..., description="Firebase ID token provided by the client after authentication.")


class UserResponse(BaseModel):
    """User information response model."""
    uid: str = Field(..., description="The unique Firebase user ID.")
    email: Optional[EmailStr] = Field(None, description="The user's email address.")
    email_verified: bool = Field(False, description="Indicates if the user's email address has been verified.")
    name: Optional[str] = Field(None, description="The user's display name.")


class SigninResponse(BaseModel):
    """Response model for signin/signup endpoints."""
    token: str = Field(..., description="The Firebase ID token for the authenticated session.")
    user: UserResponse = Field(..., description="Details of the authenticated user.")


class VerifyEmailRequest(BaseModel):
    """Request model for email verification."""
    token: str = Field(..., description="Firebase ID token after email verification, indicating the email is now verified.")


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password (frontend handles, backend just acknowledges)."""
    email: EmailStr = Field(..., description="The email address for which to send a password reset link.")


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    token: str = Field(..., description="Firebase ID token obtained after a successful password reset operation.")


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    name: Optional[str] = Field(None, description="The new display name for the user.")


class MessageResponse(BaseModel):
    """Generic success or informational message response."""
    message: str = Field(..., description="A descriptive message about the operation's outcome.")

