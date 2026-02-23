"""Pydantic schemas for AI/vector infrastructure (M16+)."""
from typing import Optional

from pydantic import BaseModel


class CharacterPublic(BaseModel):
    id: str
    novel_id: str
    name: str
    description: Optional[str] = None
    traits: list[str] = []
    first_chapter: Optional[int] = None
    model_config = {"from_attributes": True}


class EmbeddingChunkPublic(BaseModel):
    id: str
    chapter_id: str
    chunk_index: int
    content_preview: str
    vector_id: str
    model_config = {"from_attributes": True}
