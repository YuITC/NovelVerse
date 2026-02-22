from fastapi import HTTPException, status as http_status

from app.core.database import get_supabase
from app.models.crawl import CrawlSourceCreate


def _verify_source_owner(source_id: str, user_id: str) -> dict:
    result = get_supabase().table("crawl_sources").select("*").eq(
        "id", source_id
    ).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Source not found")
    if result.data["uploader_id"] != user_id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return result.data


def _verify_queue_owner(item_id: str, user_id: str) -> dict:
    supabase = get_supabase()
    result = supabase.table("crawl_queue").select(
        "*, crawl_sources(uploader_id)"
    ).eq("id", item_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Queue item not found")
    source = result.data.get("crawl_sources") or {}
    if source.get("uploader_id") != user_id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return result.data


def get_crawl_sources(user_id: str) -> list[dict]:
    result = get_supabase().table("crawl_sources").select(
        "id, novel_id, source_url, last_chapter, is_active, created_at"
    ).eq("uploader_id", user_id).order("created_at", desc=True).execute()
    return result.data or []


def create_crawl_source(data: CrawlSourceCreate, user_id: str) -> dict:
    # Verify the user owns this novel
    novel = get_supabase().table("novels").select("id").eq(
        "id", data.novel_id
    ).eq("uploader_id", user_id).maybe_single().execute()
    if not novel.data:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            detail="Novel not found or not owned by you")
    try:
        result = get_supabase().table("crawl_sources").insert({
            "novel_id": data.novel_id,
            "uploader_id": user_id,
            "source_url": data.source_url,
        }).execute()
        return result.data[0]
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=http_status.HTTP_409_CONFLICT,
                                detail="Source already exists for this novel")
        raise


def delete_crawl_source(source_id: str, user_id: str) -> None:
    _verify_source_owner(source_id, user_id)
    get_supabase().table("crawl_sources").delete().eq("id", source_id).execute()


def get_crawl_queue(user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    supabase = get_supabase()
    # Get all source IDs owned by this user
    sources_result = supabase.table("crawl_sources").select("id").eq(
        "uploader_id", user_id
    ).execute()
    source_ids = [s["id"] for s in (sources_result.data or [])]

    # Early return if user has no sources (avoids invalid in_([]) query)
    if not source_ids:
        return []

    result = supabase.table("crawl_queue").select(
        "id, crawl_source_id, novel_id, chapter_number, translated_content, "
        "translation_method, status, created_at, updated_at"
    ).in_("crawl_source_id", source_ids).order(
        "created_at", desc=True
    ).range(offset, offset + limit - 1).execute()
    return result.data or []


def translate_queue_item(item_id: str, method: str, user_id: str) -> dict:
    from app.services.translation_service import translate_opencc, translate_gemini
    from app.core.config import settings

    item = _verify_queue_owner(item_id, user_id)
    if item["status"] not in ("crawled", "translated"):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Item must be in 'crawled' or 'translated' status to translate"
        )

    raw = item.get("raw_content") or ""
    if not raw:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail="No raw content to translate")

    if method == "opencc":
        translated = translate_opencc(raw)
        tm = "opencc"
    elif method == "gemini":
        translated = translate_gemini(raw, settings.gemini_api_key)
        tm = "gemini"
    else:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail="method must be 'opencc' or 'gemini'")

    result = get_supabase().table("crawl_queue").update({
        "translated_content": translated,
        "translation_method": tm,
        "status": "translated",
    }).eq("id", item_id).execute()
    return result.data[0]


def publish_queue_item(item_id: str, user_id: str) -> dict:
    from app.services.chapter_service import create_chapter
    from app.models.chapter import ChapterCreate

    item = _verify_queue_owner(item_id, user_id)
    if item["status"] != "translated":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Item must be translated before publishing"
        )

    content = item.get("translated_content") or item.get("raw_content") or ""
    if not content:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail="No content to publish")

    chapter_data = ChapterCreate(
        chapter_number=item["chapter_number"],
        content=content,
        status="published",
    )
    chapter = create_chapter(item["novel_id"], chapter_data, user_id)

    # Mark queue item as published
    get_supabase().table("crawl_queue").update(
        {"status": "published"}
    ).eq("id", item_id).execute()

    return chapter


def skip_queue_item(item_id: str, user_id: str) -> None:
    _verify_queue_owner(item_id, user_id)
    get_supabase().table("crawl_queue").update(
        {"status": "skipped"}
    ).eq("id", item_id).execute()
