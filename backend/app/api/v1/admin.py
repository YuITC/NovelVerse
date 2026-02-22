from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import require_role
from app.models.novel import TagCreate, TagPublic
from app.core.database import get_supabase

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
