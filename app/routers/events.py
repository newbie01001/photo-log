"""
Events router - handles all /events/* endpoints for host management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from app.models.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    MessageResponse,
    BulkActionRequest,
    Event as EventModel,
)
from app.crud import get_or_create_user
from app.database import get_db

router = APIRouter(prefix="/events", tags=["events"])

# --- Helper Functions ---

def verify_event_ownership(db: Session, event_id: str, user_id: str) -> EventModel:
    """
    Verify that the current user owns the event.
    """
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found."
        )
    if event.host_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action on the specified event."
        )
    return event

# --- Endpoints ---

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new event. A unique ID will be generated for the event.
    """
    host = get_or_create_user(db, user)
    
    new_event = EventModel(
        id=str(uuid.uuid4()),
        host_id=host.id,
        **event_data.dict()
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return new_event

@router.get("", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all events created by the current host. Supports pagination.
    """
    host = get_or_create_user(db, user)
    
    query = db.query(EventModel).filter(EventModel.host_id == host.id)
    total_events = query.count()
    
    offset = (page - 1) * page_size
    events = query.offset(offset).limit(page_size).all()
    
    return EventListResponse(
        events=events,
        total=total_events,
        page=page,
        page_size=page_size,
        has_more=(offset + len(events)) < total_events
    )

@router.get("/{event_id}", response_model=EventResponse)
async def get_event_detail(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific event.
    """
    event = verify_event_ownership(db, event_id, user["uid"])
    return event

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event_metadata(
    event_id: str,
    event_data: EventUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the metadata for a specific event.
    Only provided fields will be updated.
    """
    event = verify_event_ownership(db, event_id, user["uid"])
    
    update_data = event_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
        
    db.commit()
    db.refresh(event)
    
    return event

@router.delete("/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an event and all its associated assets. This action is irreversible.
    """
    event = verify_event_ownership(db, event_id, user["uid"])
    
    # Note: The 'photos' relationship has `cascade="all, delete-orphan"`,
    # so deleting the event will automatically delete its associated photos.
    db.delete(event)
    db.commit()
    
    return MessageResponse(message=f"Event '{event_id}' and all associated assets have been deleted.")

@router.post("/{event_id}/cover", response_model=MessageResponse)
async def upload_event_cover_image(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload or replace the cover image for an event.
    (This endpoint is a placeholder and does not handle file uploads yet).
    """
    verify_event_ownership(db, event_id, user["uid"])
    # TODO: Implement file upload logic (e.g., using FastAPI's UploadFile).
    # The file would be saved to a storage service (like S3 or Firebase Storage),
    # and the resulting URL would be saved in the event's `cover_image_url` field.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Cover image upload functionality is not yet implemented."
    )

@router.get("/{event_id}/qr", response_model=MessageResponse)
async def get_event_qr_code(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and retrieve a QR code for the event's public sharing link.
    (This endpoint is a placeholder).
    """
    verify_event_ownership(db, event_id, user["uid"])
    # TODO: Implement QR code generation logic.
    # This would typically involve a library like `qrcode` to generate an image
    # of the event's `share_link` and return it or its URL.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="QR code generation is not yet implemented."
    )

@router.post("/{event_id}/download", response_model=MessageResponse)
async def trigger_event_photos_zip_export(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger a background task to create a ZIP archive of all photos in the event.
    (This endpoint is a placeholder).
    """
    verify_event_ownership(db, event_id, user["uid"])
    # TODO: Implement background task for ZIP creation (e.g., using Celery).
    # This would collect all photos from storage, create a ZIP file,
    # and then provide a download link to the user (e.g., via email or a notification).
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="ZIP export functionality is not yet implemented."
    )

@router.post("/actions/bulk", response_model=MessageResponse)
async def bulk_actions_on_events(
    request: BulkActionRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform a bulk action (e.g., archive, activate) on multiple events at once.
    """
    if request.action not in ["archive", "activate", "deactivate"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{request.action}'. Must be one of: archive, activate, deactivate."
        )
        
    query = db.query(EventModel).filter(
        EventModel.id.in_(request.event_ids),
        EventModel.host_id == user["uid"]
    )
    
    updated_count = 0
    if request.action == "archive":
        updated_count = query.update({"is_archived": True})
    elif request.action == "activate":
        updated_count = query.update({"is_active": True})
    elif request.action == "deactivate":
        updated_count = query.update({"is_active": False})
        
    db.commit()
            
    return MessageResponse(
        message=f"Successfully performed action '{request.action}' on {updated_count} event(s)."
    )
