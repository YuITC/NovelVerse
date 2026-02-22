from datetime import datetime, date
from typing import Any, Optional
from pydantic import BaseModel, HttpUrl, field_validator


class UserPublic(BaseModel):
    id: str
    username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    social_links: list[Any] = []
    donate_url: Optional[str] = None
    role: str
    chapters_read: int
    level: int
    vip_tier: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMe(UserPublic):
    """Extended profile returned only to the user themselves."""
    is_banned: bool
    ban_until: Optional[datetime] = None
    daily_nominations: int
    nominations_reset_at: Optional[date] = None
    vip_expires_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    social_links: Optional[list[str]] = None
    donate_url: Optional[str] = None
    avatar_url: Optional[str] = None

    @field_validator("bio")
    @classmethod
    def bio_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError("Bio must be 500 characters or fewer")
        return v

    @field_validator("social_links")
    @classmethod
    def max_social_links(cls, v: Optional[list]) -> Optional[list]:
        if v and len(v) > 3:
            raise ValueError("Maximum 3 social links allowed")
        return v
