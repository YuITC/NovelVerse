"""Pydantic schemas for Chat with Characters (M17)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    novel_id: str
    character_id: str


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class ChatSessionPublic(BaseModel):
    id: str
    novel_id: str
    character_id: str
    messages: list[dict[str, Any]]
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatSessionListItem(BaseModel):
    id: str
    character_id: str
    created_at: datetime
    model_config = {"from_attributes": True}
