from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.deps import require_role
from app.models.novel import TagCreate, TagPublic
from app.core.database import get_supabase
from app.services import vip_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tags", response_model=list[TagPublic])
async def list_tags(_=Depends(require_role("admin"))):
    result = get_supabase().table("tags").select("*").order("name").execute()
    return result.data or []


@router.post("/tags", response_model=TagPublic, status_code=status.HTTP_201_CREATED)
async def create_tag(data: TagCreate, _=Depends(require_role("admin"))):
    result = get_supabase().table("tags").insert(data.model_dump()).execute()
    return result.data[0]


@router.patch("/tags/{tag_id}", response_model=TagPublic)
async def update_tag(tag_id: str, data: TagCreate, _=Depends(require_role("admin"))):
    result = get_supabase().table("tags").update(data.model_dump()).eq("id", tag_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tag not found")
    return result.data[0]


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, _=Depends(require_role("admin"))):
    get_supabase().table("tags").delete().eq("id", tag_id).execute()


@router.post("/crawl/trigger")
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    novel_id: str | None = None,
    _: dict = Depends(require_role("admin")),
):
    """Trigger the crawl worker as a background task."""
    from app.workers.crawl_worker import run_crawl_job
    background_tasks.add_task(run_crawl_job, novel_id)
    return {"message": "Crawl job started", "novel_id": novel_id}


@router.patch("/vip/{subscription_id}/confirm")
async def confirm_vip_bank_transfer(
    subscription_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    """Admin confirms a bank transfer VIP payment."""
    return vip_service.confirm_bank_transfer(subscription_id, current_user["id"])


@router.get("/settings")
async def get_settings_admin(current_user: dict = Depends(require_role("admin"))):
    return vip_service.get_system_settings()


@router.patch("/settings/{key}")
async def update_setting(
    key: str,
    body: dict,
    current_user: dict = Depends(require_role("admin")),
):
    return vip_service.update_system_setting(key, body.get("value"))
