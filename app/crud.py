"""
CRUD (Create, Read, Update, Delete) operations for database models.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.user import User as UserModel

from app.models.event import Event as EventModel
from app.models.photo import Photo as PhotoModel
from sqlalchemy import func

def get_or_create_user(db: Session, user_info: Dict[str, Any]) -> UserModel:
    """
    Retrieves a user from the database or creates a new one if they don't exist.
    """
    user = db.query(UserModel).filter(UserModel.id == user_info["uid"]).first()
    if not user:
        user = UserModel(
            id=user_info["uid"],
            email=user_info["email"],
            name=user_info.get("name"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_user_upload_size(db: Session, user_id: str) -> int:
    """
    Calculates the total upload size for a user in bytes.
    """
    total_size = 0

    # Sum of photo file sizes
    photo_size = db.query(func.sum(PhotoModel.file_size)).filter(PhotoModel.uploaded_by == user_id).scalar()
    if photo_size:
        total_size += photo_size

    # Sum of event cover image file sizes
    event_cover_size = db.query(func.sum(EventModel.cover_image_file_size)).join(UserModel).filter(UserModel.id == user_id).scalar()
    if event_cover_size:
        total_size += event_cover_size

    # User avatar size
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user and user.avatar_file_size:
        total_size += user.avatar_file_size

    return total_size
