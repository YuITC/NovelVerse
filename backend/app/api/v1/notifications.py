from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.models.notification import NotificationPublic, UnreadCount
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationPublic])
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Get paginated notifications for the current user (unread first)."""
    return notification_service.get_notifications(current_user["id"], limit, offset)


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(current_user: dict = Depends(get_current_user)):
    """Return count of unread notifications for the current user."""
    return notification_service.get_unread_count(current_user["id"])


@router.patch("/read-all", status_code=204)
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the current user."""
    notification_service.mark_all_read(current_user["id"])


@router.patch("/{notification_id}/read", response_model=NotificationPublic)
async def mark_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a single notification as read."""
    return notification_service.mark_read(notification_id, current_user["id"])
