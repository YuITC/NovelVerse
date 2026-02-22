from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user, get_optional_user, require_role
from app.models.novel import NovelCreate, NovelUpdate, NovelPublic, NovelListItem, NovelListResponse
from app.services import novel_service

router = APIRouter(prefix="/novels", tags=["novels"])


@router.get("", response_model=NovelListResponse)
async def list_novels(
    q: str | None = Query(None),
    tag: str | None = Query(None, description="Tag slug"),
    status: str | None = Query(None),
    sort: str = Query("updated_at", pattern="^(updated_at|total_views|avg_rating)$"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    return novel_service.get_novels(q=q, tag_slug=tag, status=status, sort=sort, cursor=cursor, limit=limit)


@router.get("/featured", response_model=list[NovelListItem])
async def get_featured():
    return novel_service.get_featured_novels()


@router.get("/recently-updated", response_model=list[NovelListItem])
async def get_recently_updated(limit: int = Query(12, ge=1, le=50)):
    return novel_service.get_recently_updated(limit=limit)


@router.get("/recently-completed", response_model=list[NovelListItem])
async def get_recently_completed(limit: int = Query(12, ge=1, le=50)):
    return novel_service.get_recently_completed(limit=limit)


@router.get("/tags", response_model=list[dict])
async def get_tags():
    return novel_service.get_all_tags()


@router.post("", response_model=NovelPublic, status_code=status.HTTP_201_CREATED)
async def create_novel(
    data: NovelCreate,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    return novel_service.create_novel(data, current_user["id"])


@router.get("/{novel_id}", response_model=NovelPublic)
async def get_novel(novel_id: str):
    novel = novel_service.get_novel_by_id(novel_id)
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    return novel


@router.patch("/{novel_id}", response_model=NovelPublic)
async def update_novel(
    novel_id: str,
    data: NovelUpdate,
    current_user: dict = Depends(get_current_user),
):
    novel = novel_service.get_novel_by_id(novel_id)
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    if novel["uploader_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")
    return novel_service.update_novel(novel_id, data)


@router.delete("/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_novel(
    novel_id: str,
    current_user: dict = Depends(get_current_user),
):
    novel = novel_service.get_novel_by_id(novel_id)
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    if novel["uploader_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")
    novel_service.soft_delete_novel(novel_id)
