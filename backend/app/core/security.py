from jose import jwt, JWTError

from app.core.config import settings


def decode_jwt(token: str) -> dict:
    """Decode and verify a Supabase-issued JWT. Returns the payload."""
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase JWTs may not have a standard aud
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
