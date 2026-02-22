from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChapterCreate(BaseModel):
    chapter_number: int
    title: Optional[str] = None
    content: str
    status: str = "draft"        # draft | scheduled | published
    publish_at: Optional[datetime] = None  # future date for VIP scheduling


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    publish_at: Optional[datetime] = None


class ChapterListItem(BaseModel):
    id: str
    novel_id: str
    chapter_number: int
    title: Optional[str] = None
    word_count: int
    status: str
    publish_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    views: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ChapterContent(ChapterListItem):
    """Full chapter with content, plus navigation."""
    content: str
    prev_chapter: Optional[int] = None   # chapter_number of previous
    next_chapter: Optional[int] = None   # chapter_number of next
    novel_title: Optional[str] = None


class ReadingProgress(BaseModel):
    user_id: str
    novel_id: str
    last_chapter_read: int
    chapters_read_list: list[int]
    updated_at: datetime
    model_config = {"from_attributes": True}
