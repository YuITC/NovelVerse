from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    tier: str  # 'pro' or 'max'
    # stripe_price_id will be resolved server-side from settings


class BankTransferRequest(BaseModel):
    tier: str  # 'pro' or 'max'
    amount_paid: int  # in VND


class VipSubscriptionPublic(BaseModel):
    id: str
    user_id: str
    vip_tier: str
    payment_method: str
    status: str
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class ConfirmBankTransferRequest(BaseModel):
    subscription_id: str
