from fastapi import HTTPException
from fastapi import status as http_status

from app.core.database import get_supabase
from app.core.sanitize import sanitize_html, sanitize_plain
from app.models.comment import CommentCreate, ReviewCreate, ReviewUpdate

# ── Comments ──────────────────────────────────────────────────────

def get_comments_for_novel(novel_id: str, sort: str = "newest", limit: int = 20, offset: int = 0) -> list[dict]:
    """Get all top-level comments for a novel (novel-level + chapter-level), with replies."""
    supabase = get_supabase()
    query = supabase.table("comments").select(
        "id, novel_id, chapter_id, user_id, parent_id, content, likes, created_at, updated_at"
    ).eq("novel_id", novel_id).eq("is_deleted", False).is_("parent_id", "null")

    if sort == "most_liked":
        query = query.order("likes", desc=True)
    elif sort == "oldest":
        query = query.order("created_at", desc=False)
    else:  # newest (default)
        query = query.order("created_at", desc=True)

    result = query.range(offset, offset + limit - 1).execute()
    return result.data or []


def get_replies_for_comment(comment_id: str) -> list[dict]:
    result = get_supabase().table("comments").select(
        "id, novel_id, chapter_id, user_id, parent_id, content, likes, created_at, updated_at"
    ).eq("parent_id", comment_id).eq("is_deleted", False).order("created_at").execute()
    return result.data or []


def create_comment(novel_id: str, data: CommentCreate, user_id: str) -> dict:
    supabase = get_supabase()

    # If a parent_id is provided, verify it's a top-level comment (no nesting > 1)
    if data.parent_id:
        parent_result = supabase.table("comments").select("parent_id").eq(
            "id", data.parent_id
        ).maybe_single().execute()
        if not parent_result.data:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Parent comment not found")
        if parent_result.data.get("parent_id"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Replies can only be 1 level deep"
            )

    clean_content = sanitize_html(data.content)
    payload = {
        "novel_id": novel_id,
        "chapter_id": data.chapter_id,
        "user_id": user_id,
        "parent_id": data.parent_id,
        "content": clean_content,
    }
    result = supabase.table("comments").insert(payload).execute()
    return result.data[0]


def toggle_like(comment_id: str, user_id: str) -> dict:
    """Toggle like on a comment. Returns updated comment."""
    supabase = get_supabase()

    existing = supabase.table("comment_likes").select("user_id").eq(
        "user_id", user_id
    ).eq("comment_id", comment_id).maybe_single().execute()

    comment_result = supabase.table("comments").select("likes").eq(
        "id", comment_id
    ).maybe_single().execute()
    if not comment_result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Comment not found")

    current_likes = comment_result.data["likes"]

    if existing.data:
        supabase.table("comment_likes").delete().eq("user_id", user_id).eq("comment_id", comment_id).execute()
        new_likes = max(current_likes - 1, 0)
    else:
        supabase.table("comment_likes").insert({"user_id": user_id, "comment_id": comment_id}).execute()
        new_likes = current_likes + 1

    result = supabase.table("comments").update({"likes": new_likes}).eq("id", comment_id).execute()
    return result.data[0]


def soft_delete_comment(comment_id: str, user_id: str, user_role: str) -> None:
    supabase = get_supabase()
    comment = supabase.table("comments").select("user_id").eq(
        "id", comment_id
    ).maybe_single().execute()
    if not comment.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.data["user_id"] != user_id and user_role != "admin":
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not authorized")
    supabase.table("comments").update({"is_deleted": True}).eq("id", comment_id).execute()


# ── Reviews ───────────────────────────────────────────────────────

def get_reviews_for_novel(novel_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    result = get_supabase().table("reviews").select(
        "id, novel_id, user_id, rating, content, created_at, updated_at"
    ).eq("novel_id", novel_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return result.data or []


def create_review(novel_id: str, data: ReviewCreate, user_id: str) -> dict:
    clean_content = sanitize_plain(data.content)
    if len(clean_content.split()) < 10:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Review must be at least 10 words")
    try:
        result = get_supabase().table("reviews").insert({
            "novel_id": novel_id,
            "user_id": user_id,
            "rating": data.rating,
            "content": clean_content,
        }).execute()
        return result.data[0]
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="You have already reviewed this novel"
            )
        raise


def update_review(novel_id: str, data: ReviewUpdate, user_id: str) -> dict:
    supabase = get_supabase()
    existing = supabase.table("reviews").select("id").eq("novel_id", novel_id).eq(
        "user_id", user_id
    ).maybe_single().execute()
    if not existing.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Review not found")

    updates = data.model_dump(exclude_none=True)
    if "content" in updates:
        updates["content"] = sanitize_plain(updates["content"])
        if len(updates["content"].split()) < 10:
            raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Review must be at least 10 words")

    result = supabase.table("reviews").update(updates).eq("novel_id", novel_id).eq(
        "user_id", user_id
    ).execute()
    return result.data[0]
