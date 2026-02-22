from fastapi import APIRouter, Depends, Header, HTTPException, Request, status as http_status
from typing import Optional

from app.core.deps import get_current_user
from app.models.vip import CheckoutRequest, BankTransferRequest, VipSubscriptionPublic
from app.services import vip_service

router = APIRouter(tags=["vip"])


@router.post("/vip/checkout")
async def create_checkout(
    data: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create Stripe Checkout Session for VIP subscription."""
    if data.tier not in ("pro", "max"):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid VIP tier")
    # Build success/cancel URLs — frontend will pass these via header or we use defaults
    success_url = "http://localhost:3000/vip/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = "http://localhost:3000/vip"
    url = vip_service.create_stripe_checkout(
        tier=data.tier,
        user_id=current_user["id"],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return {"url": url}


@router.post("/vip/bank-transfer", response_model=VipSubscriptionPublic)
async def request_bank_transfer(
    data: BankTransferRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create pending bank transfer VIP subscription."""
    return vip_service.create_bank_transfer_request(
        tier=data.tier,
        amount_paid=data.amount_paid,
        user_id=current_user["id"],
    )


@router.post("/vip/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
):
    """Handle Stripe webhook events. No auth — verified by signature."""
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature")
    return vip_service.handle_stripe_webhook(payload, stripe_signature)


@router.get("/vip/me", response_model=list[VipSubscriptionPublic])
async def get_my_subscriptions(current_user: dict = Depends(get_current_user)):
    """Get current user's VIP subscription history."""
    return vip_service.get_my_subscriptions(current_user["id"])


@router.get("/settings")
async def get_settings():
    """Get public system settings (prices, etc.)."""
    return vip_service.get_system_settings()
