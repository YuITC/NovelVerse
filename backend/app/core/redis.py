from functools import lru_cache

from upstash_redis import Redis

from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis() -> Redis | None:
    """Return Redis client, or None if not configured."""
    if not settings.upstash_redis_url or not settings.upstash_redis_token:
        return None
    return Redis(url=settings.upstash_redis_url, token=settings.upstash_redis_token)
