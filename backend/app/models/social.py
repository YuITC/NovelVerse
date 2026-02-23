from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FollowStatus(BaseModel):
    is_following: bool
    follower_count: int


class BookmarkStatus(BaseModel):
    is_bookmarked: bool


class BookmarkedNovelItem(BaseModel):
    novel_id: str
    added_at: datetime
    novel: Optional[dict] = None
