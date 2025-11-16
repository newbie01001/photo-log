from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Dict, Any
from sqlalchemy.orm import Session
import uuid
import cloudinary

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
from app.crud import get_or_create_user, get_user_upload_size
from app.services.cloudinary import upload_image, delete_image

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
    return UserResponse(
        uid=db_user.id,
        email=db_user.email,
        email_verified=user.get("email_verified", False), # This still comes from the token
        name=db_user.name,
        avatar_url=db_user.avatar_url,
        avatar_thumbnail_url=db_user.avatar_thumbnail_url,
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
    if request.avatar_url is not None:
        db_user.avatar_url = request.avatar_url
    if request.avatar_thumbnail_url is not None:
        db_user.avatar_thumbnail_url = request.avatar_thumbnail_url
        
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        uid=db_user.id,
        email=db_user.email,
        email_verified=user.get("email_verified", False), # This still comes from the token
        name=db_user.name,
        avatar_url=db_user.avatar_url,
        avatar_thumbnail_url=db_user.avatar_thumbnail_url,
    )


@router.post("/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload or replace the user's avatar.
    """
    db_user = get_or_create_user(db, user)

    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image."
        )

    # Read file content to get size
    file_content = await file.read()
    file_size = len(file_content)
    await file.seek(0)  # Reset file pointer

    # Check upload limit
    MAX_UPLOAD_SIZE_PER_USER = 1 * 1024 * 1024 * 1024  # 1GB
    current_upload_size = get_user_upload_size(db, user["uid"])
    if current_upload_size + file_size > MAX_UPLOAD_SIZE_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload limit exceeded. You have {round(current_upload_size / (1024*1024*1024), 2)}GB uploaded. Max allowed is 1GB."
        )

    # Delete old avatar if it exists
    if db_user.avatar_url:
        try:
            public_id = "/".join(db_user.avatar_url.split('/')[-2:]).split('.')[0]
            delete_image(public_id)
        except Exception as e:
            # Log the error but don't block the upload of the new avatar
            print(f"Could not delete old avatar: {e}")

    # Upload new avatar to Cloudinary
    try:
        public_id = f"avatars/{db_user.id}_{uuid.uuid4()}"
        upload_result = upload_image(file, public_id=public_id)
        if not upload_result or "secure_url" not in upload_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload avatar."
            )
        
        db_user.avatar_url = upload_result["secure_url"]
        db_user.avatar_thumbnail_url = cloudinary.CloudinaryImage(upload_result["public_id"]).build_url(
            transformation=[
                {'width': 150, 'height': 150, 'crop': 'fill'}
            ]
        )
        db_user.avatar_file_size = file_size
        db.commit()
        db.refresh(db_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during avatar upload: {str(e)}"
        )
    
    return UserResponse(
        uid=db_user.id,
        email=db_user.email,
        email_verified=user.get("email_verified", False),
        name=db_user.name,
        avatar_url=db_user.avatar_url,
        avatar_thumbnail_url=db_user.avatar_thumbnail_url,
        avatar_file_size=db_user.avatar_file_size,
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

