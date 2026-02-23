"""Embedding pipeline: chunk chapter → embed via Gemini → upsert into Qdrant."""
import logging
import uuid

from app.core.config import settings
from app.core.database import get_supabase
from app.core.qdrant import get_qdrant

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "models/text-embedding-004"
_VECTOR_DIMENSION = 768
_MAX_CHUNK_CHARS = 1500
_CONTENT_PREVIEW_CHARS = 200


def _chunk_content(text: str) -> list[str]:
    """Split text into paragraph-based chunks of at most _MAX_CHUNK_CHARS characters.

    Splits on double newlines first. If a paragraph exceeds _MAX_CHUNK_CHARS,
    it is split further on single newlines. This preserves dialogue structure
    better than hard character-count slicing.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) + 2 > _MAX_CHUNK_CHARS:
            chunks.append(current.strip())
            current = para
        elif len(para) > _MAX_CHUNK_CHARS:
            if current:
                chunks.append(current.strip())
                current = ""
            for line in para.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if len(current) + len(line) + 1 > _MAX_CHUNK_CHARS:
                    if current:
                        chunks.append(current.strip())
                    current = line
                else:
                    current = (current + "\n" + line).strip() if current else line
        else:
            current = (current + "\n\n" + para).strip() if current else para

    if current:
        chunks.append(current.strip())
    return [c for c in chunks if c]


def _ensure_collection(qdrant_client, collection_name: str) -> None:
    """Create the Qdrant collection for a novel if it does not exist yet."""
    from qdrant_client.models import Distance, VectorParams

    existing = {c.name for c in qdrant_client.get_collections().collections}
    if collection_name not in existing:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=_VECTOR_DIMENSION, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection: %s", collection_name)


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using Gemini text-embedding-004.

    Returns a list of 768-dimensional float vectors.
    """
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    vectors = []
    for text in texts:
        result = genai.embed_content(
            model=_EMBEDDING_MODEL,
            content=text,
            task_type="RETRIEVAL_DOCUMENT",
        )
        vectors.append(result["embedding"])
    return vectors


def embed_chapter(chapter_id: str, novel_id: str) -> None:
    """Background task: chunk chapter content, embed via Gemini, upsert into Qdrant + DB.

    Silently skips if Gemini API key or Qdrant URL is not configured.
    Never raises — all exceptions are caught and logged (BackgroundTask safety).
    """
    if not settings.gemini_api_key:
        logger.warning("embed_chapter skipped: GEMINI_API_KEY not configured")
        return
    if not settings.qdrant_url:
        logger.warning("embed_chapter skipped: QDRANT_URL not configured")
        return

    qdrant = get_qdrant()
    if qdrant is None:
        logger.warning("embed_chapter skipped: Qdrant client unavailable")
        return

    try:
        sb = get_supabase()

        # 1. Fetch chapter content
        result = sb.table("chapters").select(
            "id, novel_id, chapter_number, content"
        ).eq("id", chapter_id).maybe_single().execute()
        if not result.data:
            logger.warning("embed_chapter: chapter %s not found", chapter_id)
            return
        chapter = result.data
        content = chapter.get("content", "")
        if not content.strip():
            logger.warning("embed_chapter: chapter %s has empty content", chapter_id)
            return

        # 2. Chunk
        chunks = _chunk_content(content)
        if not chunks:
            return

        # 3. Embed via Gemini
        vectors = _embed_texts(chunks)

        # 4. Ensure Qdrant collection exists
        collection_name = f"novel_{novel_id}"
        _ensure_collection(qdrant, collection_name)

        # 5. Upsert vectors into Qdrant
        from qdrant_client.models import PointStruct

        points = []
        point_ids = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "novel_id": novel_id,
                        "chapter_id": chapter_id,
                        "chapter_number": chapter["chapter_number"],
                        "chunk_index": i,
                    },
                )
            )
        qdrant.upsert(collection_name=collection_name, points=points)

        # 6. Upsert chunk records into novel_embeddings
        records = [
            {
                "chapter_id": chapter_id,
                "chunk_index": i,
                "content_preview": chunk[:_CONTENT_PREVIEW_CHARS],
                "vector_id": point_ids[i],
            }
            for i, chunk in enumerate(chunks)
        ]
        sb.table("novel_embeddings").upsert(
            records,
            on_conflict="chapter_id,chunk_index",
        ).execute()

        logger.info(
            "embed_chapter: chapter %s → %d chunks → collection %s",
            chapter_id,
            len(chunks),
            collection_name,
        )

    except Exception as exc:
        logger.exception("embed_chapter failed for chapter %s: %s", chapter_id, exc)
