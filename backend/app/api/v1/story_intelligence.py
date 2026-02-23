"""Story Intelligence API — Relationship Graph, Timeline, Q&A, Arc Summaries (M19)."""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
from fastapi.responses import Response, StreamingResponse

from app.core.deps import get_current_user
from app.models.story_intelligence import (
    ArcSummaryResponse,
    QARequest,
    RelationshipGraphResponse,
    TimelineResponse,
)
from app.services import story_intelligence_service as svc

router = APIRouter(prefix="/ai", tags=["story-intelligence"])


def _require_vip_max(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require VIP Max tier."""
    if current_user.get("vip_tier") != "max":
        raise HTTPException(status_code=403, detail="VIP Max required")
    return current_user


# ---------------------------------------------------------------------------
# Relationship graph
# ---------------------------------------------------------------------------

@router.get("/novels/{novel_id}/relationships", response_model=RelationshipGraphResponse)
async def get_relationships(
    novel_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(_require_vip_max),
) -> RelationshipGraphResponse | Response:
    """Return character relationship graph. Triggers background compute on first call."""
    data = svc.get_relationships(novel_id)
    if data.get("status") == "not_started":
        svc.set_relationships_pending(novel_id)
        background_tasks.add_task(svc.compute_relationships_task, novel_id)
        return Response(
            content=RelationshipGraphResponse(status="pending").model_dump_json(),
            status_code=202,
            media_type="application/json",
        )
    return RelationshipGraphResponse(**data)


# ---------------------------------------------------------------------------
# Story timeline
# ---------------------------------------------------------------------------

@router.get("/novels/{novel_id}/timeline", response_model=TimelineResponse)
async def get_timeline(
    novel_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(_require_vip_max),
) -> TimelineResponse | Response:
    """Return story timeline events. Triggers background compute on first call."""
    data = svc.get_timeline(novel_id)
    if data.get("status") == "not_started":
        svc.set_timeline_pending(novel_id)
        background_tasks.add_task(svc.compute_timeline_task, novel_id)
        return Response(
            content=TimelineResponse(status="pending").model_dump_json(),
            status_code=202,
            media_type="application/json",
        )
    return TimelineResponse(**data)


# ---------------------------------------------------------------------------
# Full-context Q&A (SSE streaming)
# ---------------------------------------------------------------------------

@router.post("/novels/{novel_id}/qa")
async def ask_question(
    novel_id: str,
    data: QARequest,
    current_user: dict = Depends(_require_vip_max),
) -> StreamingResponse:
    """Full-context RAG Q&A over the novel without spoiler filtering (VIP Max only)."""
    return StreamingResponse(
        svc.stream_qa(novel_id, data.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Arc summaries
# ---------------------------------------------------------------------------

@router.get("/novels/{novel_id}/arc-summary", response_model=ArcSummaryResponse)
async def get_arc_summary(
    novel_id: str,
    start_chapter: int = Query(..., ge=1),
    end_chapter: int = Query(..., ge=1),
    current_user: dict = Depends(_require_vip_max),
) -> ArcSummaryResponse:
    """Return AI-generated summary for a chapter range (cached in Supabase Storage)."""
    if start_chapter > end_chapter:
        raise HTTPException(
            status_code=422,
            detail="start_chapter must be less than or equal to end_chapter",
        )
    try:
        result = svc.get_arc_summary(novel_id, start_chapter, end_chapter)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("get_arc_summary failed for novel %s: %s", novel_id, exc)
        raise HTTPException(status_code=500, detail="Lỗi tạo tóm tắt. Vui lòng thử lại.") from exc
    return ArcSummaryResponse(**result)
