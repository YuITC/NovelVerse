from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.user import UserPublic, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: str):
    """Get a user's public profile."""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/me", response_model=UserPublic)
async def update_me(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update the authenticated user's own profile."""
    updated = user_service.update_user(current_user["id"], data)
    return updated
