from datetime import datetime, timezone

import bleach
from fastapi import HTTPException
from fastapi import status as http_status

from app.core.database import get_supabase
from app.models.chapter import ChapterCreate, ChapterUpdate

LEVEL_THRESHOLDS = [0, 100, 500, 2000, 5000, 10_000, 30_000, 50_000, 70_000, 100_000]
ALLOWED_TAGS: list[str] = []   # plain text - strip all HTML


def _calculate_level(chapters_read: int) -> int:
    level = 0
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if chapters_read >= threshold:
            level = i
    return min(level, 9)


def get_chapters_for_novel(novel_id: str) -> list[dict]:
    result = get_supabase().table("chapters").select(
        "id, novel_id, chapter_number, title, word_count, status, "
        "publish_at, published_at, views, created_at, updated_at"
    ).eq("novel_id", novel_id).eq("is_deleted", False).order("chapter_number").execute()
    return result.data or []


def get_chapter(novel_id: str, chapter_number: int) -> dict | None:
    result = get_supabase().table("chapters").select("*").eq(
        "novel_id", novel_id
    ).eq("chapter_number", chapter_number).eq("is_deleted", False).maybe_single().execute()
    return result.data

def get_chapter_with_nav(novel_id: str, chapter_number: int, user: dict | None) -> dict:
    chapter = get_chapter(novel_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    now = datetime.now(timezone.utc)
    publish_at = chapter.get("publish_at")
    if publish_at and chapter["status"] == "published":
        pub_dt = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
        if pub_dt > now:
            if not user:
                raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                                    detail="VIP Pro hoac VIP Max de doc som")
            is_vip = user.get("vip_tier") in ("pro", "max")
            is_uploader = _is_novel_owner(novel_id, user["id"])
            is_admin = user.get("role") == "admin"
            if not (is_vip or is_uploader or is_admin):
                raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                                    detail="VIP Pro hoac VIP Max de doc som")

    supabase = get_supabase()
    all_nums_result = supabase.table("chapters").select("chapter_number").eq(
        "novel_id", novel_id
    ).eq("status", "published").eq("is_deleted", False).order("chapter_number").execute()
    all_nums = [r["chapter_number"] for r in (all_nums_result.data or [])]

    prev_ch = None
    next_ch = None
    if chapter_number in all_nums:
        idx = all_nums.index(chapter_number)
        if idx > 0:
            prev_ch = all_nums[idx - 1]
        if idx < len(all_nums) - 1:
            next_ch = all_nums[idx + 1]

    novel_result = supabase.table("novels").select("title").eq("id", novel_id).maybe_single().execute()
    novel_title = novel_result.data["title"] if novel_result.data else None

    return {**chapter, "prev_chapter": prev_ch, "next_chapter": next_ch, "novel_title": novel_title}


def _is_novel_owner(novel_id: str, user_id: str) -> bool:
    result = get_supabase().table("novels").select("id").eq("id", novel_id).eq(
        "uploader_id", user_id
    ).maybe_single().execute()
    return result.data is not None

def create_chapter(novel_id: str, data: ChapterCreate, uploader_id: str) -> dict:
    if not _is_novel_owner(novel_id, uploader_id):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not the novel owner")
    content = bleach.clean(data.content, tags=ALLOWED_TAGS, strip=True)
    word_count = len(content.split())
    payload: dict = {
        "novel_id": novel_id,
        "chapter_number": data.chapter_number,
        "title": data.title,
        "content": content,
        "word_count": word_count,
        "status": data.status,
        "publish_at": data.publish_at.isoformat() if data.publish_at else None,
    }
    if data.status == "published" and not data.publish_at:
        payload["published_at"] = datetime.now(timezone.utc).isoformat()
    result = get_supabase().table("chapters").insert(payload).execute()
    return result.data[0]


def update_chapter(novel_id: str, chapter_number: int, data: ChapterUpdate, user_id: str) -> dict:
    if not _is_novel_owner(novel_id, user_id):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not the novel owner")
    updates = data.model_dump(exclude_none=True)
    if "content" in updates:
        updates["content"] = bleach.clean(updates["content"], tags=ALLOWED_TAGS, strip=True)
        updates["word_count"] = len(updates["content"].split())
    if "publish_at" in updates and updates["publish_at"]:
        updates["publish_at"] = updates["publish_at"].isoformat()
    if updates.get("status") == "published":
        existing = get_chapter(novel_id, chapter_number)
        if existing and not existing.get("published_at"):
            updates["published_at"] = datetime.now(timezone.utc).isoformat()
    result = get_supabase().table("chapters").update(updates).eq(
        "novel_id", novel_id
    ).eq("chapter_number", chapter_number).execute()
    return result.data[0]


def soft_delete_chapter(novel_id: str, chapter_number: int, user_id: str) -> None:
    if not _is_novel_owner(novel_id, user_id):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not the novel owner")
    get_supabase().table("chapters").update({"is_deleted": True}).eq(
        "novel_id", novel_id
    ).eq("chapter_number", chapter_number).execute()

def mark_chapter_read(novel_id: str, chapter_number: int, user_id: str) -> dict:
    supabase = get_supabase()
    progress_result = supabase.table("reading_progress").select("*").eq(
        "user_id", user_id
    ).eq("novel_id", novel_id).maybe_single().execute()
    progress = progress_result.data

    if progress is None:
        new_progress = {
            "user_id": user_id,
            "novel_id": novel_id,
            "last_chapter_read": chapter_number,
            "chapters_read_list": [chapter_number],
        }
        result = supabase.table("reading_progress").insert(new_progress).execute()
        progress = result.data[0]
        chapters_delta = 1
    else:
        read_list: list[int] = progress.get("chapters_read_list") or []
        is_new = chapter_number not in read_list
        if is_new:
            read_list.append(chapter_number)
            chapters_delta = 1
        else:
            chapters_delta = 0
        update_payload: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if is_new:
            update_payload["chapters_read_list"] = read_list
        if chapter_number > progress.get("last_chapter_read", 0):
            update_payload["last_chapter_read"] = chapter_number
        result = supabase.table("reading_progress").update(update_payload).eq(
            "user_id", user_id
        ).eq("novel_id", novel_id).execute()
        progress = result.data[0]

    if chapters_delta > 0:
        chapter = get_chapter(novel_id, chapter_number)
        if chapter:
            supabase.table("chapters").update(
                {"views": chapter["views"] + 1}
            ).eq("id", chapter["id"]).execute()
            novel_result = supabase.table("novels").select("total_views").eq(
                "id", novel_id
            ).maybe_single().execute()
            if novel_result.data:
                supabase.table("novels").update(
                    {"total_views": novel_result.data["total_views"] + 1}
                ).eq("id", novel_id).execute()
        user_result = supabase.table("users").select("chapters_read").eq(
            "id", user_id
        ).maybe_single().execute()
        if user_result.data:
            new_count = user_result.data["chapters_read"] + 1
            new_level = _calculate_level(new_count)
            supabase.table("users").update(
                {"chapters_read": new_count, "level": new_level}
            ).eq("id", user_id).execute()

    return progress


def get_user_library(user_id: str) -> list[dict]:
    supabase = get_supabase()
    result = supabase.table("reading_progress").select(
        "novel_id, last_chapter_read, chapters_read_list, updated_at, "
        "novels(id, title, author, cover_url, status, total_chapters, updated_at)"
    ).eq("user_id", user_id).order("updated_at", desc=True).execute()
    items = []
    for row in (result.data or []):
        novel_data = row.pop("novels", None)
        items.append({**row, "novel": novel_data})
    return items
