"""Pydantic schemas for AI Narrator TTS (M18)."""
from datetime import datetime

from pydantic import BaseModel


class ChapterNarrationPublic(BaseModel):
    id: str
    chapter_id: str
    status: str  # "pending" | "ready" | "failed"
    audio_url: str | None
    voice_id: str
    created_at: datetime
    model_config = {"from_attributes": True}
