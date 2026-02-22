from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.novels import router as novels_router
from app.api.v1.admin import router as admin_router
from app.api.v1.chapters import router as chapters_router
from app.api.v1.comments import router as comments_router
from app.api.v1.crawl import router as crawl_router
from app.api.v1.vip import router as vip_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(novels_router)
api_router.include_router(admin_router)
api_router.include_router(chapters_router)
api_router.include_router(comments_router)
api_router.include_router(crawl_router)
api_router.include_router(vip_router)
