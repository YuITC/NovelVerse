from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.core.deps import get_current_user, get_optional_user, require_role
from app.models.chapter import (
    ChapterCreate, ChapterUpdate, ChapterListItem, ChapterContent, ReadingProgress
)
from app.services import chapter_service

router = APIRouter(tags=["chapters"])


@router.get("/novels/{novel_id}/chapters", response_model=list[ChapterListItem])
async def list_chapters(novel_id: str):
    return chapter_service.get_chapters_for_novel(novel_id)


@router.post(
    "/novels/{novel_id}/chapters",
    response_model=ChapterListItem,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_chapter(
    novel_id: str,
    data: ChapterCreate,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    return chapter_service.create_chapter(novel_id, data, current_user["id"])


@router.get("/novels/{novel_id}/chapters/{chapter_number}", response_model=ChapterContent)
async def get_chapter(
    novel_id: str,
    chapter_number: int,
    current_user: dict | None = Depends(get_optional_user),
):
    return chapter_service.get_chapter_with_nav(novel_id, chapter_number, current_user)


@router.patch("/novels/{novel_id}/chapters/{chapter_number}", response_model=ChapterListItem)
async def update_chapter(
    novel_id: str,
    chapter_number: int,
    data: ChapterUpdate,
    current_user: dict = Depends(get_current_user),
):
    chapter = chapter_service.get_chapter(novel_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter_service.update_chapter(novel_id, chapter_number, data, current_user["id"])


@router.delete("/novels/{novel_id}/chapters/{chapter_number}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    novel_id: str,
    chapter_number: int,
    current_user: dict = Depends(get_current_user),
):
    chapter = chapter_service.get_chapter(novel_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    chapter_service.soft_delete_chapter(novel_id, chapter_number, current_user["id"])


@router.post("/novels/{novel_id}/chapters/{chapter_number}/read", response_model=ReadingProgress)
async def mark_read(
    novel_id: str,
    chapter_number: int,
    current_user: dict = Depends(get_current_user),
):
    return chapter_service.mark_chapter_read(novel_id, chapter_number, current_user["id"])


@router.get("/users/me/library", response_model=list[dict])
async def get_library(current_user: dict = Depends(get_current_user)):
    return chapter_service.get_user_library(current_user["id"])
