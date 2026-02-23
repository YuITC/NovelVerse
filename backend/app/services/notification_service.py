"""Notification service — read, mark-read, and unread-count endpoints.

Notifications are created by DB triggers in migration 011. This service
handles only the read-side (list, count) and mark-read operations.
"""
from fastapi import HTTPException
from fastapi import status as http_status

from app.core.database import get_supabase


def get_notifications(user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """Return paginated notifications for the user, unread first."""
    supabase = get_supabase()
    result = supabase.table("notifications").select(
        "id, user_id, type, payload, read_at, created_at"
    ).eq("user_id", user_id).order(
        "read_at", desc=False, nullsfirst=True  # unread (NULL) first
    ).order(
        "created_at", desc=True
    ).range(offset, offset + limit - 1).execute()
    return result.data or []


def get_unread_count(user_id: str) -> dict:
    """Return count of unread notifications for the user."""
    supabase = get_supabase()
    result = supabase.table("notifications").select(
        "id", count="exact"
    ).eq("user_id", user_id).is_("read_at", "null").execute()
    return {"count": result.count or 0}


def mark_read(notification_id: str, user_id: str) -> dict:
    """Mark a single notification as read. Returns the updated row."""
    supabase = get_supabase()
    # Verify ownership first
    existing = supabase.table("notifications").select("id").eq(
        "id", notification_id
    ).eq("user_id", user_id).maybe_single().execute()
    if not existing.data:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    result = supabase.table("notifications").update(
        {"read_at": "now()"}
    ).eq("id", notification_id).eq("user_id", user_id).execute()
    return result.data[0]


def mark_all_read(user_id: str) -> None:
    """Mark all unread notifications as read for the user."""
    supabase = get_supabase()
    supabase.table("notifications").update(
        {"read_at": "now()"}
    ).eq("user_id", user_id).is_("read_at", "null").execute()
