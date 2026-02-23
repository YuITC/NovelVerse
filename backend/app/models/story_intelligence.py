"""Pydantic schemas for M19 Story Intelligence Dashboard."""
from pydantic import BaseModel, Field


class RelationshipNodePublic(BaseModel):
    id: str
    name: str


class RelationshipEdgePublic(BaseModel):
    source: str
    target: str
    weight: float


class RelationshipGraphResponse(BaseModel):
    status: str  # "not_started" | "pending" | "ready" | "failed"
    nodes: list[RelationshipNodePublic] = []
    edges: list[RelationshipEdgePublic] = []


class TimelineEventPublic(BaseModel):
    chapter_number: int
    event_summary: str


class TimelineResponse(BaseModel):
    status: str  # "not_started" | "pending" | "ready" | "failed"
    events: list[TimelineEventPublic] = []


class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ArcSummaryResponse(BaseModel):
    summary: str
    start_chapter: int
    end_chapter: int
