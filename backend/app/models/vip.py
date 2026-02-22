from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class VipPurchaseRequest(BaseModel):
    tier: str

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        if v not in ("pro", "max"):
            raise ValueError("tier must be 'pro' or 'max'")
        return v


class VipSubscriptionPublic(BaseModel):
    id: str
    user_id: str
    vip_tier: str
    lt_spent: Optional[float] = None
    status: str
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
