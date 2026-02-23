from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.core.constants import ALLOWED_CRAWL_DOMAINS


class CrawlSourceCreate(BaseModel):
    novel_id: str
    source_url: str

    @field_validator("source_url")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        from urllib.parse import urlparse
        domain = urlparse(v).netloc.lower().lstrip("www.")
        if domain not in ALLOWED_CRAWL_DOMAINS:
            raise ValueError(f"Domain not in whitelist. Allowed: {', '.join(ALLOWED_CRAWL_DOMAINS)}")
        return v


class CrawlSourcePublic(BaseModel):
    id: str
    novel_id: str
    source_url: str
    last_chapter: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class CrawlQueueItem(BaseModel):
    id: str
    crawl_source_id: str
    novel_id: str
    chapter_number: int
    raw_content: Optional[str] = None
    translated_content: Optional[str] = None
    translation_method: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TranslateRequest(BaseModel):
    method: str = "opencc"  # opencc | gemini

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v not in ("opencc", "gemini"):
            raise ValueError("method must be 'opencc' or 'gemini'")
        return v
