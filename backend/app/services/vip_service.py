from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status as http_status

from app.core.database import get_supabase
from app.core.config import settings


def _get_setting(key: str):
    """Fetch a system setting value."""
    result = get_supabase().table("system_settings").select("value").eq("key", key).maybe_single().execute()
    if not result.data:
        return None
    return result.data["value"]


def get_system_settings() -> dict:
    result = get_supabase().table("system_settings").select("key, value").execute()
    return {row["key"]: row["value"] for row in (result.data or [])}


def update_system_setting(key: str, value) -> dict:
    result = get_supabase().table("system_settings").upsert(
        {"key": key, "value": value}
    ).execute()
    return result.data[0]


def create_stripe_checkout(tier: str, user_id: str, success_url: str, cancel_url: str) -> str:
    """Create a Stripe Checkout Session and return the URL."""
    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        # Map tier to price ID from settings (or use direct lookup)
        price_cents = _get_setting(f"vip_{tier}_price_usd_cents")
        if price_cents is None:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid VIP tier")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"VIP {tier.title()} - NovelVerse"},
                    "unit_amount": int(price_cents),
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id, "vip_tier": tier},
        )

        # Record pending subscription
        supabase = get_supabase()
        duration_days = int(_get_setting("vip_duration_days") or 30)
        supabase.table("vip_subscriptions").insert({
            "user_id": user_id,
            "vip_tier": tier,
            "payment_method": "stripe",
            "stripe_session_id": session.id,
            "amount_paid": int(price_cents),
            "status": "pending",
        }).execute()

        return session.url

    except ImportError:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured"
        )


def create_bank_transfer_request(tier: str, amount_paid: int, user_id: str) -> dict:
    """Create a pending bank transfer subscription."""
    if tier not in ("pro", "max"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid VIP tier")

    supabase = get_supabase()
    result = supabase.table("vip_subscriptions").insert({
        "user_id": user_id,
        "vip_tier": tier,
        "payment_method": "bank_transfer",
        "amount_paid": amount_paid,
        "status": "pending",
    }).execute()
    return result.data[0]


def handle_stripe_webhook(payload: bytes, sig_header: str) -> dict:
    """Process Stripe webhook events."""
    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ImportError:
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe not configured")
    except Exception:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    supabase = get_supabase()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"].get("user_id")
        tier = session["metadata"].get("vip_tier")
        if user_id and tier:
            duration_days = int(_get_setting("vip_duration_days") or 30)
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=duration_days)
            # Activate subscription
            supabase.table("vip_subscriptions").update({
                "status": "active",
                "stripe_subscription_id": session.get("subscription"),
                "starts_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            }).eq("stripe_session_id", session["id"]).execute()
            # Update user VIP tier
            supabase.table("users").update({
                "vip_tier": tier,
                "vip_expires_at": expires_at.isoformat(),
            }).eq("id", user_id).execute()

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        sub_id = subscription["id"]
        # Find and expire the subscription
        result = supabase.table("vip_subscriptions").select("user_id").eq(
            "stripe_subscription_id", sub_id
        ).maybe_single().execute()
        if result.data:
            user_id = result.data["user_id"]
            supabase.table("vip_subscriptions").update({"status": "cancelled"}).eq(
                "stripe_subscription_id", sub_id
            ).execute()
            supabase.table("users").update({"vip_tier": "none", "vip_expires_at": None}).eq(
                "id", user_id
            ).execute()

    return {"received": True}


def confirm_bank_transfer(subscription_id: str, admin_id: str) -> dict:
    """Admin confirms a bank transfer payment."""
    supabase = get_supabase()
    sub_result = supabase.table("vip_subscriptions").select("*").eq(
        "id", subscription_id
    ).maybe_single().execute()
    if not sub_result.data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    sub = sub_result.data
    if sub["status"] != "pending":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Subscription is not pending")
    if sub["payment_method"] != "bank_transfer":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Not a bank transfer subscription")

    duration_days = int(_get_setting("vip_duration_days") or 30)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=duration_days)

    result = supabase.table("vip_subscriptions").update({
        "status": "active",
        "starts_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "confirmed_by": admin_id,
    }).eq("id", subscription_id).execute()

    # Update user VIP
    supabase.table("users").update({
        "vip_tier": sub["vip_tier"],
        "vip_expires_at": expires_at.isoformat(),
    }).eq("id", sub["user_id"]).execute()

    return result.data[0]


def get_my_subscriptions(user_id: str) -> list[dict]:
    result = get_supabase().table("vip_subscriptions").select(
        "id, vip_tier, payment_method, status, starts_at, expires_at, amount_paid, created_at"
    ).eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data or []
