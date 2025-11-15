"""
Events router - handles all /events/* endpoints for host management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from app.models.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    MessageResponse,
    BulkActionRequest,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/events", tags=["events"])

# --- Mock Database & Helpers ---
# This is a temporary in-memory "database" to make the API functional for demonstration.
# In a real application, this would be replaced with a proper database (e.g., PostgreSQL, MongoDB).
MOCK_DB_EVENTS = {}

async def verify_event_ownership(event_id: str, user: Dict[str, Any]):
    """
    (Placeholder) Verify that the current user owns the event.
    In a real app, this would check the `host_id` in the database.
    """
    if event_id not in MOCK_DB_EVENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found."
        )
    if MOCK_DB_EVENTS[event_id]["host_id"] != user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action on the specified event."
        )
    return MOCK_DB_EVENTS[event_id]

# --- Endpoints ---

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new event. A unique ID will be generated for the event.
    """
    # TODO: Replace this mock implementation with a real database write.
    event_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_event = {
        "id": event_id,
        "host_id": user["uid"],
        "name": event_data.name,
        "description": event_data.description,
        "date": event_data.date,
        "password": event_data.password,
        "cover_image_url": event_data.cover_image_url,
        "created_at": now,
        "updated_at": now,
        "is_active": True,
        "is_archived": False,
        "photo_count": 0,
        "share_link": f"/public/events/{event_id}" # Placeholder for public link
    }
    MOCK_DB_EVENTS[event_id] = new_event
    
    return EventResponse(**new_event)

@router.get("", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all events created by the current host. Supports pagination.
    """
    # TODO: Replace this mock implementation with a real database query.
    user_events = [EventResponse(**e) for e in MOCK_DB_EVENTS.values() if e["host_id"] == user["uid"]]
    
    total_events = len(user_events)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_events = user_events[start:end]
    
    return EventListResponse(
        events=paginated_events,
        total=total_events,
        page=page,
        page_size=page_size,
        has_more=end < total_events
    )

@router.get("/{event_id}", response_model=EventResponse)
async def get_event_detail(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed information for a specific event.
    """
    # TODO: Replace this mock implementation with a real database read.
    event = await verify_event_ownership(event_id, user)
    return EventResponse(**event)

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event_metadata(
    event_id: str,
    event_data: EventUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the metadata for a specific event.
    Only provided fields will be updated.
    """
    # TODO: Replace this mock implementation with a real database update.
    event = await verify_event_ownership(event_id, user)
    
    update_data = event_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            event[key] = value
    event["updated_at"] = datetime.utcnow()
    
    MOCK_DB_EVENTS[event_id] = event
    
    return EventResponse(**event)

@router.delete("/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete an event and all its associated assets. This action is irreversible.
    """
    # TODO: Replace this mock implementation with a real database delete.
    # This should also trigger deletion of associated assets in storage (e.g., photos, cover image).
    await verify_event_ownership(event_id, user)
    del MOCK_DB_EVENTS[event_id]
    
    return MessageResponse(message=f"Event '{event_id}' and all associated assets have been deleted.")

@router.post("/{event_id}/cover", response_model=MessageResponse)
async def upload_event_cover_image(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload or replace the cover image for an event.
    (This endpoint is a placeholder and does not handle file uploads yet).
    """
    # TODO: Implement file upload logic (e.g., using FastAPI's UploadFile).
    # The file would be saved to a storage service (like S3 or Firebase Storage),
    # and the resulting URL would be saved in the event's `cover_image_url` field.
    await verify_event_ownership(event_id, user)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Cover image upload functionality is not yet implemented."
    )

@router.get("/{event_id}/qr", response_model=MessageResponse)
async def get_event_qr_code(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate and retrieve a QR code for the event's public sharing link.
    (This endpoint is a placeholder).
    """
    # TODO: Implement QR code generation logic.
    # This would typically involve a library like `qrcode` to generate an image
    # of the event's `share_link` and return it or its URL.
    await verify_event_ownership(event_id, user)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="QR code generation is not yet implemented."
    )

@router.post("/{event_id}/download", response_model=MessageResponse)
async def trigger_event_photos_zip_export(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger a background task to create a ZIP archive of all photos in the event.
    (This endpoint is a placeholder).
    """
    # TODO: Implement background task for ZIP creation (e.g., using Celery).
    # This would collect all photos from storage, create a ZIP file,
    # and then provide a download link to the user (e.g., via email or a notification).
    await verify_event_ownership(event_id, user)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="ZIP export functionality is not yet implemented."
    )

@router.post("/actions/bulk", response_model=MessageResponse)
async def bulk_actions_on_events(
    request: BulkActionRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Perform a bulk action (e.g., archive, activate) on multiple events at once.
    """
    # TODO: Replace this mock implementation with a real database update.
    if request.action not in ["archive", "activate", "deactivate"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{request.action}'. Must be one of: archive, activate, deactivate."
        )
        
    updated_count = 0
    for event_id in request.event_ids:
        if event_id in MOCK_DB_EVENTS and MOCK_DB_EVENTS[event_id]["host_id"] == user["uid"]:
            if request.action == "archive":
                MOCK_DB_EVENTS[event_id]["is_archived"] = True
            elif request.action == "activate":
                MOCK_DB_EVENTS[event_id]["is_active"] = True
            elif request.action == "deactivate":
                MOCK_DB_EVENTS[event_id]["is_active"] = False
            MOCK_DB_EVENTS[event_id]["updated_at"] = datetime.utcnow()
            updated_count += 1
            
    return MessageResponse(
        message=f"Successfully performed action '{request.action}' on {updated_count} event(s)."
    )
