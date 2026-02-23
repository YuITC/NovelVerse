from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi import status as http_status

from app.core.deps import get_current_user, get_optional_user, require_role
from app.models.chapter import (
    ChapterContent,
    ChapterCreate,
    ChapterListItem,
    ChapterUpdate,
    ReadingProgress,
)
from app.services import chapter_service, character_service, embedding_service

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
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("uploader", "admin")),
):
    chapter = chapter_service.create_chapter(novel_id, data, current_user["id"])
    if data.status == "published":
        background_tasks.add_task(
            embedding_service.embed_chapter,
            chapter_id=chapter["id"],
            novel_id=novel_id,
        )
        background_tasks.add_task(
            character_service.extract_characters,
            chapter_id=chapter["id"],
            novel_id=novel_id,
            chapter_number=chapter["chapter_number"],
        )
    return chapter


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
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    chapter = chapter_service.get_chapter(novel_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    updated = chapter_service.update_chapter(novel_id, chapter_number, data, current_user["id"])
    # Only trigger on status transition to published (avoids re-embedding on minor edits)
    if data.status == "published" and chapter.get("status") != "published":
        background_tasks.add_task(
            embedding_service.embed_chapter,
            chapter_id=updated["id"],
            novel_id=novel_id,
        )
        background_tasks.add_task(
            character_service.extract_characters,
            chapter_id=updated["id"],
            novel_id=novel_id,
            chapter_number=updated["chapter_number"],
        )
    return updated


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
