"""
Admin Dashboard router - handles all /admin/* endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List
from datetime import datetime
import uuid

from app.dependencies import get_current_admin_user
from app.models.admin import (
    OverviewStats,
    AdminEventListResponse,
    AdminEventResponse,
    AdminUserListResponse,
    AdminUserResponse,
    RecentUploadsResponse,
    RecentUpload,
    SystemExportResponse,
)
from app.models.auth import MessageResponse
from app.models.event import EventUpdate
from app.models.user import UserProfile # For AdminEventResponse host field

# Import mock databases from other routers for demonstration purposes
from app.routers.events import MOCK_DB_EVENTS
from app.routers.photos import MOCK_DB_PHOTOS

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Mock Database for Users ---
# In a real app, this would be a proper user table in a database.
MOCK_DB_USERS = {
    "user1_uid": {"uid": "user1_uid", "email": "testuser1@example.com", "name": "Test User 1", "is_suspended": False},
    "user2_uid": {"uid": "user2_uid", "email": "testuser2@example.com", "name": "Test User 2", "is_suspended": True},
}

# --- Endpoints ---

@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Get an overview of system-wide totals (events, users, photos, storage).
    """
    # TODO: Replace with real database aggregations.
    total_events = len(MOCK_DB_EVENTS)
    total_users = len(MOCK_DB_USERS)
    total_photos = len(MOCK_DB_PHOTOS)
    total_storage_gb = round(total_photos * 0.005, 2) # Assuming 5MB per photo

    return OverviewStats(
        total_events=total_events,
        total_users=total_users,
        total_photos=total_photos,
        total_storage_gb=total_storage_gb,
    )

@router.get("/events", response_model=AdminEventListResponse)
async def list_all_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    List, search, and filter all events in the system.
    """
    # TODO: Implement search and filtering logic.
    all_events = []
    for event_id, event_data in MOCK_DB_EVENTS.items():
        host_id = event_data.get("host_id")
        host_profile_data = MOCK_DB_USERS.get(host_id)
        host_profile = UserProfile(**host_profile_data) if host_profile_data else None
        all_events.append(AdminEventResponse(**event_data, host=host_profile))
    
    total = len(all_events)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_events = all_events[start:end]

    return AdminEventListResponse(
        events=paginated_events,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )

@router.get("/events/{event_id}", response_model=AdminEventResponse)
async def inspect_event(event_id: str, admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Perform a deep inspection of an event, including its photos, host, and status.
    """
    if event_id not in MOCK_DB_EVENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    event_data = MOCK_DB_EVENTS[event_id]
    # TODO: Fetch host user from a real user database
    host_id = event_data.get("host_id")
    host_profile_data = MOCK_DB_USERS.get(host_id)
    host_profile = UserProfile(**host_profile_data) if host_profile_data else None

    return AdminEventResponse(**event_data, host=host_profile)

@router.patch("/events/{event_id}/status", response_model=AdminEventResponse)
async def update_event_status(
    event_id: str,
    status_update: EventUpdate, # Reusing EventUpdate model for status changes
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Disable, enable, or feature an event.
    """
    if event_id not in MOCK_DB_EVENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    event = MOCK_DB_EVENTS[event_id]
    update_data = status_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if key in ["is_active", "is_archived"] and value is not None:
            event[key] = value
    event["updated_at"] = datetime.utcnow()
    
    return AdminEventResponse(**event)

@router.delete("/events/{event_id}", response_model=MessageResponse)
async def force_delete_event(event_id: str, admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Force-delete an event from the system.
    """
    if event_id not in MOCK_DB_EVENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
    del MOCK_DB_EVENTS[event_id]
    # TODO: Also delete associated photos from MOCK_DB_PHOTOS and storage.
    
    return MessageResponse(message=f"Event '{event_id}' has been force-deleted.")

@router.get("/uploads/recent", response_model=RecentUploadsResponse)
async def get_recent_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Get a feed of recent photo uploads across all events.
    """
    # TODO: Replace with real database query, potentially ordered by upload_at.
    all_uploads = []
    for photo_id, photo_data in MOCK_DB_PHOTOS.items():
        event_id = photo_data.get("event_id")
        event_data = MOCK_DB_EVENTS.get(event_id)
        host_id = event_data.get("host_id") if event_data else None
        host_profile_data = MOCK_DB_USERS.get(host_id)
        host_email = host_profile_data.get("email") if host_profile_data else None
        all_uploads.append(RecentUpload(**photo_data, host_email=host_email))
    
    # Sort by uploaded_at (mock data doesn't have it, so just reverse for now)
    all_uploads.sort(key=lambda x: x.uploaded_at, reverse=True)

    total = len(all_uploads)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_uploads = all_uploads[start:end]

    return RecentUploadsResponse(
        uploads=paginated_uploads,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )

@router.get("/users", response_model=AdminUserListResponse)
async def list_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Get a list of all host accounts.
    """
    # TODO: Replace with real user database query.
    all_users = []
    for user_id, user_data in MOCK_DB_USERS.items():
        event_count = len([e for e in MOCK_DB_EVENTS.values() if e["host_id"] == user_id])
        all_users.append(AdminUserResponse(**user_data, event_count=event_count))
    
    total = len(all_users)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_users = all_users[start:end]

    return AdminUserListResponse(
        users=paginated_users,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )

@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def inspect_user(user_id: str, admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Get a host profile and their events.
    """
    if user_id not in MOCK_DB_USERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_data = MOCK_DB_USERS[user_id]
    event_count = len([e for e in MOCK_DB_EVENTS.values() if e["host_id"] == user_id])
    
    return AdminUserResponse(**user_data, event_count=event_count)

@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def update_user_status(
    user_id: str,
    is_suspended: bool = Query(..., description="Set to true to suspend, false to reactivate."),
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Suspend or reactivate a host account.
    """
    if user_id not in MOCK_DB_USERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    MOCK_DB_USERS[user_id]["is_suspended"] = is_suspended
    
    user_data = MOCK_DB_USERS[user_id]
    event_count = len([e for e in MOCK_DB_EVENTS.values() if e["host_id"] == user_id])
    
    return AdminUserResponse(**user_data, event_count=event_count)

@router.get("/logs", response_model=MessageResponse)
async def get_audit_logs(admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Retrieve audit/event logs (if logging to API).
    """
    # TODO: Implement actual log retrieval from a logging service or database.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Audit log retrieval is not yet implemented."
    )

@router.post("/system/export", response_model=SystemExportResponse)
async def export_system_data(admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Trigger a background job to export system data snapshots.
    """
    # TODO: Implement background task logic (e.g., with Celery).
    job_id = f"export-{uuid.uuid4()}"
    return SystemExportResponse(export_job_id=job_id)
