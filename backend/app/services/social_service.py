from fastapi import HTTPException
from fastapi import status as http_status

from app.core.database import get_supabase

# -- Follows ------------------------------------------------------------------

def _get_follower_count(sb, followee_id: str) -> int:
    r = sb.table("follows").select("follower_id", count="exact").eq("followee_id", followee_id).execute()
    return r.count or 0


def toggle_follow(follower_id: str, followee_id: str) -> dict:
    if follower_id == followee_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")
    sb = get_supabase()
    target_r = sb.table("users").select("role").eq("id", followee_id).maybe_single().execute()
    if not target_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    if target_r.data["role"] not in ("uploader", "admin"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Can only follow uploaders")
    existing_r = sb.table("follows").select("follower_id").eq("follower_id", follower_id).eq("followee_id", followee_id).maybe_single().execute()
    if existing_r.data:
        sb.table("follows").delete().eq("follower_id", follower_id).eq("followee_id", followee_id).execute()
        is_following = False
    else:
        sb.table("follows").insert({"follower_id": follower_id, "followee_id": followee_id}).execute()
        is_following = True
    count = _get_follower_count(sb, followee_id)
    sb.table("users").update({"follower_count": count}).eq("id", followee_id).execute()
    return {"is_following": is_following, "follower_count": count}


def get_follow_status(follower_id: str, followee_id: str) -> dict:
    sb = get_supabase()
    existing_r = sb.table("follows").select("follower_id").eq("follower_id", follower_id).eq("followee_id", followee_id).maybe_single().execute()
    count = _get_follower_count(sb, followee_id)
    return {"is_following": bool(existing_r.data), "follower_count": count}


# -- Bookmarks ----------------------------------------------------------------

def toggle_bookmark(user_id: str, novel_id: str) -> dict:
    sb = get_supabase()
    novel_r = sb.table("novels").select("id").eq("id", novel_id).eq("is_deleted", False).maybe_single().execute()
    if not novel_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Novel not found")
    existing_r = sb.table("bookmarks").select("user_id").eq("user_id", user_id).eq("novel_id", novel_id).maybe_single().execute()
    if existing_r.data:
        sb.table("bookmarks").delete().eq("user_id", user_id).eq("novel_id", novel_id).execute()
        return {"is_bookmarked": False}
    else:
        sb.table("bookmarks").insert({"user_id": user_id, "novel_id": novel_id}).execute()
        return {"is_bookmarked": True}


def get_bookmark_status(user_id: str, novel_id: str) -> dict:
    sb = get_supabase()
    existing_r = sb.table("bookmarks").select("user_id").eq("user_id", user_id).eq("novel_id", novel_id).maybe_single().execute()
    return {"is_bookmarked": bool(existing_r.data)}


def get_my_bookmarks(user_id: str) -> list[dict]:
    sb = get_supabase()
    r = sb.table("bookmarks").select(
        "novel_id, added_at, "
        "novels(id, title, author, cover_url, status, total_chapters, updated_at)"
    ).eq("user_id", user_id).order("added_at", desc=True).execute()
    items = []
    for row in r.data or []:
        novel_data = row.pop("novels", None)
        items.append({**row, "novel": novel_data})
    return items
