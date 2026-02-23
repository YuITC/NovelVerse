from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class WalletPublic(BaseModel):
    user_id: str
    linh_thach: float
    tien_thach: float
    updated_at: datetime


class TransactionPublic(BaseModel):
    id: str
    currency_type: str
    amount: float
    balance_after: float
    exchange_rate: Optional[float] = None
    transaction_type: str
    status: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    created_at: datetime


class DepositCreateRequest(BaseModel):
    amount_vnd: int

    @field_validator("amount_vnd")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v < 5000:
            raise ValueError("Minimum deposit is 5,000 VND")
        return v


class DepositPublic(BaseModel):
    id: str
    transfer_code: str
    amount_vnd: int
    lt_credited: Optional[float] = None
    status: str
    admin_note: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime


class DepositConfirmRequest(BaseModel):
    amount_vnd_received: int
    admin_note: Optional[str] = None

    @field_validator("amount_vnd_received")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v < 5000:
            raise ValueError("Amount must be at least 5,000 VND")
        return v


class AdminDepositRejectRequest(BaseModel):
    admin_note: Optional[str] = None


class ShopItemPublic(BaseModel):
    id: str
    name: str
    price_lt: float
    sort_order: int


class GiftRequest(BaseModel):
    receiver_id: str


class GiftLogPublic(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    item_id: str
    lt_spent: float
    tt_credited: float
    created_at: datetime


class WithdrawalCreateRequest(BaseModel):
    tt_amount: float
    bank_info: dict

    @field_validator("tt_amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 5000:
            raise ValueError("Minimum withdrawal is 5,000 Tien Thach")
        return v


class WithdrawalPublic(BaseModel):
    id: str
    tt_amount: float
    vnd_amount: float
    bank_info: dict
    status: str
    admin_note: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime


class AdminWithdrawalActionRequest(BaseModel):
    admin_note: Optional[str] = None
