from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    id: str
    user_id: str
    type: str
    payload: dict[str, Any]
    read_at: Optional[datetime] = None
    created_at: datetime


class UnreadCount(BaseModel):
    count: int
