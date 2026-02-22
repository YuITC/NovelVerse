from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.deps import get_current_user, get_optional_user, require_role
from app.models.novel import TagCreate, TagPublic
from app.models.admin import (
    UserListItem,
    UpdateUserRoleRequest,
    BanUserRequest,
    ReportCreate,
    ReportPublic,
    ResolveReportRequest,
    FeedbackCreate,
    FeedbackPublic,
    RespondFeedbackRequest,
)
from app.core.database import get_supabase
from app.services import vip_service
from app.services import admin_service

router = APIRouter(tags=["admin"])


# ── Tags ──────────────────────────────────────────────────────────

@router.get("/admin/tags", response_model=list[TagPublic])
async def list_tags(_=Depends(require_role("admin"))):
    result = get_supabase().table("tags").select("*").order("name").execute()
    return result.data or []


@router.post("/admin/tags", response_model=TagPublic, status_code=status.HTTP_201_CREATED)
async def create_tag(data: TagCreate, _=Depends(require_role("admin"))):
    result = get_supabase().table("tags").insert(data.model_dump()).execute()
    return result.data[0]


@router.patch("/admin/tags/{tag_id}", response_model=TagPublic)
async def update_tag(tag_id: str, data: TagCreate, _=Depends(require_role("admin"))):
    result = get_supabase().table("tags").update(data.model_dump()).eq("id", tag_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tag not found")
    return result.data[0]


@router.delete("/admin/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, _=Depends(require_role("admin"))):
    get_supabase().table("tags").delete().eq("id", tag_id).execute()


# ── Crawl ─────────────────────────────────────────────────────────

@router.post("/admin/crawl/trigger")
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    novel_id: str | None = None,
    _: dict = Depends(require_role("admin")),
):
    """Trigger the crawl worker as a background task."""
    from app.workers.crawl_worker import run_crawl_job
    background_tasks.add_task(run_crawl_job, novel_id)
    return {"message": "Crawl job started", "novel_id": novel_id}


# ── VIP ───────────────────────────────────────────────────────────

@router.patch("/admin/vip/{subscription_id}/confirm")
async def confirm_vip_bank_transfer(
    subscription_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    """Admin confirms a bank transfer VIP payment."""
    return vip_service.confirm_bank_transfer(subscription_id, current_user["id"])


# ── Settings ──────────────────────────────────────────────────────

@router.get("/admin/settings")
async def get_settings_admin(current_user: dict = Depends(require_role("admin"))):
    return vip_service.get_system_settings()


@router.patch("/admin/settings/{key}")
async def update_setting(
    key: str,
    body: dict,
    current_user: dict = Depends(require_role("admin")),
):
    return vip_service.update_system_setting(key, body.get("value"))


# ── User Management ───────────────────────────────────────────────

@router.get("/admin/users", response_model=list[UserListItem])
async def list_users(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _: dict = Depends(require_role("admin")),
):
    """List all users with optional search by username."""
    return admin_service.list_users(limit=limit, offset=offset, search=search)


@router.patch("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    data: UpdateUserRoleRequest,
    _: dict = Depends(require_role("admin")),
):
    """Change a user's role."""
    return admin_service.update_user_role(user_id, data.role)


@router.post("/admin/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    data: BanUserRequest,
    _: dict = Depends(require_role("admin")),
):
    """Ban a user (permanent if ban_until is None)."""
    return admin_service.ban_user(user_id, data.ban_until)


@router.post("/admin/users/{user_id}/unban")
async def unban_user(
    user_id: str,
    _: dict = Depends(require_role("admin")),
):
    """Unban a user."""
    return admin_service.unban_user(user_id)


# ── Content Management ────────────────────────────────────────────

@router.post("/admin/novels/{novel_id}/pin")
async def pin_novel(
    novel_id: str,
    _: dict = Depends(require_role("admin")),
):
    """Pin a novel to the featured section."""
    return admin_service.pin_novel(novel_id)


@router.post("/admin/novels/{novel_id}/unpin")
async def unpin_novel(
    novel_id: str,
    _: dict = Depends(require_role("admin")),
):
    """Unpin a novel."""
    return admin_service.unpin_novel(novel_id)


@router.delete("/admin/novels/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def force_delete_novel(
    novel_id: str,
    _: dict = Depends(require_role("admin")),
):
    """Admin force soft-deletes a novel."""
    admin_service.force_delete_novel(novel_id)


@router.delete("/admin/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def force_delete_comment(
    comment_id: str,
    _: dict = Depends(require_role("admin")),
):
    """Admin force soft-deletes a comment."""
    admin_service.force_delete_comment(comment_id)


# ── Reports ───────────────────────────────────────────────────────

@router.post("/reports", response_model=ReportPublic, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a report (any authenticated user)."""
    return admin_service.create_report(data, current_user["id"])


@router.get("/admin/reports", response_model=list[ReportPublic])
async def list_reports(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _: dict = Depends(require_role("admin")),
):
    """List reports (admin only)."""
    return admin_service.list_reports(status=status, limit=limit, offset=offset)


@router.patch("/admin/reports/{report_id}", response_model=ReportPublic)
async def resolve_report(
    report_id: str,
    data: ResolveReportRequest,
    current_user: dict = Depends(require_role("admin")),
):
    """Resolve or dismiss a report (admin only)."""
    return admin_service.resolve_report(
        report_id, data.status, data.admin_note, current_user["id"]
    )


# ── Feedbacks ─────────────────────────────────────────────────────

@router.post("/feedbacks", response_model=FeedbackPublic, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    data: FeedbackCreate,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Submit feedback (anonymous allowed)."""
    user_id = current_user["id"] if current_user else None
    return admin_service.create_feedback(data.content, user_id)


@router.get("/admin/feedbacks", response_model=list[FeedbackPublic])
async def list_feedbacks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _: dict = Depends(require_role("admin")),
):
    """List feedbacks (admin only)."""
    return admin_service.list_feedbacks(status=status, limit=limit, offset=offset)


@router.patch("/admin/feedbacks/{feedback_id}", response_model=FeedbackPublic)
async def respond_feedback(
    feedback_id: str,
    data: RespondFeedbackRequest,
    _: dict = Depends(require_role("admin")),
):
    """Respond to feedback (admin only)."""
    return admin_service.respond_feedback(feedback_id, data.admin_response, data.status)
