from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi import status as http_status

from app.core.database import get_supabase


def _get_setting(key: str):
    sb = get_supabase()
    r = sb.table("system_settings").select("value").eq("key", key).single().execute()
    return r.data["value"] if r.data else None


def get_system_settings() -> dict:
    sb = get_supabase()
    r = sb.table("system_settings").select("key,value").execute()
    return {row["key"]: row["value"] for row in (r.data or [])}


def update_system_setting(key: str, value) -> dict:
    sb = get_supabase()
    r = sb.table("system_settings").upsert({"key": key, "value": value}).execute()
    return r.data[0] if r.data else {}


def purchase_vip(tier: str, user_id: str) -> dict:
    sb = get_supabase()
    price_lt = float(_get_setting(f"vip_{tier}_price_lt") or 0)
    duration_days = int(_get_setting("vip_duration_days") or 30)
    if price_lt <= 0:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid VIP tier")
    wallet_r = sb.table("wallets").select("linh_thach").eq("user_id", user_id).single().execute()
    if not wallet_r.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    balance = float(wallet_r.data["linh_thach"])
    if balance < price_lt:
        raise HTTPException(
            status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient Linh Thach balance. Required: {price_lt:.0f}, Available: {balance:.0f}",
        )
    new_balance = round(balance - price_lt, 2)
    sb.table("wallets").update({"linh_thach": new_balance}).eq("user_id", user_id).execute()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=duration_days)
    sub_r = sb.table("vip_subscriptions").insert({
        "user_id": user_id,
        "vip_tier": tier,
        "lt_spent": price_lt,
        "status": "active",
        "starts_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }).execute()
    sub = sub_r.data[0] if sub_r.data else {}
    sb.table("users").update({
        "vip_tier": tier,
        "vip_expires_at": expires_at.isoformat(),
    }).eq("id", user_id).execute()
    sb.table("transactions").insert({
        "user_id": user_id,
        "currency_type": "linh_thach",
        "amount": -price_lt,
        "balance_after": new_balance,
        "transaction_type": "vip_purchase",
        "status": "completed",
        "related_entity_type": "vip_subscription",
        "related_entity_id": sub.get("id"),
    }).execute()
    return sub


def get_my_subscriptions(user_id: str) -> list[dict]:
    sb = get_supabase()
    r = sb.table("vip_subscriptions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return r.data or []
