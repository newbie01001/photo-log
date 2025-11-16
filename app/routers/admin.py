"""
Admin Dashboard router - handles all /admin/* endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List
from datetime import datetime
import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

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
from app.models.event import EventUpdate, Event as EventModel
from app.models.user import UserProfile, User as UserModel
from app.models.photo import Photo as PhotoModel
from app.database import get_db
from app.services.cloudinary import delete_image

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Endpoints ---

@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get an overview of system-wide totals (events, users, photos, storage).
    """
    total_events = db.query(EventModel).count()
    total_users = db.query(UserModel).count()
    total_photos = db.query(PhotoModel).count()
    
    # Calculate total storage from photos and event covers
    total_photo_storage = db.query(func.sum(PhotoModel.file_size)).scalar() or 0
    total_cover_storage = db.query(func.sum(EventModel.cover_image_file_size)).scalar() or 0
    total_storage_bytes = total_photo_storage + total_cover_storage
    total_storage_gb = round(total_storage_bytes / (1024**3), 4) if total_storage_bytes else 0

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
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List, search, and filter all events in the system.
    """
    # TODO: Implement search and filtering logic.
    query = db.query(EventModel).options(joinedload(EventModel.host))
    total = query.count()
    
    offset = (page - 1) * page_size
    events = query.offset(offset).limit(page_size).all()

    admin_events = []
    for event in events:
        host_profile = UserProfile(
            uid=event.host.id,
            email=event.host.email,
            name=event.host.name,
            email_verified=True # Assuming verified for existing users
        ) if event.host else None
        admin_events.append(AdminEventResponse(**event.__dict__, host=host_profile))

    return AdminEventListResponse(
        events=admin_events,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(events)) < total,
    )

@router.get("/events/{event_id}", response_model=AdminEventResponse)
async def inspect_event(
    event_id: str,
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Perform a deep inspection of an event, including its photos, host, and status.
    """
    event = db.query(EventModel).options(joinedload(EventModel.host)).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    host_profile = UserProfile(
        uid=event.host.id,
        email=event.host.email,
        name=event.host.name,
        email_verified=True
    ) if event.host else None

    return AdminEventResponse(**event.__dict__, host=host_profile)

@router.patch("/events/{event_id}/status", response_model=AdminEventResponse)
async def update_event_status(
    event_id: str,
    status_update: EventUpdate, # Reusing EventUpdate model for status changes
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Disable, enable, or feature an event.
    """
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    update_data = status_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if key in ["is_active", "is_archived"] and value is not None:
            setattr(event, key, value)
    event.updated_at = datetime.utcnow() # Manually update timestamp
    
    db.commit()
    db.refresh(event)

    host_profile = UserProfile(
        uid=event.host.id,
        email=event.host.email,
        name=event.host.name,
        email_verified=True
    ) if event.host else None
    
    return AdminEventResponse(**event.__dict__, host=host_profile)

@router.delete("/events/{event_id}", response_model=MessageResponse)
async def force_delete_event(
    event_id: str,
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Force-delete an event from the system.
    """
    event = db.query(EventModel).options(joinedload(EventModel.photos)).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
    # Delete all photos associated with the event from Cloudinary
    for photo in event.photos:
        try:
            public_id = "/".join(photo.url.split('/')[-2:]).split('.')[0]
            delete_image(public_id)
        except Exception as e:
            # Log the error but continue with other deletions
            print(f"Could not delete photo {photo.id} from Cloudinary: {e}")
            
    # Delete the event's cover image from Cloudinary
    if event.cover_image_url:
        try:
            public_id = "/".join(event.cover_image_url.split('/')[-2:]).split('.')[0]
            delete_image(public_id)
        except Exception as e:
            print(f"Could not delete cover image for event {event.id} from Cloudinary: {e}")

    db.delete(event)
    db.commit()
    
    return MessageResponse(message=f"Event '{event_id}' has been force-deleted.")

@router.get("/uploads/recent", response_model=RecentUploadsResponse)
async def get_recent_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a feed of recent photo uploads across all events.
    """
    query = db.query(PhotoModel).order_by(PhotoModel.uploaded_at.desc())
    total = query.count()
    
    offset = (page - 1) * page_size
    photos = query.offset(offset).limit(page_size).all()

    recent_uploads = []
    for photo in photos:
        host_email = None
        if photo.event and photo.event.host:
            host_email = photo.event.host.email
        recent_uploads.append(RecentUpload(**photo.__dict__, host_email=host_email))

    return RecentUploadsResponse(
        uploads=recent_uploads,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(photos)) < total,
    )

@router.get("/users", response_model=AdminUserListResponse)
async def list_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a list of all host accounts.
    """
    query = db.query(UserModel)
    total = query.count()
    
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()

    admin_users = []
    for user_obj in users:
        event_count = db.query(EventModel).filter(EventModel.host_id == user_obj.id).count()
        admin_users.append(AdminUserResponse(
            uid=user_obj.id,
            email=user_obj.email,
            name=user_obj.name,
            email_verified=True, # Assuming verified for existing users
            event_count=event_count,
            is_suspended=user_obj.is_suspended
        ))
    
    return AdminUserListResponse(
        users=admin_users,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(users)) < total,
    )

@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def inspect_user(
    user_id: str,
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a host profile and their events.
    """
    user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    event_count = db.query(EventModel).filter(EventModel.host_id == user_obj.id).count()
    
    return AdminUserResponse(
        uid=user_obj.id,
        email=user_obj.email,
        name=user_obj.name,
        email_verified=True,
        event_count=event_count,
        is_suspended=user_obj.is_suspended
    )

@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def update_user_status(
    user_id: str,
    is_suspended: bool = Query(..., description="Set to true to suspend, false to reactivate."),
    admin: Dict[str, Any] = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Suspend or reactivate a host account.
    """
    user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    user_obj.is_suspended = is_suspended
    db.commit()
    db.refresh(user_obj)
    
    event_count = db.query(EventModel).filter(EventModel.host_id == user_obj.id).count()
    
    return AdminUserResponse(
        uid=user_obj.id,
        email=user_obj.email,
        name=user_obj.name,
        email_verified=True,
        event_count=event_count,
        is_suspended=user_obj.is_suspended
    )

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
