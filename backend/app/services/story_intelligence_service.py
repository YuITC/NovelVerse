"""Story Intelligence service — Relationship Graph, Timeline, Q&A, Arc Summaries (M19)."""
import json
import logging
from collections.abc import Generator

from app.core.config import settings
from app.core.database import get_supabase
from app.core.qdrant import get_qdrant

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "models/text-embedding-004"
_CHAT_MODEL = "gemini-2.0-flash"
_TOP_K = 5


# ---------------------------------------------------------------------------
# Relationship graph helpers
# ---------------------------------------------------------------------------

def get_relationships(novel_id: str) -> dict:
    """Return the current relationship_graph JSONB for a novel.

    Returns {"status": "not_started"} if the column is NULL.
    """
    sb = get_supabase()
    result = (
        sb.table("novels")
        .select("relationship_graph")
        .eq("id", novel_id)
        .eq("is_deleted", False)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return {"status": "not_started"}
    graph = result.data.get("relationship_graph")
    if graph is None:
        return {"status": "not_started"}
    return graph


def set_relationships_pending(novel_id: str) -> None:
    """Mark relationship_graph as pending (computation about to start)."""
    sb = get_supabase()
    sb.table("novels").update(
        {"relationship_graph": {"status": "pending"}}
    ).eq("id", novel_id).execute()


def _mark_relationships_failed(novel_id: str) -> None:
    try:
        sb = get_supabase()
        sb.table("novels").update(
            {"relationship_graph": {"status": "failed"}}
        ).eq("id", novel_id).execute()
    except Exception:
        pass


def compute_relationships_task(novel_id: str) -> None:
    """Background task: extract character co-mentions via Gemini, build NetworkX graph.

    Never raises — safe for FastAPI BackgroundTasks.
    """
    if not settings.gemini_api_key:
        _mark_relationships_failed(novel_id)
        logger.warning("compute_relationships_task: gemini_api_key not set, marking failed")
        return

    try:
        import google.generativeai as genai
        import networkx as nx

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(_CHAT_MODEL)

        sb = get_supabase()
        chapters_result = (
            sb.table("chapters")
            .select("chapter_number, content")
            .eq("novel_id", novel_id)
            .eq("is_deleted", False)
            .order("chapter_number")
            .execute()
        )
        chapters = chapters_result.data or []

        G: nx.Graph = nx.Graph()

        for chapter in chapters:
            content = chapter.get("content") or ""
            if not content.strip():
                continue

            prompt = (
                "List pairs of characters who interact or appear together in this text. "
                "Return a JSON array only, with no explanation: [[\"Name1\",\"Name2\"],...] "
                "If no pairs found, return []. "
                f"Text:\n{content[:3000]}"
            )
            try:
                response = model.generate_content(prompt)
                raw = (response.text or "").strip()
                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                pairs = json.loads(raw)
                for pair in pairs:
                    if isinstance(pair, list) and len(pair) == 2:
                        a, b = str(pair[0]).strip(), str(pair[1]).strip()
                        if a and b and a != b:
                            if G.has_edge(a, b):
                                G[a][b]["weight"] += 1
                            else:
                                G.add_edge(a, b, weight=1)
            except Exception as exc:
                logger.debug(
                    "Skipping chapter %s pair extraction: %s",
                    chapter.get("chapter_number"),
                    exc,
                )
                continue

        nodes = [{"id": n, "name": n} for n in G.nodes()]
        edges = [
            {"source": u, "target": v, "weight": d.get("weight", 1)}
            for u, v, d in G.edges(data=True)
        ]

        sb.table("novels").update(
            {"relationship_graph": {"status": "ready", "nodes": nodes, "edges": edges}}
        ).eq("id", novel_id).execute()

    except Exception as exc:
        logger.exception("compute_relationships_task failed for novel %s: %s", novel_id, exc)
        _mark_relationships_failed(novel_id)


# ---------------------------------------------------------------------------
# Story timeline helpers
# ---------------------------------------------------------------------------

def get_timeline(novel_id: str) -> dict:
    """Return the current arc_timeline JSONB for a novel.

    Returns {"status": "not_started"} if the column is NULL.
    """
    sb = get_supabase()
    result = (
        sb.table("novels")
        .select("arc_timeline")
        .eq("id", novel_id)
        .eq("is_deleted", False)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return {"status": "not_started"}
    timeline = result.data.get("arc_timeline")
    if timeline is None:
        return {"status": "not_started"}
    return timeline


def set_timeline_pending(novel_id: str) -> None:
    """Mark arc_timeline as pending."""
    sb = get_supabase()
    sb.table("novels").update(
        {"arc_timeline": {"status": "pending"}}
    ).eq("id", novel_id).execute()


def _mark_timeline_failed(novel_id: str) -> None:
    try:
        sb = get_supabase()
        sb.table("novels").update(
            {"arc_timeline": {"status": "failed"}}
        ).eq("id", novel_id).execute()
    except Exception:
        pass


def compute_timeline_task(novel_id: str) -> None:
    """Background task: extract key plot event per chapter via Gemini.

    Never raises — safe for FastAPI BackgroundTasks.
    """
    if not settings.gemini_api_key:
        _mark_timeline_failed(novel_id)
        logger.warning("compute_timeline_task: gemini_api_key not set, marking failed")
        return

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(_CHAT_MODEL)

        sb = get_supabase()
        chapters_result = (
            sb.table("chapters")
            .select("chapter_number, content")
            .eq("novel_id", novel_id)
            .eq("is_deleted", False)
            .order("chapter_number")
            .execute()
        )
        chapters = chapters_result.data or []

        events = []
        for chapter in chapters:
            ch_num = chapter.get("chapter_number", 0)
            content = chapter.get("content") or ""
            if not content.strip():
                continue

            prompt = (
                "Tóm tắt sự kiện chính của chương này trong một câu tiếng Việt ngắn gọn. "
                "Chỉ trả lời đúng một câu, không giải thích thêm.\n"
                f"Chương {ch_num}:\n{content[:2000]}"
            )
            try:
                response = model.generate_content(prompt)
                summary = (response.text or "").strip()
                if summary:
                    events.append({"chapter_number": ch_num, "event_summary": summary})
            except Exception as exc:
                logger.debug(
                    "Skipping chapter %s timeline extraction: %s", ch_num, exc
                )
                continue

        sb.table("novels").update(
            {"arc_timeline": {"status": "ready", "events": events}}
        ).eq("id", novel_id).execute()

    except Exception as exc:
        logger.exception("compute_timeline_task failed for novel %s: %s", novel_id, exc)
        _mark_timeline_failed(novel_id)


# ---------------------------------------------------------------------------
# Full-context Q&A (RAG, no spoiler filter)
# ---------------------------------------------------------------------------

def stream_qa(novel_id: str, question: str) -> Generator[str, None, None]:
    """SSE generator for full-context Q&A.

    No chapter filter — user sees complete novel context.
    Never raises — safe for FastAPI StreamingResponse.
    """
    if not settings.gemini_api_key:
        yield "data: [ERROR] AI service not configured\n\n"
        return

    sb = get_supabase()
    context_chunks: list[str] = []

    qdrant = get_qdrant()
    if qdrant and settings.qdrant_url:
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)
            embed_result = genai.embed_content(
                model=_EMBEDDING_MODEL,
                content=question,
                task_type="RETRIEVAL_QUERY",
            )
            query_vector: list[float] = embed_result["embedding"]

            collection_name = f"novel_{novel_id}"
            # No chapter filter — full novel context (no spoiler control for VIP Max)
            search_results = qdrant.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=_TOP_K,
            )

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
            logger.warning("Q&A RAG search failed (continuing without context): %s", exc)

    context_section = ""
    if context_chunks:
        context_section = (
            "\n\n[Ngữ cảnh từ câu chuyện]\n"
            + "\n---\n".join(context_chunks)
        )

    prompt = (
        "Dựa vào ngữ cảnh sau từ câu chuyện, trả lời câu hỏi bằng tiếng Việt một cách chi tiết."
        f"{context_section}"
        f"\n\nCâu hỏi: {question}"
    )

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(_CHAT_MODEL)
        response = model.generate_content(prompt, stream=True)

        for chunk in response:
            token = chunk.text or ""
            if token:
                safe_token = token.replace("\n", "\\n")
                yield f"data: {safe_token}\n\n"

    except Exception as exc:
        logger.exception("Q&A Gemini streaming failed for novel %s: %s", novel_id, exc)
        yield "data: [ERROR] AI generation failed\n\n"
        return

    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Arc summaries (cached in Supabase Storage)
