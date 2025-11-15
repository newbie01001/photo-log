"""
Photos router - handles photo moderation endpoints for hosts.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from app.models.photo import (
    PhotoResponse,
    PhotoListResponse,
    UpdatePhotoRequest,
    BulkDeleteRequest,
    BulkDownloadRequest,
)
from app.dependencies import get_current_user
from app.models.auth import MessageResponse # Keep unused imports as per user instruction

router = APIRouter(prefix="/events", tags=["photos"])

# --- Mock Database & Helpers ---
# This is a temporary in-memory "database" for photos.
# In a real application, this would be replaced with a proper database.
MOCK_DB_PHOTOS = {}

# (Re-using MOCK_DB_EVENTS from app/routers/events.py for context)
# In a real app, this would be a shared database connection.
# For now, we'll simulate event existence.
from app.routers.events import MOCK_DB_EVENTS as MOCK_DB_EVENTS_FOR_PHOTOS

async def verify_event_ownership_for_photos(event_id: str, user: Dict[str, Any]):
    """
    (Placeholder) Verify that the current user owns the event.
    In a real app, this would check the `host_id` in the database.
    """
    # TODO: Replace with actual database check for event ownership
    if event_id not in MOCK_DB_EVENTS_FOR_PHOTOS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found."
        )
    if MOCK_DB_EVENTS_FOR_PHOTOS[event_id]["host_id"] != user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage photos for this event."
        )
    return True # Ownership verified

# --- Endpoints ---

@router.get("/{event_id}/photos", response_model=PhotoListResponse)
async def get_event_photos(
    event_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a paginated list of photos for a specific event.
    Only the event owner (host) can see all photos, including unapproved ones.
    """
    await verify_event_ownership_for_photos(event_id, user)
    
    # TODO: Replace this mock implementation with a real database query for photos
    event_photos = [PhotoResponse(**p) for p in MOCK_DB_PHOTOS.values() if p["event_id"] == event_id]
    
    total_photos = len(event_photos)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_photos = event_photos[start:end]
    
    return PhotoListResponse(
        photos=paginated_photos,
        total=total_photos,
        page=page,
        page_size=page_size,
        has_more=end < total_photos
    )

@router.patch("/{event_id}/photos/{photo_id}", response_model=PhotoResponse)
async def update_photo(
    event_id: str,
    photo_id: str,
    request: UpdatePhotoRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update metadata (caption, approval status) for a specific photo within an event.
    """
    await verify_event_ownership_for_photos(event_id, user)
    
    # TODO: Replace this mock implementation with a real database update
    if photo_id not in MOCK_DB_PHOTOS or MOCK_DB_PHOTOS[photo_id]["event_id"] != event_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID '{photo_id}' not found in event '{event_id}'."
        )
    
    photo = MOCK_DB_PHOTOS[photo_id]
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            photo[key] = value
    
    MOCK_DB_PHOTOS[photo_id] = photo
    
    return PhotoResponse(**photo)

@router.delete("/{event_id}/photos/{photo_id}", response_model=MessageResponse)
async def delete_photo(
    event_id: str,
    photo_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a single photo from an event.
    """
    await verify_event_ownership_for_photos(event_id, user)
    
    # TODO: Replace this mock implementation with real database and storage deletion
    if photo_id not in MOCK_DB_PHOTOS or MOCK_DB_PHOTOS[photo_id]["event_id"] != event_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID '{photo_id}' not found in event '{event_id}'."
        )
    
    del MOCK_DB_PHOTOS[photo_id]
    
    return MessageResponse(message=f"Photo '{photo_id}' deleted successfully from event '{event_id}'.")

@router.post("/{event_id}/photos/bulk-delete", response_model=MessageResponse)
async def bulk_delete_photos(
    event_id: str,
    request: BulkDeleteRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete multiple photos from an event at once.
    """
    await verify_event_ownership_for_photos(event_id, user)
    
    # TODO: Replace this mock implementation with real database and storage deletion
    deleted_count = 0
    for photo_id in request.photo_ids:
        if photo_id in MOCK_DB_PHOTOS and MOCK_DB_PHOTOS[photo_id]["event_id"] == event_id:
            del MOCK_DB_PHOTOS[photo_id]
            deleted_count += 1
            
    return MessageResponse(
        message=f"Successfully deleted {deleted_count} photo(s) from event '{event_id}'."
    )

@router.post("/{event_id}/photos/bulk-download", response_model=MessageResponse)
async def bulk_download_photos(
    event_id: str,
    request: BulkDownloadRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger a download of selected photos from an event (e.g., returns a download link or ZIP).
    (This endpoint is a placeholder).
    """
    await verify_event_ownership_for_photos(event_id, user)
    
    # TODO: Implement logic to create a ZIP file of selected photos and return a download link.
    # This might involve a background task for large downloads.
    
    return MessageResponse(
        message=f"Download prepared for {len(request.photo_ids)} photo(s) from event '{event_id}'. "
                 "Download link will be provided shortly."
    )