from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.models.auth import (
    TokenRequest,
    SigninResponse,
    UserResponse,
    VerifyEmailRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    MessageResponse,
)
from app.dependencies import get_current_user
from app.services.firebase import verify_firebase_token

router = APIRouter(prefix="/me", tags=["me"])

# Protected routes (require authentication)

@router.get("", response_model=UserResponse)
async def get_current_user_profile(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current host profile.
    
    Returns user information derived from the verified Firebase token.
    TODO: Query database for a more complete user profile including plan/limits.
    """
    return UserResponse(
        uid=user["uid"],
        email=user.get("email"),
        email_verified=user.get("email_verified", False),
        name=user.get("name"),
    )


@router.patch("", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update profile settings (e.g., name).
    
    Currently, this endpoint acknowledges the update and returns the (potentially updated)
    user information from the token. It does NOT persist changes to a database yet.
    TODO: Update user profile in database.
    """
    # For now, just acknowledge the update and reflect the change in the response
    # TODO: Update user profile in database
    
    return UserResponse(
        uid=user["uid"],
        email=user.get("email"),
        email_verified=user.get("email_verified", False),
        name=request.name if request.name else user.get("name"),
    )


@router.patch("/password", response_model=MessageResponse)
async def change_password(
    request: TokenRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Change password (authenticated).
    
    Frontend handles the password change with Firebase.
    Backend receives a new token after a successful password change and verifies it.
    """
    try:
        verify_firebase_token(request.token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token after password change: {e.detail}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return MessageResponse(message="Password changed successfully")

