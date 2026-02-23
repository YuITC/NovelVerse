import base64
import json

import bleach

from app.core.database import get_supabase
from app.models.novel import NovelCreate, NovelUpdate

ALLOWED_HTML_TAGS = ["p", "br", "strong", "em", "ul", "ol", "li"]


def _encode_cursor(updated_at: str, novel_id: str) -> str:
    data = json.dumps({"updated_at": updated_at, "id": novel_id})
    return base64.b64encode(data.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[str, str]:
    data = json.loads(base64.b64decode(cursor.encode()).decode())
    return data["updated_at"], data["id"]


def get_novels(
    q: str | None = None,
    tag_slug: str | None = None,
    status: str | None = None,
    sort: str = "updated_at",   # "updated_at" | "total_views" | "avg_rating"
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    """Returns {"items": [...], "next_cursor": str | None}"""
    supabase = get_supabase()

    # Select novels with tags via join
    select_str = (
        "id, title, original_title, author, cover_url, status, uploader_id, "
        "total_chapters, total_views, avg_rating, rating_count, is_pinned, updated_at, "
        "novel_tags(tag_id, tags(id, name, slug))"
    )

    query = supabase.table("novels").select(select_str).eq("is_deleted", False)

    if q:
        # Full text search — use ilike on title as fallback for simplicity
        # (text_search via PostgREST requires raw query)
        query = query.ilike("title", f"%{q}%")

    if status:
        query = query.eq("status", status)

    if tag_slug:
        # Filter via novel_tags -> tags join
        tag_result = supabase.table("tags").select("id").eq("slug", tag_slug).maybe_single().execute()
        if tag_result.data:
            tag_id = tag_result.data["id"]
            novel_ids_result = supabase.table("novel_tags").select("novel_id").eq("tag_id", tag_id).execute()
            ids = [r["novel_id"] for r in novel_ids_result.data]
            if not ids:
                return {"items": [], "next_cursor": None}
            query = query.in_("id", ids)

    if cursor:
        cursor_updated_at, cursor_id = _decode_cursor(cursor)
        # Cursor-based: items updated before cursor, or same time with smaller id
        query = query.or_(f"updated_at.lt.{cursor_updated_at},and(updated_at.eq.{cursor_updated_at},id.lt.{cursor_id})")

    query = query.order(sort, desc=True).order("id", desc=True).limit(limit + 1)
    result = query.execute()
    rows = result.data or []

    has_more = len(rows) > limit
    rows = rows[:limit]

    # Reshape tags from nested join
    for row in rows:
        raw_tags = row.pop("novel_tags", [])
        row["tags"] = [nt["tags"] for nt in raw_tags if nt.get("tags")]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = _encode_cursor(last["updated_at"], last["id"])

    return {"items": rows, "next_cursor": next_cursor}


def get_novel_by_id(novel_id: str) -> dict | None:
    supabase = get_supabase()
    result = supabase.table("novels").select(
        "*, novel_tags(tag_id, tags(id, name, slug)), users!uploader_id(id, username, avatar_url)"
    ).eq("id", novel_id).eq("is_deleted", False).maybe_single().execute()

    if not result.data:
        return None

    row = result.data
    raw_tags = row.pop("novel_tags", [])
    row["tags"] = [nt["tags"] for nt in raw_tags if nt.get("tags")]

    uploader_data = row.pop("users", None)
    if uploader_data:
        row["uploader"] = uploader_data

    return row


def create_novel(data: NovelCreate, uploader_id: str) -> dict:
    supabase = get_supabase()
    payload = data.model_dump(exclude={"tag_ids"})
    if payload.get("description"):
        payload["description"] = bleach.clean(payload["description"], tags=ALLOWED_HTML_TAGS, strip=True)
    payload["uploader_id"] = uploader_id

    result = supabase.table("novels").insert(payload).execute()
    novel = result.data[0]

    if data.tag_ids:
        tag_rows = [{"novel_id": novel["id"], "tag_id": tid} for tid in data.tag_ids]
        supabase.table("novel_tags").insert(tag_rows).execute()

    return get_novel_by_id(novel["id"])


def update_novel(novel_id: str, data: NovelUpdate) -> dict:
    supabase = get_supabase()
    payload = data.model_dump(exclude={"tag_ids"}, exclude_none=True)
    if payload.get("description"):
        payload["description"] = bleach.clean(payload["description"], tags=ALLOWED_HTML_TAGS, strip=True)

    if payload:
        supabase.table("novels").update(payload).eq("id", novel_id).execute()

    if data.tag_ids is not None:
        supabase.table("novel_tags").delete().eq("novel_id", novel_id).execute()
        if data.tag_ids:
            tag_rows = [{"novel_id": novel_id, "tag_id": tid} for tid in data.tag_ids]
            supabase.table("novel_tags").insert(tag_rows).execute()

    return get_novel_by_id(novel_id)


def soft_delete_novel(novel_id: str) -> None:
    get_supabase().table("novels").update({"is_deleted": True}).eq("id", novel_id).execute()


def get_featured_novels() -> list[dict]:
    supabase = get_supabase()
    result = supabase.table("novels").select(
        "id, title, original_title, author, cover_url, status, uploader_id, "
        "total_chapters, total_views, avg_rating, rating_count, is_pinned, updated_at, "
        "novel_tags(tag_id, tags(id, name, slug))"
    ).eq("is_deleted", False).eq("is_pinned", True).order("updated_at", desc=True).execute()
    rows = result.data or []
    for row in rows:
        raw_tags = row.pop("novel_tags", [])
        row["tags"] = [nt["tags"] for nt in raw_tags if nt.get("tags")]
    return rows


def get_recently_updated(limit: int = 12) -> list[dict]:
    result = get_supabase().table("novels").select(
        "id, title, original_title, author, cover_url, status, uploader_id, "
        "total_chapters, total_views, avg_rating, rating_count, is_pinned, updated_at, "
        "novel_tags(tag_id, tags(id, name, slug))"
    ).eq("is_deleted", False).order("updated_at", desc=True).limit(limit).execute()
    rows = result.data or []
    for row in rows:
        raw_tags = row.pop("novel_tags", [])
        row["tags"] = [nt["tags"] for nt in raw_tags if nt.get("tags")]
    return rows


def get_recently_completed(limit: int = 12) -> list[dict]:
    result = get_supabase().table("novels").select(
        "id, title, original_title, author, cover_url, status, uploader_id, "
        "total_chapters, total_views, avg_rating, rating_count, is_pinned, updated_at, "
        "novel_tags(tag_id, tags(id, name, slug))"
    ).eq("is_deleted", False).eq("status", "completed").order("updated_at", desc=True).limit(limit).execute()
    rows = result.data or []
    for row in rows:
        raw_tags = row.pop("novel_tags", [])
        row["tags"] = [nt["tags"] for nt in raw_tags if nt.get("tags")]
    return rows


def get_all_tags() -> list[dict]:
    result = get_supabase().table("tags").select("*").order("name").execute()
    return result.data or []
