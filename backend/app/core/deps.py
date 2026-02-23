from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_supabase
from app.core.security import decode_jwt

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Extract and validate the JWT from the Authorization header.
    Returns the user row from the public.users table.
    Raises 401 if missing or invalid.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_jwt(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    supabase = get_supabase()
    result = supabase.table("users").select("*").eq("id", user_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user = result.data

    # Lazy VIP expiry check
    if user.get("vip_expires_at"):
        from datetime import datetime, timezone
        expires_at = datetime.fromisoformat(user["vip_expires_at"].replace("Z", "+00:00"))
        if expires_at < datetime.now(timezone.utc):
            supabase.table("users").update({"vip_tier": "none", "vip_expires_at": None}).eq("id", user_id).execute()
            user["vip_tier"] = "none"
            user["vip_expires_at"] = None

    # Block banned users
    if user.get("is_banned"):
        from datetime import datetime, timezone
        ban_until = user.get("ban_until")
        if ban_until is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is permanently banned")
        ban_dt = datetime.fromisoformat(ban_until.replace("Z", "+00:00"))
        if ban_dt > datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is temporarily banned")

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    """Like get_current_user but returns None instead of raising for unauthenticated requests."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(*roles: str):
    """Dependency factory: require the current user to have one of the given roles."""
    async def check_role(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return check_role
