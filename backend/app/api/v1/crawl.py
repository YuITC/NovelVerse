from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.models.crawl import CrawlQueueItem, CrawlSourceCreate, CrawlSourcePublic, TranslateRequest
from app.services import crawl_service

router = APIRouter(tags=["crawl"])


# ── Crawl Sources ─────────────────────────────────────────────────

@router.get("/crawl/sources", response_model=list[CrawlSourcePublic])
async def list_sources(current_user: dict = Depends(require_role("uploader", "admin"))):
    return crawl_service.get_crawl_sources(current_user["id"])


@router.post("/crawl/sources", response_model=CrawlSourcePublic, status_code=201)
async def create_source(
    data: CrawlSourceCreate,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    return crawl_service.create_crawl_source(data, current_user["id"])


@router.delete("/crawl/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    crawl_service.delete_crawl_source(source_id, current_user["id"])


# ── Crawl Queue ────────────────────────────────────────────────────

@router.get("/crawl/queue", response_model=list[CrawlQueueItem])
async def list_queue(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    return crawl_service.get_crawl_queue(current_user["id"], limit=limit, offset=offset)


@router.post("/crawl/queue/{item_id}/translate", response_model=CrawlQueueItem)
async def translate_item(
    item_id: str,
    data: TranslateRequest,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    return crawl_service.translate_queue_item(item_id, data.method, current_user["id"])


@router.post("/crawl/queue/{item_id}/publish", status_code=201)
async def publish_item(
    item_id: str,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    return crawl_service.publish_queue_item(item_id, current_user["id"])


@router.delete("/crawl/queue/{item_id}", status_code=204)
async def skip_item(
    item_id: str,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    crawl_service.skip_queue_item(item_id, current_user["id"])
