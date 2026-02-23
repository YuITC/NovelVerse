"""Nomination service — daily novel voting + Redis-backed leaderboards."""
from datetime import date

from fastapi import HTTPException
from fastapi import status as http_status

from app.core.database import get_supabase
from app.core.redis import get_redis

# Daily nomination allowances by VIP tier
_DAILY_ALLOWANCE = {"none": 3, "pro": 5, "max": 10}

# Redis key TTLs (seconds)
_TTL = {"daily": 172_800, "weekly": 1_209_600, "monthly": 5_184_000}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _leaderboard_key(period: str) -> str:
    today = date.today()
    if period == "daily":
        return f"leaderboard:daily:{today.strftime('%Y%m%d')}"
    if period == "weekly":
        return f"leaderboard:weekly:{today.strftime('%Y-W%W')}"
    if period == "monthly":
        return f"leaderboard:monthly:{today.strftime('%Y-%m')}"
    raise ValueError(f"Invalid period: {period}")


def _daily_allowance(vip_tier: str) -> int:
    return _DAILY_ALLOWANCE.get(vip_tier, 3)


def _reset_quota_if_needed(user_id: str, supabase) -> dict:
    """Fetch user row and reset daily_nominations if nominations_reset_at < today.
    Returns the (possibly updated) user row with daily_nominations and vip_tier."""
    result = supabase.table("users").select(
        "daily_nominations, nominations_reset_at, vip_tier"
    ).eq("id", user_id).single().execute()
    user = result.data

    today = date.today()
    reset_at_raw = user.get("nominations_reset_at")
    reset_at = date.fromisoformat(reset_at_raw) if reset_at_raw else None

    if reset_at is None or reset_at < today:
        allowance = _daily_allowance(user.get("vip_tier", "none"))
        supabase.table("users").update({
            "daily_nominations": allowance,
            "nominations_reset_at": today.isoformat(),
        }).eq("id", user_id).execute()
        user["daily_nominations"] = allowance

    return user


def _zincrby(key: str, increment: float, member: str, ttl: int | None = None) -> float:
    """ZINCRBY wrapper. Sets TTL on the key if ttl is provided and key is brand new."""
    redis = get_redis()
    if redis is None:
        return 0.0
    new_score = redis.zincrby(key, increment, member)
    # Set TTL only when creating the key for the first time (score transitions from 0)
    if ttl and new_score == increment:
        redis.expire(key, ttl)
    return float(new_score)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def nominate(user_id: str, novel_id: str) -> dict:
    """Toggle nomination for today's period.

    - If not yet nominated today: insert, decrement daily quota, +1 on leaderboard.
    - If already nominated today: delete, refund daily quota, -1 on leaderboard.
    Returns: {is_nominated, nominations_remaining}
    """
    supabase = get_supabase()

    # 1. Reset daily quota if needed
    user = _reset_quota_if_needed(user_id, supabase)

    # 2. Verify novel exists
    novel_result = supabase.table("novels").select("id").eq(
        "id", novel_id
    ).eq("is_deleted", False).maybe_single().execute()
    if not novel_result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Novel not found")

    today = date.today()

    # 3. Check existing nomination for today
    existing = supabase.table("nominations").select("user_id").eq(
        "user_id", user_id
    ).eq("novel_id", novel_id).eq("period", today.isoformat()).maybe_single().execute()

    key = _leaderboard_key("daily")
    weekly_key = _leaderboard_key("weekly")
    monthly_key = _leaderboard_key("monthly")

    if existing.data:
        # De-nominate: refund vote
        supabase.table("nominations").delete().eq(
            "user_id", user_id
        ).eq("novel_id", novel_id).eq("period", today.isoformat()).execute()

        new_remaining = user["daily_nominations"] + 1
        supabase.table("users").update(
            {"daily_nominations": new_remaining}
        ).eq("id", user_id).execute()

        # Decrement Redis leaderboards (floor at 0)
        _zincrby(key, -1, novel_id)
        _zincrby(weekly_key, -1, novel_id)
        _zincrby(monthly_key, -1, novel_id)

        # Decrement denorm counter on novel
        current = supabase.table("novels").select("nomination_count").eq(
            "id", novel_id
        ).single().execute().data.get("nomination_count", 0)
        supabase.table("novels").update(
            {"nomination_count": max(current - 1, 0)}
        ).eq("id", novel_id).execute()

        return {"is_nominated": False, "nominations_remaining": new_remaining}

    else:
        # Check quota
        if user["daily_nominations"] <= 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Daily nomination limit reached",
            )

        # Insert nomination
        supabase.table("nominations").insert({
            "user_id": user_id,
            "novel_id": novel_id,
            "period": today.isoformat(),
        }).execute()

        new_remaining = user["daily_nominations"] - 1
        supabase.table("users").update(
            {"daily_nominations": new_remaining}
        ).eq("id", user_id).execute()

        # Increment Redis leaderboards
        _zincrby(key, 1, novel_id, ttl=_TTL["daily"])
        _zincrby(weekly_key, 1, novel_id, ttl=_TTL["weekly"])
        _zincrby(monthly_key, 1, novel_id, ttl=_TTL["monthly"])

        # Increment denorm counter on novel
        current = supabase.table("novels").select("nomination_count").eq(
            "id", novel_id
        ).single().execute().data.get("nomination_count", 0)
        supabase.table("novels").update(
            {"nomination_count": current + 1}
        ).eq("id", novel_id).execute()

        return {"is_nominated": True, "nominations_remaining": new_remaining}


