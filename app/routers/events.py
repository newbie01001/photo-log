"""
Events router - handles all /events/* endpoints for host management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app.dependencies import get_current_user

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
from app.dependencies import get_current_user
from app.services.cloudinary import upload_image
from app.crud import get_user_upload_size
import cloudinary

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

@router.post("/{event_id}/cover", response_model=EventResponse)
async def upload_event_cover_image(
    event_id: str,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload or replace the cover image for an event.
    """
    event = verify_event_ownership(db, event_id, user["uid"])

    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image."
        )

    # Read file content to get size
    file_content = await file.read()
    file_size = len(file_content)
    await file.seek(0)  # Reset file pointer

    # Check upload limit
    MAX_UPLOAD_SIZE_PER_USER = 1 * 1024 * 1024 * 1024  # 1GB
    current_upload_size = get_user_upload_size(db, user["uid"])
    if current_upload_size + file_size > MAX_UPLOAD_SIZE_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload limit exceeded. You have {round(current_upload_size / (1024*1024*1024), 2)}GB uploaded. Max allowed is 1GB."
        )

    # Upload image to Cloudinary
    try:
        # We can use the event_id as part of the public_id to keep it unique
        public_id = f"event_covers/{event_id}_{uuid.uuid4()}"
        upload_result = upload_image(file, public_id=public_id)
        if not upload_result or "secure_url" not in upload_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload cover image."
            )
        
        event.cover_image_url = upload_result["secure_url"]
        event.cover_thumbnail_url = cloudinary.CloudinaryImage(upload_result["public_id"]).build_url(
            transformation=[
                {'width': 400, 'height': 400, 'crop': 'fill'}
            ]
        )
        event.cover_image_file_size = file_size
        db.commit()
        db.refresh(event)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during cover image upload: {str(e)}"
        )
    
    return event

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
