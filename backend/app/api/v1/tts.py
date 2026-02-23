"""AI Narrator TTS API endpoints (M18)."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response

from app.core.deps import get_current_user
from app.models.tts import ChapterNarrationPublic
from app.services import tts_service

router = APIRouter(prefix="/tts", tags=["tts"])


def _require_vip_max(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require VIP Max tier."""
    if current_user.get("vip_tier") != "max":
        raise HTTPException(status_code=403, detail="VIP Max required")
    return current_user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/chapters/{chapter_id}", response_model=ChapterNarrationPublic)
async def get_narration(
    chapter_id: str,
    current_user: dict = Depends(get_current_user),
) -> ChapterNarrationPublic:
    """Get cached narration status and audio URL for a chapter. Auth required."""
    row = tts_service.get_narration(chapter_id)
    if not row:
        raise HTTPException(status_code=404, detail="Narration not found")
    return ChapterNarrationPublic(**row)


@router.post("/chapters/{chapter_id}")
async def request_narration(
    chapter_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(_require_vip_max),
) -> Response:
    """Request ElevenLabs narration for a chapter. VIP Max only.

    - Returns 202 (Accepted) when a new generation is queued.
    - Returns 200 (OK) when an existing pending/ready record is returned (idempotent).
    - Returns 404 if the chapter does not exist.
    """
    try:
        row, is_new = tts_service.request_narration(chapter_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if is_new:
        background_tasks.add_task(tts_service.generate_narration, chapter_id)

    return Response(
        content=ChapterNarrationPublic(**row).model_dump_json(),
        status_code=202 if is_new else 200,
        media_type="application/json",
    )
