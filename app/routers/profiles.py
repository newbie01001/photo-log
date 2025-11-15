from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from sqlalchemy.orm import Session

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
from app.database import get_db
from app.crud import get_or_create_user

router = APIRouter(prefix="/me", tags=["me"])

# Protected routes (require authentication)

@router.get("", response_model=UserResponse)
async def get_current_user_profile(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current host profile from the database.
    """
    db_user = get_or_create_user(db, user)
    return UserResponse(
        uid=db_user.id,
        email=db_user.email,
        email_verified=user.get("email_verified", False), # This still comes from the token
        name=db_user.name,
    )


@router.patch("", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update profile settings (e.g., name) in the database.
    """
    db_user = get_or_create_user(db, user)
    
    if request.name is not None:
        db_user.name = request.name
        
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        uid=db_user.id,
        email=db_user.email,
        email_verified=user.get("email_verified", False), # This still comes from the token
        name=db_user.name,
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

