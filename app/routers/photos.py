"""
Photos router - handles photo moderation endpoints for hosts and public uploads.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import uuid
import logging

from app.models.photo import (
    PhotoResponse,
    PhotoListResponse,
    UpdatePhotoRequest,
    BulkDeleteRequest,
    BulkDownloadRequest,
    Photo as PhotoModel,
)
from app.models.event import Event as EventModel
from app.dependencies import get_current_user
from app.database import get_db
from app.routers.events import verify_event_ownership
from app.models.auth import MessageResponse
from app.services.email import email_service
from app.services.cloudinary import delete_image

logger = logging.getLogger(__name__)

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
    
    # Get event for email context
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found."
        )
    
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id, PhotoModel.event_id == event_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID '{photo_id}' not found in event '{event_id}'."
        )
    
    # Track if approval status changed
    old_approved_status = photo.approved
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(photo, key, value)
    
    db.commit()
    db.refresh(photo)
    
    # Send email notification if approval status changed and photo was uploaded by a public user
    if 'approved' in update_data and photo.uploaded_by and photo.uploaded_by != event.host_id:
        try:
            # Check if approval status actually changed
            if old_approved_status != photo.approved:
                if photo.approved:
                    # Photo was approved
                    email_service.send_photo_approved_email(
                        user_email=photo.uploaded_by,  # Assuming uploaded_by contains email
                        event_name=event.name,
                        photo_url=photo.url,
                        user_name=None
                    )
                else:
                    # Photo was rejected/unapproved
                    email_service.send_photo_rejected_email(
                        user_email=photo.uploaded_by,
                        event_name=event.name,
                        reason=None,
                        user_name=None
                    )
        except Exception as e:
            logger.warning(f"Failed to send photo notification email: {e}")
    
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
    
    # Extract public_id from Cloudinary URL
    # Assuming URL format like: https://res.cloudinary.com/<cloud_name>/image/upload/v<version>/<public_id>.<extension>
    try:
        public_id = "/".join(photo.url.split('/')[-2:]).split('.')[0]
        delete_image(public_id)
    except Exception as e:
        logger.error(f"Failed to delete image from Cloudinary for photo {photo_id}: {e}")
        # Decide whether to raise an HTTPException or just log and proceed.
        # For now, we'll log and proceed to delete the DB record to avoid orphaned DB entries.
        # raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     detail=f"Failed to delete image from storage: {str(e)}"
        # )
    
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
    
    # Fetch photos to get their Cloudinary URLs
    photos_to_delete = query.all()
    
    for photo in photos_to_delete:
        try:
            public_id = "/".join(photo.url.split('/')[-2:]).split('.')[0]
            delete_image(public_id)
        except Exception as e:
            logger.error(f"Failed to delete image from Cloudinary for photo {photo.id}: {e}")
            # Log the error but continue with other deletions and DB record deletion
            
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
