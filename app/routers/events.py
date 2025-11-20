"""
Events router - handles all /events/* endpoints for host management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Response
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import io
import qrcode
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
from app.config import settings

router = APIRouter(prefix="/events", tags=["events"])

# --- Helper Functions ---

def generate_share_link(event_id: str) -> str:
    """
    Generate a public share link for an event.
    Uses the frontend URL from settings.
    """
    # For now, using event ID as slug
    # In the future, this could use a proper slug field
    base_url = settings.frontend_url.rstrip('/')
    return f"{base_url}/event/{event_id}"

def event_to_response(event: EventModel, db: Session = None, photo_count: int = None) -> EventResponse:
    """
    Convert an Event model to EventResponse with computed fields.
    """
    from app.models.photo import Photo as PhotoModel
    
    # Count photos if not provided
    if photo_count is None:
        if db:
            photo_count = db.query(PhotoModel).filter(PhotoModel.event_id == event.id).count()
        else:
            # Fallback: try to use relationship if loaded
            photo_count = len(event.photos) if hasattr(event, 'photos') and event.photos else 0
    
    # Create response dict
    # Handle updated_at: if None (newly created event), use created_at as fallback
    updated_at = event.updated_at if event.updated_at is not None else event.created_at
    
    response_dict = {
        "id": event.id,
        "host_id": event.host_id,
        "name": event.name,
        "description": event.description,
        "date": event.date,
        "password": event.password,
        "cover_image_url": event.cover_image_url,
        "cover_thumbnail_url": event.cover_thumbnail_url,
        "cover_image_file_size": event.cover_image_file_size,
        "is_active": event.is_active,
        "is_archived": event.is_archived,
        "created_at": event.created_at,
        "updated_at": updated_at,
        "photo_count": photo_count,
        "share_link": generate_share_link(event.id)
    }
    
    return EventResponse(**response_dict)

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
    
    return event_to_response(new_event, db=db, photo_count=0)

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
    
    # Convert events to response format with share links
    event_responses = [event_to_response(event, db=db) for event in events]
    
    return EventListResponse(
        events=event_responses,
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
    return event_to_response(event, db=db)

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
    
    return event_to_response(event, db=db)

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

@router.get("/{event_id}/qr")
async def get_event_qr_code(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
    size: int = Query(10, ge=1, le=20, description="QR code size (1-20, default 10)")
):
    """
    Generate and retrieve a QR code for the event's public sharing link.
    Returns a PNG image of the QR code that can be scanned to access the event.
    """
    event = verify_event_ownership(db, event_id, user["uid"])
    
    # Generate the share link
    share_link = generate_share_link(event_id)
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code (1 is smallest)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
        box_size=size,  # Size of each box in pixels
        border=4,  # Border thickness in boxes
    )
    
    # Add data to QR code
    qr.add_data(share_link)
    qr.make(fit=True)
    
    # Create image from QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Return image as response
    return Response(
        content=img_bytes.getvalue(),
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="event-{event_id}-qr.png"'
        }
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
