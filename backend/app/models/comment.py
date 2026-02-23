from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[str] = None   # for replies (1 level only)
    chapter_id: Optional[str] = None  # if None -> novel-level

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class CommentPublic(BaseModel):
    id: str
    novel_id: str
    chapter_id: Optional[str] = None
    user_id: str
    parent_id: Optional[str] = None
    content: str
    likes: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    rating: int
    content: str

    @field_validator("rating")
    @classmethod
    def rating_in_range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("content")
    @classmethod
    def min_words(cls, v: str) -> str:
        if len(v.split()) < 10:
            raise ValueError("Review must be at least 10 words")
        return v


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    content: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_in_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewPublic(BaseModel):
    id: str
    novel_id: str
    user_id: str
    rating: int
    content: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
