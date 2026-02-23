from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.social import BookmarkedNovelItem, FollowStatus
from app.models.user import UserPublic, UserUpdate
from app.services import social_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/bookmarks", response_model=list[BookmarkedNovelItem])
async def my_bookmarks(current_user: dict = Depends(get_current_user)):
    """Get the authenticated user's bookmarked novels."""
    return social_service.get_my_bookmarks(current_user["id"])


@router.patch("/me", response_model=UserPublic)
async def update_me(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update the authenticated user's own profile."""
    updated = user_service.update_user(current_user["id"], data)
    return updated


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: str):
    """Get a user's public profile."""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/{user_id}/follow", response_model=FollowStatus)
async def get_follow_status(user_id: str, current_user: dict = Depends(get_current_user)):
    """Check if the authenticated user follows another user."""
    return social_service.get_follow_status(current_user["id"], user_id)


@router.post("/{user_id}/follow", response_model=FollowStatus)
async def toggle_follow(user_id: str, current_user: dict = Depends(get_current_user)):
    """Follow or unfollow a user (toggle)."""
    return social_service.toggle_follow(current_user["id"], user_id)
