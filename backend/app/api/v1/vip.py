from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.core.deps import get_current_user
from app.models.vip import VipPurchaseRequest, VipSubscriptionPublic
from app.services import vip_service

router = APIRouter(tags=["vip"])


@router.post("/vip/purchase", response_model=VipSubscriptionPublic, status_code=http_status.HTTP_201_CREATED)
async def purchase_vip(body: VipPurchaseRequest, current_user: dict = Depends(get_current_user)):
    return vip_service.purchase_vip(body.tier, current_user["id"])


@router.get("/vip/me", response_model=list[VipSubscriptionPublic])
async def my_subscriptions(current_user: dict = Depends(get_current_user)):
    return vip_service.get_my_subscriptions(current_user["id"])


@router.get("/settings")
async def public_settings():
    return vip_service.get_system_settings()
