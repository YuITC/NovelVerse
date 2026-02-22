from app.core.database import get_supabase
from app.models.user import UserUpdate


def get_user_by_id(user_id: str) -> dict | None:
    result = get_supabase().table("users").select(
        "id, username, avatar_url, bio, social_links, donate_url, role, "
        "chapters_read, level, vip_tier, created_at"
    ).eq("id", user_id).single().execute()
    return result.data


def update_user(user_id: str, data: UserUpdate) -> dict:
    updates = data.model_dump(exclude_none=True)
    result = get_supabase().table("users").update(updates).eq("id", user_id).execute()
    return result.data[0]
