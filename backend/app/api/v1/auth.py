from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models.user import UserMe

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserMe)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's full profile."""
    return current_user
