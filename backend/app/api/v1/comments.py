from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.models.comment import (
    CommentCreate,
    CommentPublic,
    ReviewCreate,
    ReviewPublic,
    ReviewUpdate,
)
from app.services import comment_service

router = APIRouter(tags=["comments"])


# ── Novel comments ────────────────────────────────────────────────

@router.get("/novels/{novel_id}/comments", response_model=list[CommentPublic])
async def list_comments(
    novel_id: str,
    sort: str = Query("newest", pattern="^(newest|oldest|most_liked)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return comment_service.get_comments_for_novel(novel_id, sort=sort, limit=limit, offset=offset)


@router.get("/comments/{comment_id}/replies", response_model=list[CommentPublic])
async def list_replies(comment_id: str):
    return comment_service.get_replies_for_comment(comment_id)


@router.post("/novels/{novel_id}/comments", response_model=CommentPublic, status_code=201)
async def create_comment(
    novel_id: str,
    data: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    return comment_service.create_comment(novel_id, data, current_user["id"])


@router.post("/comments/{comment_id}/like", response_model=CommentPublic)
async def toggle_like(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
):
    return comment_service.toggle_like(comment_id, current_user["id"])


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
):
    comment_service.soft_delete_comment(comment_id, current_user["id"], current_user["role"])


# ── Reviews ───────────────────────────────────────────────────────

@router.get("/novels/{novel_id}/reviews", response_model=list[ReviewPublic])
async def list_reviews(
    novel_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return comment_service.get_reviews_for_novel(novel_id, limit=limit, offset=offset)


@router.post("/novels/{novel_id}/reviews", response_model=ReviewPublic, status_code=201)
async def create_review(
    novel_id: str,
    data: ReviewCreate,
    current_user: dict = Depends(get_current_user),
):
    return comment_service.create_review(novel_id, data, current_user["id"])


@router.patch("/novels/{novel_id}/reviews/me", response_model=ReviewPublic)
async def update_review(
    novel_id: str,
    data: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
):
    return comment_service.update_review(novel_id, data, current_user["id"])