def get_nomination_status(user_id: str, novel_id: str) -> dict:
    """Return whether the user has nominated this novel today and remaining count."""
    supabase = get_supabase()
    user = _reset_quota_if_needed(user_id, supabase)

    today = date.today()
    existing = supabase.table("nominations").select("user_id").eq(
        "user_id", user_id
    ).eq("novel_id", novel_id).eq("period", today.isoformat()).maybe_single().execute()

    return {
        "is_nominated": bool(existing.data),
        "nominations_remaining": user["daily_nominations"],
    }


def get_leaderboard(period: str, limit: int = 20) -> dict:
    """Return top-N novels by nomination score for the given period.

    Tries Redis first; falls back to DB aggregation if Redis is unavailable or empty.
    """
    if period not in ("daily", "weekly", "monthly"):
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="period must be daily, weekly, or monthly",
        )

    supabase = get_supabase()
    redis = get_redis()

    entries: list[dict] = []

    # ── Redis path ──────────────────────────────────────────────
    if redis is not None:
        key = _leaderboard_key(period)
        raw = redis.zrevrange(key, 0, limit - 1, withscores=True)  # list of (member, score)
        if raw:
            novel_ids = [item[0] for item in raw]
            scores = {item[0]: int(item[1]) for item in raw}

            novels_result = supabase.table("novels").select(
                "id, title, author, cover_url, status, total_chapters, total_views, avg_rating"
            ).in_("id", novel_ids).eq("is_deleted", False).execute()
            novels_map = {n["id"]: n for n in (novels_result.data or [])}

            for rank, novel_id in enumerate(novel_ids, start=1):
                entries.append({
                    "rank": rank,
                    "novel_id": novel_id,
                    "score": scores[novel_id],
                    "novel": novels_map.get(novel_id),
                })

            return {"period": period, "entries": entries}

    # ── DB fallback ─────────────────────────────────────────────
    today = date.today()
    if period == "daily":
        from_date = today.isoformat()
        to_date = today.isoformat()
    elif period == "weekly":
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())
        from_date = week_start.isoformat()
        to_date = today.isoformat()
    else:  # monthly
        from_date = today.replace(day=1).isoformat()
        to_date = today.isoformat()

    # PostgREST doesn't support GROUP BY directly; use RPC or aggregate in Python
    nom_result = supabase.table("nominations").select("novel_id").gte(
        "period", from_date
    ).lte("period", to_date).execute()

    if not nom_result.data:
        return {"period": period, "entries": []}

    # Aggregate counts in Python
    counts: dict[str, int] = {}
    for row in nom_result.data:
        nid = row["novel_id"]
        counts[nid] = counts.get(nid, 0) + 1

    sorted_ids = sorted(counts, key=lambda x: counts[x], reverse=True)[:limit]

    novels_result = supabase.table("novels").select(
        "id, title, author, cover_url, status, total_chapters, total_views, avg_rating"
    ).in_("id", sorted_ids).eq("is_deleted", False).execute()
    novels_map = {n["id"]: n for n in (novels_result.data or [])}

    for rank, novel_id in enumerate(sorted_ids, start=1):
        entries.append({
            "rank": rank,
            "novel_id": novel_id,
            "score": counts[novel_id],
            "novel": novels_map.get(novel_id),
        })

    return {"period": period, "entries": entries}
