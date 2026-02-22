import time
from fastapi import Request, HTTPException, status as http_status
from app.core.redis import get_redis

RATE_LIMIT = 100   # requests
WINDOW = 60        # seconds


async def rate_limit(request: Request) -> None:
    """Token bucket rate limiter: 100 req/min per user or IP."""
    redis = get_redis()
    if redis is None:
        return  # Redis not configured — skip rate limiting

    # Use authenticated user ID if available, otherwise fall back to IP
    user_id = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Extract sub from JWT without full verification (just for key)
        try:
            import jwt as _jwt
            token = auth_header[7:]
            unverified = _jwt.decode(token, options={"verify_signature": False})
            user_id = unverified.get("sub")
        except Exception:
            pass

    key_id = user_id or request.client.host or "unknown"
    key = f"rl:{key_id}"

    now = int(time.time())
    window_start = now - WINDOW

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, WINDOW)
    results = pipe.execute()

    count = results[2]
    if count > RATE_LIMIT:
        raise HTTPException(
            status_code=http_status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in a minute.",
            headers={"Retry-After": str(WINDOW)},
        )
