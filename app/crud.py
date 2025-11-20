"""
CRUD (Create, Read, Update, Delete) operations for database models.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any
from sqlalchemy import func, cast, Integer
import logging

from app.models.user import User as UserModel

logger = logging.getLogger(__name__)


from app.models.event import Event as EventModel
from app.models.photo import Photo as PhotoModel

def get_or_create_user(db: Session, user_info: Dict[str, Any]) -> UserModel:
    """
    Retrieves a user from the database or creates a new one if they don't exist.
    """
    # Check if a user with this email already exists
    user = db.query(UserModel).filter(UserModel.email == user_info["email"]).first()
    
    if user:
        # User already exists, check if the UID matches
        if user.id != user_info["uid"]:
            # Log a warning if the UID is different
            logger.warning(f"User with email {user.email} already exists with a different UID.")
        if user.name != user_info.get("name") and user_info.get("name") is not None:
            user.name = user_info.get("name")
            db.commit()
            db.refresh(user)
        return user
    else:
        # User does not exist, create a new one
        new_user = UserModel(
            id=user_info["uid"],
            email=user_info["email"],
            name=user_info.get("name"),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return db.query(UserModel).filter(UserModel.id == new_user.id).first()

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
