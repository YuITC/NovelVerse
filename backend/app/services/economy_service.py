import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from fastapi import status as http_status

from app.core.database import get_supabase
from app.services.vip_service import _get_setting

# -- Wallet ------------------------------------------------------------------

def get_wallet(user_id: str) -> dict:
    sb = get_supabase()
    r = sb.table("wallets").select("*").eq("user_id", user_id).single().execute()
    if not r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return r.data


# -- Transactions -------------------------------------------------------------

def get_transaction_history(user_id: str, limit: int = 20, cursor: Optional[str] = None) -> list[dict]:
    sb = get_supabase()
    q = sb.table("transactions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit)
    if cursor:
        q = q.lt("created_at", cursor)
    return q.execute().data or []


# -- Deposits -----------------------------------------------------------------

def _generate_transfer_code() -> str:
    return f"NV-{secrets.token_hex(4).upper()}"


def create_deposit_request(user_id: str, amount_vnd: int) -> dict:
    min_vnd = int(_get_setting("min_deposit_vnd") or 5000)
    if amount_vnd < min_vnd:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum deposit is {min_vnd:,} VND",
        )
    sb = get_supabase()
    for _ in range(5):
        code = _generate_transfer_code()
        r = sb.table("deposit_requests").select("id").eq("transfer_code", code).execute()
        if not r.data:
            break
    deposit = sb.table("deposit_requests").insert({
        "user_id": user_id,
        "transfer_code": code,
        "amount_vnd": amount_vnd,
        "status": "pending",
    }).execute()
    return deposit.data[0] if deposit.data else {}


def get_my_deposits(user_id: str) -> list[dict]:
    sb = get_supabase()
    return sb.table("deposit_requests").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []

def confirm_deposit(deposit_id: str, amount_vnd_received: int, admin_id: str, admin_note: Optional[str] = None) -> dict:
    sb = get_supabase()
    r = sb.table("deposit_requests").select("*").eq("id", deposit_id).single().execute()
    if not r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Deposit request not found")
    deposit = r.data
    if deposit["status"] != "pending":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Deposit is not in pending state")
    lt_rate = float(_get_setting("lt_per_vnd") or 0.95)
    lt_to_credit = round(amount_vnd_received * lt_rate, 2)
    user_id = deposit["user_id"]
    wallet_r = sb.table("wallets").select("linh_thach").eq("user_id", user_id).single().execute()
    if not wallet_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    new_balance = round(float(wallet_r.data["linh_thach"]) + lt_to_credit, 2)
    sb.table("wallets").update({"linh_thach": new_balance}).eq("user_id", user_id).execute()
    now = datetime.now(timezone.utc)
    sb.table("deposit_requests").update({
        "status": "completed",
        "lt_credited": lt_to_credit,
        "confirmed_by": admin_id,
        "confirmed_at": now.isoformat(),
        "admin_note": admin_note,
    }).eq("id", deposit_id).execute()
    sb.table("transactions").insert({
        "user_id": user_id,
        "currency_type": "linh_thach",
        "amount": lt_to_credit,
        "balance_after": new_balance,
        "exchange_rate": lt_rate,
        "transaction_type": "deposit",
        "status": "completed",
        "related_entity_type": "deposit_request",
        "related_entity_id": deposit_id,
    }).execute()
    return {"lt_credited": lt_to_credit, "new_balance": new_balance}


def reject_deposit(deposit_id: str, admin_id: str, admin_note: Optional[str] = None) -> dict:
    sb = get_supabase()
    r = sb.table("deposit_requests").select("status").eq("id", deposit_id).single().execute()
    if not r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Deposit request not found")
    if r.data["status"] != "pending":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Deposit is not in pending state")
    sb.table("deposit_requests").update({
        "status": "rejected",
        "admin_note": admin_note,
    }).eq("id", deposit_id).execute()
    return {"status": "rejected"}


