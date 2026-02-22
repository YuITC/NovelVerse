"""Tests for novels API endpoints."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def make_token(user_id: str = "uploader-uuid", role: str = "uploader") -> str:
    from jose import jwt
    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")

MOCK_NOVEL_LIST_ITEM = {
    "id": "novel-uuid-1", "title": "Test Novel Title", "original_title": None,
    "author": "Test Author", "cover_url": None, "status": "completed",
    "uploader_id": "uploader-uuid",
    "tags": [{"id": "tag-uuid-1", "name": "Tu tien", "slug": "tu-tien"}],
    "total_chapters": 1600, "total_views": 500000, "avg_rating": 4.5,
    "rating_count": 200, "is_pinned": False, "updated_at": "2026-01-15T10:00:00+00:00",
}
MOCK_NOVEL_FULL = {
    **MOCK_NOVEL_LIST_ITEM, "description": "<p>A great novel</p>", "total_comments": 50,
    "uploader": {"id": "uploader-uuid", "username": "uploader_user", "avatar_url": None},
    "created_at": "2026-01-01T00:00:00+00:00",
}
MOCK_USER_READER = {
    "id": "reader-uuid", "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 0, "level": 0, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}
MOCK_USER_UPLOADER = {**MOCK_USER_READER, "id": "uploader-uuid", "username": "uploader_user", "role": "uploader"}

def _make_user_supabase_mock(user):
    r = MagicMock(); r.data = user; c = MagicMock()
    c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = r
    return c

class TestListNovels:
    def test_list_returns_200_with_items_and_cursor(self):
        with patch("app.services.novel_service.get_novels", return_value={"items": [MOCK_NOVEL_LIST_ITEM], "next_cursor": None}):
            r = client.get("/api/v1/novels")
        assert r.status_code == 200
        assert "items" in r.json() and "next_cursor" in r.json()
        assert len(r.json()["items"]) == 1

    def test_list_with_cursor_pagination(self):
        with patch("app.services.novel_service.get_novels", return_value={"items": [MOCK_NOVEL_LIST_ITEM], "next_cursor": "dGVzdA=="}):
            r = client.get("/api/v1/novels?limit=1")
        assert r.status_code == 200 and r.json()["next_cursor"] == "dGVzdA=="

    def test_list_with_filters_passes_params(self):
        with patch("app.services.novel_service.get_novels", return_value={"items": [], "next_cursor": None}) as m:
            client.get("/api/v1/novels?q=test&status=completed&tag=tu-tien&sort=total_views")
        m.assert_called_once_with(q="test", tag_slug="tu-tien", status="completed", sort="total_views", cursor=None, limit=20)

    def test_list_invalid_sort_returns_422(self):
        assert client.get("/api/v1/novels?sort=invalid_field").status_code == 422

class TestFeaturedNovels:
    def test_featured_returns_200(self):
        with patch("app.services.novel_service.get_featured_novels", return_value=[MOCK_NOVEL_LIST_ITEM]):
            r = client.get("/api/v1/novels/featured")
        assert r.status_code == 200 and r.json()[0]["id"] == "novel-uuid-1"

    def test_featured_returns_empty_list(self):
        with patch("app.services.novel_service.get_featured_novels", return_value=[]):
            r = client.get("/api/v1/novels/featured")
        assert r.status_code == 200 and r.json() == []

class TestRecentlyUpdated:
    def test_recently_updated_returns_200(self):
        with patch("app.services.novel_service.get_recently_updated", return_value=[MOCK_NOVEL_LIST_ITEM]):
            r = client.get("/api/v1/novels/recently-updated")
        assert r.status_code == 200 and len(r.json()) == 1

    def test_recently_updated_custom_limit(self):
        with patch("app.services.novel_service.get_recently_updated", return_value=[]) as m:
            client.get("/api/v1/novels/recently-updated?limit=5")
        m.assert_called_once_with(limit=5)

class TestRecentlyCompleted:
    def test_recently_completed_returns_200(self):
        with patch("app.services.novel_service.get_recently_completed", return_value=[MOCK_NOVEL_LIST_ITEM]):
            r = client.get("/api/v1/novels/recently-completed")
        assert r.status_code == 200 and len(r.json()) == 1

class TestGetTags:
    def test_get_tags_returns_200(self):
        tags = [{"id": "t1", "name": "Tu tien", "slug": "tu-tien", "created_at": "2026-01-01T00:00:00+00:00"}]
        with patch("app.services.novel_service.get_all_tags", return_value=tags):
            r = client.get("/api/v1/novels/tags")
        assert r.status_code == 200 and r.json()[0]["slug"] == "tu-tien"

class TestGetNovelById:
    def test_get_existing_novel_returns_200(self):
        with patch("app.services.novel_service.get_novel_by_id", return_value=MOCK_NOVEL_FULL):
            r = client.get("/api/v1/novels/novel-uuid-1")
        assert r.status_code == 200 and r.json()["id"] == "novel-uuid-1"
        assert r.json()["uploader"]["username"] == "uploader_user"

    def test_get_missing_novel_returns_404(self):
        with patch("app.services.novel_service.get_novel_by_id", return_value=None):
            r = client.get("/api/v1/novels/nonexistent-uuid")
        assert r.status_code == 404 and r.json()["detail"] == "Novel not found"

    def test_get_novel_includes_tags(self):
        with patch("app.services.novel_service.get_novel_by_id", return_value=MOCK_NOVEL_FULL):
            r = client.get("/api/v1/novels/novel-uuid-1")
        assert r.status_code == 200
        assert r.json()["tags"][0]["slug"] == "tu-tien"

class TestCreateNovel:
    def test_create_without_auth_returns_401(self):
        r = client.post("/api/v1/novels", json={"title": "T", "author": "A"})
        assert r.status_code == 401

    def test_create_as_reader_returns_403(self):
        tok = make_token(user_id="reader-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post("/api/v1/novels", json={"title": "T", "author": "A"}, headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403

    def test_create_as_uploader_returns_201(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.novel_service.create_novel", return_value=MOCK_NOVEL_FULL) as mc:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post("/api/v1/novels", json={"title": "New", "author": "Auth"}, headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 201
        mc.assert_called_once()

    def test_create_missing_required_fields_returns_422(self):
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post("/api/v1/novels", json={"title": "Only Title"}, headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 422

class TestUpdateNovel:
    def test_update_without_auth_returns_401(self):
        r = client.patch("/api/v1/novels/novel-uuid-1", json={"title": "Updated"})
        assert r.status_code == 401

    def test_update_as_non_owner_returns_403(self):
        other = {**MOCK_USER_UPLOADER, "id": "other-uploader-uuid"}
        tok = make_token(user_id="other-uploader-uuid")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.novel_service.get_novel_by_id", return_value=MOCK_NOVEL_FULL):
            ms.return_value = _make_user_supabase_mock(other)
            r = client.patch("/api/v1/novels/novel-uuid-1", json={"title": "X"}, headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403

    def test_update_as_owner_returns_200(self):
        tok = make_token(user_id="uploader-uuid")
        updated = {**MOCK_NOVEL_FULL, "title": "Updated Title"}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.novel_service.get_novel_by_id", return_value=MOCK_NOVEL_FULL), \
             patch("app.services.novel_service.update_novel", return_value=updated):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.patch("/api/v1/novels/novel-uuid-1", json={"title": "Updated Title"}, headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200 and r.json()["title"] == "Updated Title"

    def test_update_missing_novel_returns_404(self):
        tok = make_token(user_id="uploader-uuid")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.novel_service.get_novel_by_id", return_value=None):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.patch("/api/v1/novels/x", json={"title": "u"}, headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 404

class TestDeleteNovel:
    def test_delete_without_auth_returns_401(self):
        assert client.delete("/api/v1/novels/novel-uuid-1").status_code == 401

    def test_delete_as_non_owner_returns_403(self):
        other = {**MOCK_USER_UPLOADER, "id": "other-uploader-uuid"}
        tok = make_token(user_id="other-uploader-uuid")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.novel_service.get_novel_by_id", return_value=MOCK_NOVEL_FULL):
            ms.return_value = _make_user_supabase_mock(other)
            r = client.delete("/api/v1/novels/novel-uuid-1", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403

    def test_delete_as_owner_returns_204(self):
        tok = make_token(user_id="uploader-uuid")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.novel_service.get_novel_by_id", return_value=MOCK_NOVEL_FULL), \
             patch("app.services.novel_service.soft_delete_novel") as md:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.delete("/api/v1/novels/novel-uuid-1", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 204
        md.assert_called_once_with("novel-uuid-1")

    def test_delete_missing_novel_returns_404(self):
        tok = make_token(user_id="uploader-uuid")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.novel_service.get_novel_by_id", return_value=None):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.delete("/api/v1/novels/x", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 404
