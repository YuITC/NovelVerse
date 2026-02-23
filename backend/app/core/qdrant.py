"""Lazy Qdrant client — returns None when QDRANT_URL is not configured."""
import logging
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_qdrant():
    """Return a QdrantClient instance, or None if Qdrant is not configured."""
    if not settings.qdrant_url:
        logger.warning("QDRANT_URL not configured — vector operations will be skipped")
        return None
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    except Exception as exc:
        logger.warning("Failed to initialize Qdrant client: %s", exc)
        return None