def list_deposits_admin(status_filter: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
    sb = get_supabase()
    q = sb.table("deposit_requests").select("*").order("created_at", desc=True).range(offset, offset + limit - 1)
    if status_filter:
        q = q.eq("status", status_filter)
    return q.execute().data or []

# -- Shop ---------------------------------------------------------------------

def list_shop_items() -> list[dict]:
    sb = get_supabase()
    return sb.table("shop_items").select("*").eq("is_active", True).order("sort_order").execute().data or []


def purchase_item(item_id: str, user_id: str) -> dict:
    sb = get_supabase()
    item_r = sb.table("shop_items").select("*").eq("id", item_id).eq("is_active", True).single().execute()
    if not item_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Item not found")
    item = item_r.data
    price = float(item["price_lt"])
    wallet_r = sb.table("wallets").select("linh_thach").eq("user_id", user_id).single().execute()
    if not wallet_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    balance = float(wallet_r.data["linh_thach"])
    if balance < price:
        raise HTTPException(
            status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient Linh Thach. Required: {price:.0f}, Available: {balance:.0f}",
        )
    new_balance = round(balance - price, 2)
    sb.table("wallets").update({"linh_thach": new_balance}).eq("user_id", user_id).execute()
    sb.table("transactions").insert({
        "user_id": user_id,
        "currency_type": "linh_thach",
        "amount": -price,
        "balance_after": new_balance,
        "transaction_type": "item_purchase",
        "status": "completed",
        "related_entity_type": "shop_item",
        "related_entity_id": item_id,
    }).execute()
    return {"item": item, "lt_spent": price, "new_balance": new_balance}


def gift_item(item_id: str, sender_id: str, receiver_id: str) -> dict:
    if sender_id == receiver_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Cannot gift to yourself")
    sb = get_supabase()
    receiver_r = sb.table("users").select("role").eq("id", receiver_id).single().execute()
    if not receiver_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Receiver not found")
    if receiver_r.data["role"] not in ("uploader", "admin"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Can only gift to uploaders")
    item_r = sb.table("shop_items").select("*").eq("id", item_id).eq("is_active", True).single().execute()
    if not item_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Item not found")
    item = item_r.data
    lt_price = float(item["price_lt"])
    tt_rate = float(_get_setting("tt_per_lt") or 0.95)
    tt_to_credit = round(lt_price * tt_rate, 2)
    sender_wallet_r = sb.table("wallets").select("linh_thach").eq("user_id", sender_id).single().execute()
    if not sender_wallet_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Sender wallet not found")
    sender_balance = float(sender_wallet_r.data["linh_thach"])
    if sender_balance < lt_price:
        raise HTTPException(
            status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient Linh Thach. Required: {lt_price:.0f}, Available: {sender_balance:.0f}",
        )
    new_sender_balance = round(sender_balance - lt_price, 2)
    sb.table("wallets").update({"linh_thach": new_sender_balance}).eq("user_id", sender_id).execute()
    receiver_wallet_r = sb.table("wallets").select("tien_thach").eq("user_id", receiver_id).single().execute()
    if not receiver_wallet_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Receiver wallet not found")
    new_receiver_balance = round(float(receiver_wallet_r.data["tien_thach"]) + tt_to_credit, 2)
    sb.table("wallets").update({"tien_thach": new_receiver_balance}).eq("user_id", receiver_id).execute()
    gift_r = sb.table("gift_logs").insert({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "item_id": item_id,
        "lt_spent": lt_price,
        "tt_credited": tt_to_credit,
    }).execute()
    gift_id = gift_r.data[0]["id"] if gift_r.data else None
    sb.table("transactions").insert({
        "user_id": sender_id,
        "currency_type": "linh_thach",
        "amount": -lt_price,
        "balance_after": new_sender_balance,
        "exchange_rate": tt_rate,
        "transaction_type": "gift_sent",
        "status": "completed",
        "related_entity_type": "gift_log",
        "related_entity_id": gift_id,
    }).execute()
    sb.table("transactions").insert({
        "user_id": receiver_id,
        "currency_type": "tien_thach",
        "amount": tt_to_credit,
        "balance_after": new_receiver_balance,
        "exchange_rate": tt_rate,
        "transaction_type": "gift_received",
        "status": "completed",
        "related_entity_type": "gift_log",
        "related_entity_id": gift_id,
    }).execute()
    return {"lt_spent": lt_price, "tt_credited": tt_to_credit, "item": item}


def get_gift_history(user_id: str) -> dict:
    sb = get_supabase()
    sent = sb.table("gift_logs").select("*").eq("sender_id", user_id).order("created_at", desc=True).execute().data or []
    received = sb.table("gift_logs").select("*").eq("receiver_id", user_id).order("created_at", desc=True).execute().data or []
    return {"sent": sent, "received": received}

# -- Withdrawals --------------------------------------------------------------

def create_withdrawal(user_id: str, tt_amount: float, bank_info: dict, user_role: str) -> dict:
    if user_role not in ("uploader", "admin"):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only uploaders can withdraw")
    min_tt = float(_get_setting("min_withdrawal_vnd") or 5000)
    if tt_amount < min_tt:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum withdrawal is {min_tt:.0f} Tien Thach",
        )
    sb = get_supabase()
    max_per_month = int(_get_setting("max_withdrawals_per_month") or 2)
    from datetime import date
    month_start = date.today().replace(day=1).isoformat()
    existing_r = sb.table("withdrawal_requests").select("id").eq("user_id", user_id).in_("status", ["pending", "completed"]).gte("created_at", month_start).execute()
    if len(existing_r.data or []) >= max_per_month:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {max_per_month} withdrawal requests per month",
        )
    pending_r = sb.table("withdrawal_requests").select("id").eq("user_id", user_id).eq("status", "pending").execute()
    if pending_r.data:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="You already have a pending withdrawal request")
    wallet_r = sb.table("wallets").select("tien_thach").eq("user_id", user_id).single().execute()
    if not wallet_r.data or float(wallet_r.data["tien_thach"]) < tt_amount:
        raise HTTPException(status_code=http_status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient Tien Thach balance")
    vnd_amount = round(tt_amount * float(_get_setting("vnd_per_tt") or 1), 2)
    r = sb.table("withdrawal_requests").insert({
        "user_id": user_id,
        "tt_amount": tt_amount,
        "vnd_amount": vnd_amount,
        "bank_info": bank_info,
        "status": "pending",
    }).execute()
    return r.data[0] if r.data else {}


def get_my_withdrawals(user_id: str) -> list[dict]:
    sb = get_supabase()
    return sb.table("withdrawal_requests").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []


def complete_withdrawal(withdrawal_id: str, admin_id: str, admin_note: Optional[str] = None) -> dict:
    sb = get_supabase()
    r = sb.table("withdrawal_requests").select("*").eq("id", withdrawal_id).single().execute()
    if not r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Withdrawal request not found")
    wr = r.data
    if wr["status"] != "pending":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Withdrawal is not pending")
    user_id = wr["user_id"]
    tt_amount = float(wr["tt_amount"])
    wallet_r = sb.table("wallets").select("tien_thach").eq("user_id", user_id).single().execute()
    if not wallet_r.data or float(wallet_r.data["tien_thach"]) < tt_amount:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Insufficient Tien Thach at time of completion")
    new_balance = round(float(wallet_r.data["tien_thach"]) - tt_amount, 2)
    sb.table("wallets").update({"tien_thach": new_balance}).eq("user_id", user_id).execute()
    now = datetime.now(timezone.utc)
    sb.table("withdrawal_requests").update({
        "status": "completed",
        "processed_by": admin_id,
        "processed_at": now.isoformat(),
        "admin_note": admin_note,
    }).eq("id", withdrawal_id).execute()
    sb.table("transactions").insert({
        "user_id": user_id,
        "currency_type": "tien_thach",
        "amount": -tt_amount,
        "balance_after": new_balance,
        "transaction_type": "withdrawal",
        "status": "completed",
        "related_entity_type": "withdrawal_request",
        "related_entity_id": withdrawal_id,
    }).execute()
    return {"status": "completed", "tt_deducted": tt_amount, "new_balance": new_balance}


def reject_withdrawal(withdrawal_id: str, admin_id: str, admin_note: Optional[str] = None) -> dict:
    sb = get_supabase()
    r = sb.table("withdrawal_requests").select("status").eq("id", withdrawal_id).single().execute()
    if not r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Withdrawal request not found")
    if r.data["status"] != "pending":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Withdrawal is not pending")
    sb.table("withdrawal_requests").update({
        "status": "rejected",
        "processed_by": admin_id,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "admin_note": admin_note,
    }).eq("id", withdrawal_id).execute()
    return {"status": "rejected"}


def list_withdrawals_admin(status_filter: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
    sb = get_supabase()
    q = sb.table("withdrawal_requests").select("*").order("created_at", desc=True).range(offset, offset + limit - 1)
    if status_filter:
        q = q.eq("status", status_filter)
    return q.execute().data or []
