"""
FastAPI dependencies for authentication and authorization.
"""
from fastapi import Depends, HTTPException, status, Header
from typing import Optional, Dict, Any

from app.services.firebase import verify_firebase_token
from app.config import settings # Moved import to top


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency to verify Firebase token and extract user information.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    
    Args:
        authorization: Authorization header containing "Bearer <token>"
        
    Returns:
        Dictionary with user information (uid, email, email_verified)
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: 'Bearer <token>'", # Refined error message
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token and return user info
    user_info = verify_firebase_token(token)
    return user_info


async def get_current_admin_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    FastAPI dependency to verify if the authenticated user has admin privileges.
    
    Currently, checks if the user's email is in the configured admin_emails list.
    This will be updated to check an `is_admin` flag in the database once implemented.
    
    Usage:
        @app.get("/admin/protected")
        async def admin_route(admin: dict = Depends(get_current_admin_user)):
            return {"admin": admin}
    
    Args:
        user: User info from get_current_user dependency
        
    Returns:
        User info if admin, otherwise raises HTTPException (403 Forbidden)
    """
    user_email = user.get("email")
    
    if not user_email or user_email not in settings.get_admin_emails_list():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user

