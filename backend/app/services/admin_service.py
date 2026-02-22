from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status as http_status
from app.core.database import get_supabase
from app.core.sanitize import sanitize_plain


def list_users(limit: int = 50, offset: int = 0, search: Optional[str] = None) -> list[dict]:
    """List all users with optional search by username."""
    supabase = get_supabase()
    query = supabase.table("users").select(
        "id, username, role, is_banned, ban_until, vip_tier, chapters_read, level, created_at"
    )
    if search:
        query = query.ilike("username", f"%{search}%")
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return result.data or []


def update_user_role(user_id: str, role: str) -> dict:
    """Change a user's role."""
    if role not in ("reader", "uploader", "admin"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    result = get_supabase().table("users").update({"role": role}).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return result.data[0]


def ban_user(user_id: str, ban_until: Optional[datetime]) -> dict:
    """Ban a user (permanent if ban_until is None)."""
    payload = {"is_banned": True}
    if ban_until:
        payload["ban_until"] = ban_until.isoformat()
    result = get_supabase().table("users").update(payload).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return result.data[0]


def unban_user(user_id: str) -> dict:
    """Unban a user."""
    result = get_supabase().table("users").update(
        {"is_banned": False, "ban_until": None}
    ).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return result.data[0]


def pin_novel(novel_id: str) -> dict:
    """Pin a novel to the featured section."""
    result = get_supabase().table("novels").update({"is_pinned": True}).eq("id", novel_id).execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Novel not found")
    return result.data[0]


def unpin_novel(novel_id: str) -> dict:
    """Unpin a novel."""
    result = get_supabase().table("novels").update({"is_pinned": False}).eq("id", novel_id).execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Novel not found")
    return result.data[0]


def force_delete_novel(novel_id: str) -> None:
    """Admin force soft-deletes a novel."""
    result = get_supabase().table("novels").select("id").eq("id", novel_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Novel not found")
    get_supabase().table("novels").update({"is_deleted": True}).eq("id", novel_id).execute()


def force_delete_comment(comment_id: str) -> None:
    """Admin force soft-deletes a comment."""
    result = get_supabase().table("comments").select("id").eq("id", comment_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Comment not found")
    get_supabase().table("comments").update({"is_deleted": True}).eq("id", comment_id).execute()


# ── Reports ───────────────────────────────────────────────────────

def create_report(data, reporter_id: str) -> dict:
    if data.target_type not in ("novel", "chapter", "comment", "review", "user"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid target type")
    clean_reason = sanitize_plain(data.reason)
    result = get_supabase().table("reports").insert({
        "reporter_id": reporter_id,
        "target_type": data.target_type,
        "target_id": data.target_id,
        "reason": clean_reason,
    }).execute()
    return result.data[0]


def list_reports(status: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
    query = get_supabase().table("reports").select(
        "id, reporter_id, target_type, target_id, reason, status, admin_note, created_at"
    )
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return result.data or []


def resolve_report(report_id: str, status: str, admin_note: Optional[str], admin_id: str) -> dict:
    if status not in ("resolved", "dismissed"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    report = get_supabase().table("reports").select("id").eq("id", report_id).maybe_single().execute()
    if not report.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Report not found")
    payload = {"status": status, "resolved_by": admin_id}
    if admin_note:
        payload["admin_note"] = admin_note
    result = get_supabase().table("reports").update(payload).eq("id", report_id).execute()
    return result.data[0]


# ── Feedbacks ─────────────────────────────────────────────────────

def create_feedback(content: str, user_id: Optional[str]) -> dict:
    clean = sanitize_plain(content)
    if len(clean.strip()) < 5:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Feedback too short")
    payload = {"content": clean}
    if user_id:
        payload["user_id"] = user_id
    result = get_supabase().table("feedbacks").insert(payload).execute()
    return result.data[0]


def list_feedbacks(status: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
    query = get_supabase().table("feedbacks").select(
        "id, user_id, content, status, admin_response, created_at"
    )
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return result.data or []


def respond_feedback(feedback_id: str, admin_response: str, status: str) -> dict:
    if status not in ("reviewed", "closed"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    fb = get_supabase().table("feedbacks").select("id").eq("id", feedback_id).maybe_single().execute()
    if not fb.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    result = get_supabase().table("feedbacks").update({
        "admin_response": admin_response,
        "status": status,
    }).eq("id", feedback_id).execute()
    return result.data[0]
