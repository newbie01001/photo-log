"""
CRUD (Create, Read, Update, Delete) operations for database models.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from sqlalchemy import func, cast, Integer
from sqlalchemy.exc import IntegrityError
import logging

from app.models.user import User as UserModel

logger = logging.getLogger(__name__)


from app.models.event import Event as EventModel
from app.models.photo import Photo as PhotoModel

def get_or_create_user(db: Session, user_info: Dict[str, Any], is_signup: bool = False) -> UserModel:
    """
    Retrieves a user from the database or creates a new one if they don't exist.
    
    Args:
        db: Database session
        user_info: Dictionary containing user information (uid, email, name, etc.)
        is_signup: If True, this is a signup operation. If email exists with different UID, raise error.
                   If False (signin), return existing user even if UID differs (for account linking scenarios).
    
    Returns:
        UserModel: The user object
        
    Raises:
        ValueError: If is_signup=True and email already exists with a different UID
    """
    email = user_info.get("email")
    uid = user_info.get("uid")
    
    if not email:
        raise ValueError("Email is required for user creation")
    
    # Check if a user with this email already exists
    user = db.query(UserModel).filter(UserModel.email == email).first()
    
    if user:
        # User already exists, check if the UID matches
        if user.id != uid:
            if is_signup:
                # During signup, reject if email exists with different UID
                logger.error(
                    f"Signup rejected: Email {email} already exists with UID {user.id}, "
                    f"but signup attempted with UID {uid}. User should sign in instead."
                )
                raise ValueError(
                    f"An account with this email already exists. Please sign in instead. "
                    f"If you forgot your password, use the 'Forgot Password' option."
                )
            else:
                # During signin, log warning but allow (for account linking scenarios)
                logger.warning(
                    f"User with email {email} already exists with UID {user.id}, "
                    f"but signin attempted with UID {uid}. Returning existing user."
                )
        
        # Update name if provided and different
        if user.name != user_info.get("name") and user_info.get("name") is not None:
            user.name = user_info.get("name")
            db.commit()
            db.refresh(user)
        
        return user
    else:
        # User does not exist, create a new one
        try:
            new_user = UserModel(
                id=uid,
                email=email,
                name=user_info.get("name"),
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return db.query(UserModel).filter(UserModel.id == new_user.id).first()
        except IntegrityError as e:
            # Handle race condition: another request created the user between our check and insert
            db.rollback()
            logger.warning(f"Integrity error creating user (likely race condition): {e}")
            # Try to fetch the user that was just created
            user = db.query(UserModel).filter(
                (UserModel.email == email) | (UserModel.id == uid)
            ).first()
            if user:
                return user
            raise ValueError(f"Failed to create user: {e}")

def get_user_upload_size(db: Session, user_id: str) -> int:
    """
    Calculates the total upload size for a user in bytes.
    """
    total_size = 0

    # Sum of photo file sizes - cast string to integer for sum operation
    photo_size = db.query(func.sum(cast(PhotoModel.file_size, Integer))).filter(PhotoModel.uploaded_by == user_id).scalar()
    if photo_size:
        total_size += photo_size

    # Sum of event cover image file sizes - cast string to integer for sum operation
    event_cover_size = db.query(func.sum(cast(EventModel.cover_image_file_size, Integer))).join(UserModel).filter(UserModel.id == user_id).scalar()
    if event_cover_size:
        total_size += event_cover_size

    # User avatar size - cast string to integer
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user and user.avatar_file_size:
        try:
            total_size += int(user.avatar_file_size)
        except (ValueError, TypeError):
            pass  # Skip if conversion fails

    return total_size
