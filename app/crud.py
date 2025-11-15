"""
CRUD (Create, Read, Update, Delete) operations for database models.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.user import User as UserModel

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
