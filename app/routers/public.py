"""
Public router - handles all /public/* endpoints for visitor access.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import uuid

from app.models.event import (
    PublicEventResponse,
    Event as EventModel,
)
from app.models.photo import (
    PhotoResponse,
    PhotoListResponse,
    Photo as PhotoModel,
)
from app.models.auth import MessageResponse
from app.database import get_db

router = APIRouter(prefix="/public", tags=["public"])


def get_event_by_slug(db: Session, slug: str) -> EventModel:
    """
    Get an event by slug (using event ID as slug for now).
    Returns the event if it exists, is active, and not archived.
    """
    event = db.query(EventModel).filter(
        EventModel.id == slug,
        EventModel.is_active == True,
        EventModel.is_archived == False
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or not available for public access."
        )
    
    return event


def verify_event_password(event: EventModel, password: str) -> bool:
    """
    Verify if the provided password matches the event password.
    """
    if not event.password:
        return True  # No password required
    
    # Simple password comparison (in production, use hashing)
    return event.password == password


@router.get("/events/{slug}", response_model=PublicEventResponse)
async def get_public_event_info(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get public information about an event (name, description, cover, settings).
    This endpoint does not require authentication.
    """
    event = get_event_by_slug(db, slug)
    
    # Count approved photos only
    approved_photo_count = db.query(PhotoModel).filter(
        PhotoModel.event_id == event.id,
        PhotoModel.approved == True
    ).count()
    
    return PublicEventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        date=event.date,
        cover_image_url=event.cover_image_url,
        has_password=event.password is not None,
        photo_count=approved_photo_count,
        is_active=event.is_active
    )


@router.get("/events/{slug}/photos", response_model=PhotoListResponse)
async def get_public_event_photos(
    slug: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of approved photos for a public event.
    Only approved photos are visible to public visitors.
    """
    event = get_event_by_slug(db, slug)
    
    # Only get approved photos
    query = db.query(PhotoModel).filter(
        PhotoModel.event_id == event.id,
        PhotoModel.approved == True
    ).order_by(PhotoModel.uploaded_at.desc())
    
    total_photos = query.count()
    
    offset = (page - 1) * page_size
    photos = query.offset(offset).limit(page_size).all()
    
    return PhotoListResponse(
        photos=photos,
        total=total_photos,
        page=page,
        page_size=page_size,
        has_more=(offset + len(photos)) < total_photos
    )


@router.post("/events/{slug}/verify-password", response_model=MessageResponse)
async def verify_event_password_endpoint(
    slug: str,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Verify the event password before allowing photo uploads.
    Returns success if password is correct or if no password is required.
    """
    event = get_event_by_slug(db, slug)
    
    if not event.password:
        return MessageResponse(message="No password required for this event.")
    
    if verify_event_password(event, password):
        return MessageResponse(message="Password verified successfully.")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password."
        )


@router.post("/events/{slug}/photos", response_model=PhotoResponse)
async def upload_public_photo(
    slug: str,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a photo to a public event.
    Requires password verification if the event has a password set.
    
    Note: File storage integration is still a placeholder.
    The file will be validated but actual storage upload needs to be implemented.
    """
    event = get_event_by_slug(db, slug)
    
    # Verify password if required
    if event.password:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password required to upload photos to this event."
            )
        if not verify_event_password(event, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password."
            )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image."
        )
    
    # Validate file size (e.g., max 10MB)
    file_content = await file.read()
    file_size = len(file_content)
    max_size = 10 * 1024 * 1024  # 10MB
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed size (10MB)."
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty."
        )
    
    # TODO: Upload file to storage service (e.g., S3, Firebase Storage)
    # For now, we'll create a placeholder URL
    # In production, this would be:
    # 1. Upload to storage service
    # 2. Get the public URL
    # 3. Optionally create a thumbnail
    # 4. Store URLs in database
    
    # Placeholder: Generate a URL (in production, this comes from storage service)
    photo_id = str(uuid.uuid4())
    # In a real implementation, you would upload to storage and get the URL
    # For now, we'll use a placeholder
    file_url = f"https://storage.example.com/photos/{photo_id}/{file.filename}"
    thumbnail_url = f"https://storage.example.com/photos/{photo_id}/thumb_{file.filename}"
    
    # Create photo record in database
    # Photos uploaded by public visitors start as unapproved (approved=False)
    new_photo = PhotoModel(
        id=photo_id,
        event_id=event.id,
        url=file_url,
        thumbnail_url=thumbnail_url,
        caption=caption,
        approved=False,  # Requires host approval
        uploaded_by=None  # Could be an anonymous identifier or email if provided
    )
    
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    
    return new_photo

