"""Character extraction service: parse chapter content → populate characters table."""
import json
import logging

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

_EXTRACTION_MODEL = "gemini-2.0-flash"
_EXTRACTION_PROMPT = """You are a literary analysis assistant for Vietnamese web novels (translated from Chinese).
Analyze the chapter text and identify all named characters who appear or are meaningfully mentioned.

Return ONLY a valid JSON array. Each element must have exactly these fields:
- "name": string — character's name as it appears in text
- "description": string — 1-2 sentence description
- "traits": array of strings — 3 to 5 personality or physical traits

If no characters are found, return [].

Chapter text:
---
{content}
---"""


def _extract_from_gemini(content: str) -> list[dict]:
    """Call Gemini and parse structured character JSON from the response."""
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(_EXTRACTION_MODEL)
    prompt = _EXTRACTION_PROMPT.format(content=content[:8000])
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    raw = response.text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, list) else []


def extract_characters(chapter_id: str, novel_id: str, chapter_number: int) -> None:
    """Background task: extract characters from a chapter and upsert into the characters table.

    Silently skips if Gemini API key is not configured.
    Never raises — all exceptions are caught and logged (BackgroundTask safety).
    """
    if not settings.gemini_api_key:
        logger.warning("extract_characters skipped: GEMINI_API_KEY not configured")
        return

    try:
        sb = get_supabase()

        # 1. Fetch chapter content
        result = sb.table("chapters").select(
            "id, content"
        ).eq("id", chapter_id).maybe_single().execute()
        if not result.data:
            logger.warning("extract_characters: chapter %s not found", chapter_id)
            return
        content = result.data.get("content", "")
        if not content.strip():
            return

        # 2. Call Gemini for structured extraction
        characters = _extract_from_gemini(content)
        if not characters:
            logger.info("extract_characters: no characters found in chapter %s", chapter_id)
            return

        # 3. Upsert each character — preserve lowest first_chapter across chapters
        for char in characters:
            name = (char.get("name") or "").strip()
            if not name:
                continue

            existing = sb.table("characters").select(
                "id, first_chapter"
            ).eq("novel_id", novel_id).eq("name", name).maybe_single().execute()

            if existing.data:
                update_payload: dict = {
                    "description": char.get("description"),
                    "traits": char.get("traits") or [],
                }
                existing_fc = existing.data.get("first_chapter")
                if existing_fc is None or chapter_number < existing_fc:
                    update_payload["first_chapter"] = chapter_number
                sb.table("characters").update(update_payload).eq(
                    "id", existing.data["id"]
                ).execute()
            else:
                sb.table("characters").insert({
                    "novel_id": novel_id,
                    "name": name,
                    "description": char.get("description"),
                    "traits": char.get("traits") or [],
                    "first_chapter": chapter_number,
                }).execute()

        logger.info(
            "extract_characters: processed %d characters from chapter %s",
            len(characters),
            chapter_id,
        )

    except Exception as exc:
        logger.exception("extract_characters failed for chapter %s: %s", chapter_id, exc)
