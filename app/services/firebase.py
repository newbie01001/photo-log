"""
Firebase Admin SDK initialization and token verification.
"""
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from pathlib import Path
from typing import Dict, Any
import logging
import time

from app.config import get_firebase_credentials_path

logger = logging.getLogger(__name__)

# Global variable to track if Firebase is initialized
_firebase_initialized = False


def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK using service account credentials.
    This should be called once at application startup.
    """
    global _firebase_initialized
    
    if _firebase_initialized:
        logger.info("Firebase Admin SDK already initialized")
        return
    
    try:
        cred_path = get_firebase_credentials_path()
        
        if not cred_path.exists():
            raise FileNotFoundError(
                f"Firebase credentials file not found at {cred_path}. "
                "Please download your service account JSON from Firebase Console."
            )
        
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


def verify_firebase_token(token: str, retry_on_clock_skew: bool = True) -> Dict[str, Any]:
    """
    Verify a Firebase ID token and return decoded token information.
    
    Handles clock skew issues by retrying with a small delay if the token is "used too early".
    
    Args:
        token: Firebase ID token string
        retry_on_clock_skew: If True, retry once with a delay if token is used too early
        
    Returns:
        Dictionary containing user information from decoded token:
        - uid: Firebase user ID
        - email: User email
        - email_verified: Whether email is verified
        - name: User's display name
        - firebase_claims: All claims present in the decoded token
        
    Raises:
        HTTPException: If token is invalid, expired, or revoked
    """
    if not _firebase_initialized:
        # This should ideally be handled at application startup, but this acts as a safeguard.
        logger.warning("Firebase Admin SDK not initialized, attempting to initialize now.")
        initialize_firebase()
    
    max_retries = 2 if retry_on_clock_skew else 1
    retry_delay = 0.5  # 500ms delay for clock skew retry
    
    for attempt in range(max_retries):
        try:
            # Verify the token
            decoded_token: Dict[str, Any] = auth.verify_id_token(token)
            
            # Extract user information
            user_info = {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "firebase_claims": decoded_token  # Include all claims for reference
            }
            
            return user_info
            
        except auth.InvalidIdTokenError as e:
            error_str = str(e)
            # Check if it's a clock skew issue ("used too early")
            if retry_on_clock_skew and "used too early" in error_str.lower() and attempt < max_retries - 1:
                logger.info(f"Token used too early (clock skew detected), retrying after {retry_delay}s...")
                time.sleep(retry_delay)
                continue  # Retry once
            
            logger.warning(f"Invalid Firebase ID token provided: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired Firebase ID token provided: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired"
            )
        except auth.RevokedIdTokenError as e:
            logger.warning(f"Revoked Firebase ID token provided: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has been revoked"
            )
        except Exception as e:
            logger.error(f"Unexpected error verifying Firebase token: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying authentication token"
            )