# ---------------------------------------------------------------------------

def get_arc_summary(novel_id: str, start_chapter: int, end_chapter: int) -> dict:
    """Return arc summary for the given chapter range.

    Checks Supabase Storage cache first. On cache miss: calls Gemini and caches result.
    Raises on Gemini failure (propagates as 500).
    """
    cache_path = f"{novel_id}/{start_chapter}-{end_chapter}.json"
    sb = get_supabase()

    # Check cache
    try:
        cached_bytes = sb.storage.from_("arc-summaries").download(cache_path)
        return json.loads(cached_bytes)
    except Exception:
        pass  # Cache miss — proceed to compute

    if not settings.gemini_api_key:
        raise ValueError("AI service not configured")

    # Fetch chapters in range
    chapters_result = (
        sb.table("chapters")
        .select("chapter_number, content")
        .eq("novel_id", novel_id)
        .eq("is_deleted", False)
        .gte("chapter_number", start_chapter)
        .lte("chapter_number", end_chapter)
        .order("chapter_number")
        .execute()
    )
    chapters = chapters_result.data or []

    if not chapters:
        raise ValueError(f"No chapters found in range {start_chapter}–{end_chapter}")

    # Build combined text (truncated to avoid token limits)
    combined_parts = []
    total_chars = 0
    for ch in chapters:
        part = f"=== Chương {ch['chapter_number']} ===\n{ch.get('content', '')}\n\n"
        if total_chars + len(part) > 30000:
            break
        combined_parts.append(part)
        total_chars += len(part)
    combined_text = "".join(combined_parts)

    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(_CHAT_MODEL)

    prompt = (
        f"Tóm tắt nội dung từ chương {start_chapter} đến chương {end_chapter} "
        "trong 3-5 đoạn văn tiếng Việt. "
        "Bao gồm các sự kiện chính, diễn biến của nhân vật, và những điểm nổi bật quan trọng.\n\n"
        f"{combined_text}"
    )
    response = model.generate_content(prompt)
    summary_text = (response.text or "").strip()

    result = {
        "summary": summary_text,
        "start_chapter": start_chapter,
        "end_chapter": end_chapter,
    }

    # Cache to Storage
    try:
        sb.storage.from_("arc-summaries").upload(
            path=cache_path,
            file=json.dumps(result, ensure_ascii=False).encode("utf-8"),
            file_options={"upsert": "true", "content-type": "application/json"},
        )
    except Exception as exc:
        logger.warning("Failed to cache arc summary to Storage: %s", exc)

    return result
