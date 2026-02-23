from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TagPublic(BaseModel):
    id: str
    name: str
    slug: str

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str
    slug: str


class NovelCreate(BaseModel):
    title: str
    original_title: Optional[str] = None
    author: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: str = "ongoing"
    tag_ids: list[str] = []


class NovelUpdate(BaseModel):
    title: Optional[str] = None
    original_title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[str] = None
    tag_ids: Optional[list[str]] = None


class NovelUploader(BaseModel):
    id: str
    username: str
    avatar_url: Optional[str] = None
    model_config = {"from_attributes": True}


class NovelPublic(BaseModel):
    id: str
    title: str
    original_title: Optional[str] = None
    author: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: str
    uploader_id: str
    uploader: Optional[NovelUploader] = None
    tags: list[TagPublic] = []
    total_chapters: int
    total_views: int
    avg_rating: float
    rating_count: int
    total_comments: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class NovelListItem(BaseModel):
    """Lighter schema for list endpoints (no description)."""
    id: str
    title: str
    original_title: Optional[str] = None
    author: str
    cover_url: Optional[str] = None
    status: str
    uploader_id: str
    tags: list[TagPublic] = []
    total_chapters: int
    total_views: int
    avg_rating: float
    rating_count: int
    is_pinned: bool
    updated_at: datetime
    model_config = {"from_attributes": True}


class NovelListResponse(BaseModel):
    items: list[NovelListItem]
    next_cursor: Optional[str] = None  # base64-encoded (updated_at, id)
