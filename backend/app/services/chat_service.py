"""Chat with Characters service — RAG pipeline with SSE streaming (M17)."""
import json
import logging
from collections.abc import Generator
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import settings
from app.core.database import get_supabase
from app.core.qdrant import get_qdrant

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "models/text-embedding-004"
_CHAT_MODEL = "gemini-2.0-flash"
_TOP_K = 5
_MAX_HISTORY_MESSAGES = 6  # last 3 exchanges kept in context


# ---------------------------------------------------------------------------
# Character helpers
# ---------------------------------------------------------------------------

def get_characters(novel_id: str) -> list[dict]:
    """Return all characters for a novel, sorted by first_chapter."""
    sb = get_supabase()
    result = (
        sb.table("characters")
        .select("id, novel_id, name, description, traits, first_chapter, created_at")
        .eq("novel_id", novel_id)
        .order("first_chapter", nullsfirst=True)
        .execute()
    )
    return result.data or []


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def create_session(user_id: str, novel_id: str, character_id: str) -> dict:
    """Create a new chat session. Raises 404 if novel/character not found."""
    sb = get_supabase()

    # Validate novel
    novel = (
        sb.table("novels")
        .select("id")
        .eq("id", novel_id)
        .eq("is_deleted", False)
        .maybe_single()
        .execute()
    )
    if not novel.data:
        raise HTTPException(status_code=404, detail="Novel not found")

    # Validate character belongs to this novel
    character = (
        sb.table("characters")
        .select("id")
        .eq("id", character_id)
        .eq("novel_id", novel_id)
        .maybe_single()
        .execute()
    )
    if not character.data:
        raise HTTPException(status_code=404, detail="Character not found in this novel")

    result = (
        sb.table("chat_sessions")
        .insert(
            {
                "user_id": user_id,
                "novel_id": novel_id,
                "character_id": character_id,
                "messages": [],
            }
        )
        .execute()
    )
    return result.data[0]


def get_session(session_id: str, user_id: str) -> dict | None:
    """Return session if it belongs to user, else None."""
    sb = get_supabase()
    result = (
        sb.table("chat_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return result.data


def list_sessions(user_id: str, novel_id: str) -> list[dict]:
    """Return all sessions for a user on a novel, newest first."""
    sb = get_supabase()
    result = (
        sb.table("chat_sessions")
        .select("id, character_id, created_at")
        .eq("user_id", user_id)
        .eq("novel_id", novel_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


# ---------------------------------------------------------------------------
# RAG streaming pipeline
# ---------------------------------------------------------------------------

def stream_message(
    session_id: str,
    user_id: str,
    content: str,
) -> Generator[str, None, None]:
    """RAG pipeline that streams SSE tokens.

    Yields Server-Sent Event strings ("data: <token>\\n\\n").
    Yields "data: [DONE]\\n\\n" when complete.
    Yields "data: [ERROR] <msg>\\n\\n" on failure and then stops.
    Never raises — safe for FastAPI StreamingResponse.
    """
    sb = get_supabase()

    # 1. Validate session ownership
    session = get_session(session_id, user_id)
    if not session:
        yield "data: [ERROR] Session not found\n\n"
        return

    novel_id = session["novel_id"]
    character_id = session["character_id"]

    # 2. Fetch character persona
    char_result = (
        sb.table("characters")
        .select("name, description, traits")
        .eq("id", character_id)
        .maybe_single()
        .execute()
    )
    if not char_result.data:
        yield "data: [ERROR] Character not found\n\n"
        return
    character = char_result.data
    char_name: str = character.get("name", "Nhân vật")
    char_desc: str = character.get("description") or ""
    char_traits: list[str] = character.get("traits") or []

    # 3. Get user reading progress for spoiler prevention
    progress_result = (
        sb.table("reading_progress")
        .select("last_chapter_read")
        .eq("user_id", user_id)
        .eq("novel_id", novel_id)
        .maybe_single()
        .execute()
    )
    user_progress: int = 0
    if progress_result.data:
        user_progress = progress_result.data.get("last_chapter_read") or 0

    # 4. Embed query & search Qdrant (if configured)
    context_chunks: list[str] = []
    qdrant = get_qdrant()
    if qdrant and settings.gemini_api_key and settings.qdrant_url:
        try:
            import google.generativeai as genai
            from qdrant_client.models import FieldCondition, Filter, Range

            genai.configure(api_key=settings.gemini_api_key)
            embed_result = genai.embed_content(
                model=_EMBEDDING_MODEL,
                content=content,
                task_type="RETRIEVAL_QUERY",
            )
            query_vector: list[float] = embed_result["embedding"]

            collection_name = f"novel_{novel_id}"
            search_results = qdrant.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=_TOP_K,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chapter_number",
                            range=Range(lte=user_progress),
                        )
                    ]
                ),
            )

            # 5. Fetch content_preview for each matched chunk
            vector_ids = [str(hit.id) for hit in search_results]
            if vector_ids:
                chunks_result = (
                    sb.table("novel_embeddings")
                    .select("content_preview")
                    .in_("vector_id", vector_ids)
                    .execute()
                )
                context_chunks = [
                    row["content_preview"]
                    for row in (chunks_result.data or [])
                    if row.get("content_preview")
                ]
        except Exception as exc:
            logger.warning("RAG search failed (continuing without context): %s", exc)

    # 6. Build Gemini prompt
    traits_str = ", ".join(char_traits) if char_traits else "không rõ"
    system_prompt = (
        f"Bạn là {char_name}. {char_desc} "
        f"Tính cách: {traits_str}. "
        f"Hãy trả lời bằng tiếng Việt và giữ nguyên vai trò của nhân vật. "
        f"Đừng phá vỡ nhân vật."
    )

    context_section = ""
    if context_chunks:
        context_section = (
            "\n\n[Ngữ cảnh từ câu chuyện]\n"
            + "\n---\n".join(context_chunks)
        )

    # Build conversation history (last N messages)
    history: list[dict] = session.get("messages") or []
    history_tail = history[-_MAX_HISTORY_MESSAGES:]
    history_text = ""
    for msg in history_tail:
        role_label = "Người dùng" if msg["role"] == "user" else char_name
        history_text += f"\n{role_label}: {msg['content']}"

    full_prompt = (
        f"{system_prompt}"
        f"{context_section}"
        f"{history_text}"
        f"\nNgười dùng: {content}"
        f"\n{char_name}:"
    )

    # 7. Stream Gemini response
    if not settings.gemini_api_key:
        yield "data: [ERROR] AI service not configured\n\n"
        return

    full_response = ""
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(_CHAT_MODEL)
        response = model.generate_content(full_prompt, stream=True)

        for chunk in response:
            token = chunk.text or ""
            if token:
                full_response += token
                # Escape newlines in SSE data field
                safe_token = token.replace("\n", "\\n")
                yield f"data: {safe_token}\n\n"

    except Exception as exc:
        logger.exception("Gemini streaming failed for session %s: %s", session_id, exc)
        yield "data: [ERROR] AI generation failed\n\n"
        return

    # 8. Persist both messages to chat_sessions.messages
    now_iso = datetime.now(timezone.utc).isoformat()
    new_messages = list(history) + [
        {"role": "user", "content": content, "created_at": now_iso},
        {"role": "assistant", "content": full_response, "created_at": now_iso},
    ]
    try:
        sb.table("chat_sessions").update(
            {"messages": new_messages}
        ).eq("id", session_id).execute()
    except Exception as exc:
        logger.warning("Failed to persist chat messages for session %s: %s", session_id, exc)

    yield "data: [DONE]\n\n"
