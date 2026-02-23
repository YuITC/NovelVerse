"""TTS Narration service (M18) — ElevenLabs + Supabase Storage caching."""
import logging

import httpx

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

_ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
_ELEVENLABS_MODEL = "eleven_multilingual_v2"
_CHUNK_MAX_CHARS = 4500
_STORAGE_BUCKET = "chapter-narrations"


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def get_narration(chapter_id: str) -> dict | None:
    """Return the cached narration row for a chapter, or None if not found."""
    result = (
        get_supabase()
        .table("chapter_narrations")
        .select("*")
        .eq("chapter_id", chapter_id)
        .maybe_single()
        .execute()
    )
    return result.data or None


def request_narration(chapter_id: str) -> tuple[dict, bool]:
    """Ensure a narration record exists for the chapter.

    Returns (row, is_new):
    - is_new=True  → new record created (caller should enqueue background task)
    - is_new=False → existing pending/ready record returned (no duplicate needed)

    Raises ValueError if the chapter_id does not exist.
    """
    supabase = get_supabase()

    # Validate chapter exists
    chapter_check = (
        supabase.table("chapters")
        .select("id")
        .eq("id", chapter_id)
        .eq("is_deleted", False)
        .maybe_single()
        .execute()
    )
    if not chapter_check.data:
        raise ValueError(f"Chapter {chapter_id} not found")

    # Check existing record
    existing = (
        supabase.table("chapter_narrations")
        .select("*")
        .eq("chapter_id", chapter_id)
        .maybe_single()
        .execute()
    )

    if existing.data:
        if existing.data["status"] in ("pending", "ready"):
            return existing.data, False
        # status == "failed" → reset and retry
        supabase.table("chapter_narrations").update(
            {"status": "pending", "audio_url": None, "updated_at": "now()"}
        ).eq("chapter_id", chapter_id).execute()
        updated = (
            supabase.table("chapter_narrations")
            .select("*")
            .eq("chapter_id", chapter_id)
            .single()
            .execute()
        )
        return updated.data, True

    # No record yet — insert
    row = (
        supabase.table("chapter_narrations")
        .insert(
            {
                "chapter_id": chapter_id,
                "status": "pending",
                "voice_id": settings.elevenlabs_voice_id,
            }
        )
        .execute()
    )
    return row.data[0], True


def generate_narration(chapter_id: str) -> None:
    """Background task: call ElevenLabs, upload to Storage, update DB.

    Never raises — all exceptions are caught and logged; DB status set to 'failed'.
    """
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        logger.warning(
            "generate_narration skipped: ElevenLabs not configured (chapter %s)",
            chapter_id,
        )
        _mark_failed(chapter_id)
        return

    try:
        supabase = get_supabase()

        # Fetch chapter content
        chapter_row = (
            supabase.table("chapters")
            .select("content")
            .eq("id", chapter_id)
            .single()
            .execute()
        )
        content: str = chapter_row.data["content"]

        # Chunk and call ElevenLabs
        chunks = _chunk_text(content, _CHUNK_MAX_CHARS)
        audio_bytes = b""
        for chunk in chunks:
            audio_bytes += _call_elevenlabs(chunk, settings.elevenlabs_voice_id)

        # Upload to Supabase Storage
        storage_path = f"chapters/{chapter_id}.mp3"
        supabase.storage.from_(_STORAGE_BUCKET).upload(
            path=storage_path,
            file=audio_bytes,
            file_options={"content-type": "audio/mpeg", "upsert": "true"},
        )
        audio_url: str = supabase.storage.from_(_STORAGE_BUCKET).get_public_url(
            storage_path
        )

        # Mark ready
        supabase.table("chapter_narrations").update(
            {"status": "ready", "audio_url": audio_url, "updated_at": "now()"}
        ).eq("chapter_id", chapter_id).execute()

        logger.info("generate_narration: chapter %s ready (%d bytes)", chapter_id, len(audio_bytes))

    except Exception as exc:  # noqa: BLE001
        logger.exception("generate_narration failed for chapter %s: %s", chapter_id, exc)
        _mark_failed(chapter_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _chunk_text(text: str, max_chars: int = _CHUNK_MAX_CHARS) -> list[str]:
    """Split text into chunks at line boundaries, each ≤ max_chars characters."""
    lines = text.split("\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # +1 for the newline
        if current and current_len + line_len > max_chars:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks or [text]


def _call_elevenlabs(text: str, voice_id: str) -> bytes:
    """Call ElevenLabs TTS API and return raw MP3 bytes."""
    url = _ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    payload = {
        "text": text,
        "model_id": _ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.content


def _mark_failed(chapter_id: str) -> None:
    """Set narration status to failed; silently ignore errors."""
    try:
        get_supabase().table("chapter_narrations").update(
            {"status": "failed", "updated_at": "now()"}
        ).eq("chapter_id", chapter_id).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("_mark_failed: could not update DB for chapter %s: %s", chapter_id, exc)
