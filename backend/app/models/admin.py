from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserListItem(BaseModel):
    id: str
    username: str
    role: str
    is_banned: bool
    ban_until: Optional[datetime] = None
    vip_tier: str
    chapters_read: int
    level: int
    created_at: datetime


class UpdateUserRoleRequest(BaseModel):
    role: str  # 'reader', 'uploader', 'admin'


class BanUserRequest(BaseModel):
    ban_until: Optional[datetime] = None  # None = permanent


class ReportCreate(BaseModel):
    target_type: str  # 'novel', 'chapter', 'comment', 'review', 'user'
    target_id: str
    reason: str


class ReportPublic(BaseModel):
    id: str
    reporter_id: str
    target_type: str
    target_id: str
    reason: str
    status: str
    admin_note: Optional[str] = None
    created_at: datetime


class ResolveReportRequest(BaseModel):
    status: str  # 'resolved' or 'dismissed'
    admin_note: Optional[str] = None


class FeedbackCreate(BaseModel):
    content: str


class FeedbackPublic(BaseModel):
    id: str
    user_id: Optional[str] = None
    content: str
    status: str
    admin_response: Optional[str] = None
    created_at: datetime


class RespondFeedbackRequest(BaseModel):
    admin_response: str
    status: str = "reviewed"
