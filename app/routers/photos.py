"""
Photos router - handles photo moderation endpoints for hosts and public uploads.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import uuid

from app.models.photo import (
    PhotoResponse,
    PhotoListResponse,
    UpdatePhotoRequest,
    BulkDeleteRequest,
    BulkDownloadRequest,
    Photo as PhotoModel,
)
from app.dependencies import get_current_user
from app.database import get_db
from app.routers.events import verify_event_ownership
from app.models.auth import MessageResponse # Keep unused imports as per user instruction

router = APIRouter(prefix="/events", tags=["photos"])

# --- Host Moderation Endpoints ---

@router.get("/events/{event_id}/photos", response_model=PhotoListResponse)
async def get_event_photos(
    event_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of photos for a specific event.
    Only the event owner (host) can see all photos, including unapproved ones.
    """
    verify_event_ownership(db, event_id, user["uid"])
    
    query = db.query(PhotoModel).filter(PhotoModel.event_id == event_id)
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

@router.patch("/events/{event_id}/photos/{photo_id}", response_model=PhotoResponse)
async def update_photo(
    event_id: str,
    photo_id: str,
    request: UpdatePhotoRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update metadata (caption, approval status) for a specific photo within an event.
    """
    verify_event_ownership(db, event_id, user["uid"])
    
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id, PhotoModel.event_id == event_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID '{photo_id}' not found in event '{event_id}'."
        )
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(photo, key, value)
        
    db.commit()
    db.refresh(photo)
    
    return photo

@router.delete("/events/{event_id}/photos/{photo_id}", response_model=MessageResponse)
async def delete_photo(
    event_id: str,
    photo_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a single photo from an event.
    """
    verify_event_ownership(db, event_id, user["uid"])
    
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id, PhotoModel.event_id == event_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID '{photo_id}' not found in event '{event_id}'."
        )
    
    db.delete(photo)
    db.commit()
    
    return MessageResponse(message=f"Photo '{photo_id}' deleted successfully from event '{event_id}'.")

@router.post("/events/{event_id}/photos/bulk-delete", response_model=MessageResponse)
async def bulk_delete_photos(
    event_id: str,
    request: BulkDeleteRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete multiple photos from an event at once.
    """
    verify_event_ownership(db, event_id, user["uid"])
    
    query = db.query(PhotoModel).filter(
        PhotoModel.id.in_(request.photo_ids),
        PhotoModel.event_id == event_id
    )
    
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
            
    return MessageResponse(
        message=f"Successfully deleted {deleted_count} photo(s) from event '{event_id}'."
    )

@router.post("/events/{event_id}/photos/bulk-download", response_model=MessageResponse)
async def bulk_download_photos(
    event_id: str,
    request: BulkDownloadRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger a download of selected photos from an event (e.g., returns a download link or ZIP).
    (This endpoint is a placeholder).
    """
    verify_event_ownership(db, event_id, user["uid"])
    
    # TODO: Implement logic to create a ZIP file of selected photos and return a download link.
    
    return MessageResponse(
        message=f"Download prepared for {len(request.photo_ids)} photo(s) from event '{event_id}'. "
                 "Download link will be provided shortly."
    )

# --- Public Visitor Flow Endpoints ---

@router.post("/public/events/{event_slug}/photos", response_model=PhotoResponse)
async def upload_photo(
    event_slug: str,
    file: UploadFile = File(...),
    caption: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload a photo to a public event.
    (This endpoint is a placeholder and does not handle file uploads yet).
    """
    # TODO: 1. Find event by slug.
    # TODO: 2. Verify event password if required.
    # TODO: 3. Upload file to storage service (e.g., S3, Firebase Storage).
    # TODO: 4. Create a new Photo record in the database.
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Public photo upload functionality is not yet implemented."
    )