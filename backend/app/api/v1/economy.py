from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.deps import get_current_user
from app.models.economy import (
    WalletPublic, TransactionPublic,
    DepositCreateRequest, DepositPublic,
    ShopItemPublic, GiftRequest, GiftLogPublic,
    WithdrawalCreateRequest, WithdrawalPublic,
)
from app.services import economy_service

router = APIRouter(tags=["economy"])


@router.get("/economy/wallet", response_model=WalletPublic)
async def get_wallet(current_user: dict = Depends(get_current_user)):
    return economy_service.get_wallet(current_user["id"])


@router.get("/economy/transactions", response_model=list[TransactionPublic])
async def get_transactions(
    limit: int = Query(20, le=100),
    cursor: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    return economy_service.get_transaction_history(current_user["id"], limit=limit, cursor=cursor)


@router.post("/economy/deposit", response_model=DepositPublic, status_code=201)
async def create_deposit(body: DepositCreateRequest, current_user: dict = Depends(get_current_user)):
    return economy_service.create_deposit_request(current_user["id"], body.amount_vnd)


@router.get("/economy/deposit", response_model=list[DepositPublic])
async def my_deposits(current_user: dict = Depends(get_current_user)):
    return economy_service.get_my_deposits(current_user["id"])


@router.get("/economy/shop", response_model=list[ShopItemPublic])
async def list_shop():
    return economy_service.list_shop_items()


@router.post("/economy/shop/{item_id}/purchase")
async def purchase_item(item_id: str, current_user: dict = Depends(get_current_user)):
    return economy_service.purchase_item(item_id, current_user["id"])


@router.post("/economy/shop/{item_id}/gift")
async def gift_item(item_id: str, body: GiftRequest, current_user: dict = Depends(get_current_user)):
    return economy_service.gift_item(item_id, current_user["id"], body.receiver_id)


@router.get("/economy/gifts")
async def gift_history(current_user: dict = Depends(get_current_user)):
    return economy_service.get_gift_history(current_user["id"])


@router.post("/economy/withdrawal", response_model=WithdrawalPublic, status_code=201)
async def create_withdrawal(body: WithdrawalCreateRequest, current_user: dict = Depends(get_current_user)):
    return economy_service.create_withdrawal(
        current_user["id"],
        body.tt_amount,
        body.bank_info,
        current_user.get("role", "reader"),
    )


@router.get("/economy/withdrawal", response_model=list[WithdrawalPublic])
async def my_withdrawals(current_user: dict = Depends(get_current_user)):
    return economy_service.get_my_withdrawals(current_user["id"])
