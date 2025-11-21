"""
Authentication router - handles all /auth/* endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from app.models.auth import (
    TokenRequest,
    SigninResponse,
    UserResponse,
    VerifyEmailRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)
from app.services.firebase import verify_firebase_token
from app.services.email import email_service
from app.database import get_db
from app.crud import get_or_create_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SigninResponse)
async def signup(request: TokenRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Register a new host user.
    
    Verifies the Firebase token and creates a corresponding user in the database if one doesn't already exist.
    Rejects signup if email already exists with a different UID (user should sign in instead).
    """
    try:
        user_info = verify_firebase_token(request.token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token during signup: {e.detail}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = get_or_create_user(db, user_info, is_signup=True)
    except ValueError as e:
        # Handle case where email exists with different UID
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    # Send welcome email in the background
    background_tasks.add_task(
        email_service.send_welcome_email,
        user_email=user.email,
        user_name=user.name
    )
    
    user_response = UserResponse(
        uid=user.id,
        email=user.email,
        email_verified=user_info.get("email_verified", False), 
        name=user.name,
    )
    
    return SigninResponse(
        token=request.token,
        user=user_response
    )


@router.post("/signin", response_model=SigninResponse)
async def signin(request: TokenRequest, db: Session = Depends(get_db)):
    """
    Host login - verifies Firebase token and ensures user exists in the database.
    
    If the user doesn't exist in the local database (e.g., first sign-in with a social provider),
    a new user record is created.
    """
    try:
        user_info = verify_firebase_token(request.token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token during signin: {e.detail}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_or_create_user(db, user_info)
    
    user_response = UserResponse(
        uid=user.id,
        email=user.email,
        email_verified=user_info.get("email_verified", False),
        name=user.name,
    )
    
    return SigninResponse(
        token=request.token,
        user=user_response
    )


@router.post("/signout", response_model=MessageResponse)
async def signout():
    """
    Sign out - invalidate session/token.
    
    Frontend handles Firebase signout (revokes token client-side).
    Backend just returns success. No token invalidation logic needed on backend if using JWTs.
    """
    return MessageResponse(message="Signed out successfully")


@router.post("/refresh", response_model=SigninResponse)
async def refresh(request: TokenRequest):
    """
    Refresh authentication token.
    
    Frontend gets new token from Firebase, backend verifies it.
    """
    try:
        user_info = verify_firebase_token(request.token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token during refresh: {e.detail}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_response = UserResponse(
        uid=user_info["uid"],
        email=user_info.get("email"),
        email_verified=user_info.get("email_verified", False),
        name=user_info.get("name"),
    )
    
    return SigninResponse(
        token=request.token,
        user=user_response
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_confirm(request: VerifyEmailRequest): # Renamed to avoid confusion with local variable
    """
    Confirm email verification status.
    
    Frontend handles email verification flow with Firebase.
    Backend receives a token (after Firebase has marked email as verified) and confirms verification.
    """
    try:
        user_info = verify_firebase_token(request.token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token during email verification: {e.detail}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Update user's email_verified status in database if applicable
    # For now, we assume the token already contains the updated status
    
    if not user_info.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not marked as verified in the provided token."
        )

    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_link(): # Renamed for clarity
    """
    Request a new email verification link.
    
    Frontend calls Firebase to resend the verification email to the user.
    Backend just acknowledges the request.
    """
    # TODO: Optionally, add rate limiting or user-specific logic if desired.
    return MessageResponse(message="Verification email sent")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password_request(request: ForgotPasswordRequest): # Renamed for clarity
    """
    Initiate the forgot password flow by sending a reset email.
    
    Frontend handles the actual password reset email sending via Firebase.
    Backend just acknowledges the request for the specific email.
    """
    # TODO: Optionally, add rate limiting or user-specific logic.
    return MessageResponse(message="Password reset email sent to " + request.email) # Added email to response message


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_confirm(request: ResetPasswordRequest): # Renamed for clarity
    """
    Confirm password reset and set new password after a successful reset on the frontend.
    
    Frontend handles password reset with Firebase.
    Backend receives new token after reset and verifies it.
    """
    try:
        user_info = verify_firebase_token(request.token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token during password reset confirmation: {e.detail}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Optionally, update any relevant database fields if needed after password reset.
    
    return MessageResponse(message="Password reset successfully")
