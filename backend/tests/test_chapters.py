"""Tests for chapters API endpoints."""
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_token(user_id: str = "uploader-uuid", role: str = "uploader") -> str:
    from jose import jwt

    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


NOVEL_ID = "novel-uuid-1"
CHAPTER_NUM = 1

MOCK_CHAPTER_LIST_ITEM = {
    "id": "chapter-uuid-1",
    "novel_id": NOVEL_ID,
    "chapter_number": CHAPTER_NUM,
    "title": "Chapter 1: The Beginning",
    "word_count": 2500,
    "status": "published",
    "publish_at": None,
    "published_at": "2026-01-01T00:00:00+00:00",
    "views": 1000,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}

MOCK_CHAPTER_CONTENT = {
    **MOCK_CHAPTER_LIST_ITEM,
    "content": "Once upon a time in a world of cultivation...",
    "prev_chapter": None,
    "next_chapter": 2,
    "novel_title": "Test Novel Title",
}

MOCK_READING_PROGRESS = {
    "user_id": "reader-uuid",
    "novel_id": NOVEL_ID,
    "last_chapter_read": CHAPTER_NUM,
    "chapters_read_list": [CHAPTER_NUM],
    "updated_at": "2026-01-01T12:00:00+00:00",
}

MOCK_USER_READER = {
    "id": "reader-uuid", "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 0, "level": 0, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}
MOCK_USER_UPLOADER = {
    **MOCK_USER_READER,
    "id": "uploader-uuid",
    "username": "uploader_user",
    "role": "uploader",
}


def _make_user_supabase_mock(user):
    r = MagicMock()
    r.data = user
    c = MagicMock()
    c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = r
    return c


class TestListChapters:
    def test_list_chapters_returns_200(self):
        """Test 1: GET /novels/{id}/chapters returns 200 with list."""
        with patch("app.services.chapter_service.get_chapters_for_novel",
                   return_value=[MOCK_CHAPTER_LIST_ITEM]):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/chapters")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["chapter_number"] == CHAPTER_NUM


class TestCreateChapter:
    def test_create_chapter_reader_gets_403(self):
        """Test 2: POST /novels/{id}/chapters requires uploader role - 403 for reader."""
        tok = make_token(user_id="reader-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/chapters",
                json={"chapter_number": 1, "content": "Some content"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 403

    def test_create_chapter_no_auth_gets_401(self):
        """Test 3: POST /novels/{id}/chapters without auth returns 401."""
        r = client.post(
            f"/api/v1/novels/{NOVEL_ID}/chapters",
            json={"chapter_number": 1, "content": "Some content"},
        )
        assert r.status_code == 401

    def test_create_chapter_as_uploader_gets_201(self):
        """Test 4: POST /novels/{id}/chapters as uploader returns 201."""
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms,              patch("app.services.chapter_service.create_chapter",
                   return_value=MOCK_CHAPTER_LIST_ITEM):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/chapters",
                json={"chapter_number": 1, "content": "Some content"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert r.json()["chapter_number"] == CHAPTER_NUM


class TestGetChapter:
    def test_get_chapter_returns_200_with_content(self):
        """Test 5: GET /novels/{id}/chapters/{num} returns 200 with content + nav."""
        with patch("app.services.chapter_service.get_chapter_with_nav",
                   return_value=MOCK_CHAPTER_CONTENT):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/chapters/{CHAPTER_NUM}")
        assert r.status_code == 200
        data = r.json()
        assert "content" in data
        assert data["next_chapter"] == 2
        assert data["prev_chapter"] is None
        assert data["novel_title"] == "Test Novel Title"

    def test_get_chapter_404_for_missing(self):
        """Test 6: GET /novels/{id}/chapters/{num} returns 404 for missing chapter."""
        with patch("app.services.chapter_service.get_chapter_with_nav",
                   side_effect=HTTPException(status_code=404, detail="Chapter not found")):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/chapters/9999")
        assert r.status_code == 404
        assert r.json()["detail"] == "Chapter not found"

    def test_get_chapter_403_for_vip_gated_unauthenticated(self):
        """Test 7: GET /novels/{id}/chapters/{num} returns 403 for VIP-gated unauthenticated user."""
        with patch("app.services.chapter_service.get_chapter_with_nav",
                   side_effect=HTTPException(status_code=403, detail="VIP Pro hoac VIP Max de doc som")):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/chapters/{CHAPTER_NUM}")
        assert r.status_code == 403


class TestUpdateChapter:
    def test_update_chapter_no_auth_gets_401(self):
        """Test 8: PATCH /novels/{id}/chapters/{num} without auth returns 401."""
        r = client.patch(
            f"/api/v1/novels/{NOVEL_ID}/chapters/{CHAPTER_NUM}",
            json={"title": "Updated Title"},
        )
        assert r.status_code == 401

    def test_update_chapter_as_owner_returns_200(self):
        """Test: PATCH as owner returns 200."""
        tok = make_token(user_id="uploader-uuid")
        updated = {**MOCK_CHAPTER_LIST_ITEM, "title": "Updated Title"}
        with patch("app.core.deps.get_supabase") as ms,              patch("app.services.chapter_service.get_chapter", return_value=MOCK_CHAPTER_LIST_ITEM),              patch("app.services.chapter_service.update_chapter", return_value=updated):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.patch(
                f"/api/v1/novels/{NOVEL_ID}/chapters/{CHAPTER_NUM}",
                json={"title": "Updated Title"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Title"


class TestDeleteChapter:
    def test_delete_chapter_404_for_missing(self):
        """Test 9: DELETE /novels/{id}/chapters/{num} returns 404 for missing chapter."""
        tok = make_token(user_id="uploader-uuid")
        with patch("app.core.deps.get_supabase") as ms,              patch("app.services.chapter_service.get_chapter", return_value=None):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.delete(
                f"/api/v1/novels/{NOVEL_ID}/chapters/9999",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 404

    def test_delete_chapter_as_owner_returns_204(self):
        """Test: DELETE as owner returns 204."""
        tok = make_token(user_id="uploader-uuid")
        with patch("app.core.deps.get_supabase") as ms,              patch("app.services.chapter_service.get_chapter", return_value=MOCK_CHAPTER_LIST_ITEM),              patch("app.services.chapter_service.soft_delete_chapter") as md:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.delete(
                f"/api/v1/novels/{NOVEL_ID}/chapters/{CHAPTER_NUM}",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 204
        md.assert_called_once()


class TestMarkRead:
    def test_mark_read_no_auth_gets_401(self):
        """Test 10: POST /novels/{id}/chapters/{num}/read requires auth - 401."""
        r = client.post(f"/api/v1/novels/{NOVEL_ID}/chapters/{CHAPTER_NUM}/read")
        assert r.status_code == 401

    def test_mark_read_as_user_returns_progress(self):
        """Test 11: POST mark read marks chapter and returns progress."""
        tok = make_token(user_id="reader-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as ms,              patch("app.services.chapter_service.mark_chapter_read",
                   return_value=MOCK_READING_PROGRESS):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/chapters/{CHAPTER_NUM}/read",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["last_chapter_read"] == CHAPTER_NUM
        assert CHAPTER_NUM in data["chapters_read_list"]


class TestUserLibrary:
    def test_library_no_auth_gets_401(self):
        """Test 12: GET /users/me/library requires auth - 401."""
        r = client.get("/api/v1/users/me/library")
        assert r.status_code == 401

    def test_library_returns_list(self):
        """Test 13: GET /users/me/library returns library list."""
        mock_library = [
            {
                "novel_id": NOVEL_ID,
                "last_chapter_read": 5,
                "chapters_read_list": [1, 2, 3, 4, 5],
                "updated_at": "2026-01-10T12:00:00+00:00",
                "novel": {
                    "id": NOVEL_ID,
                    "title": "Test Novel Title",
                    "author": "Test Author",
                    "cover_url": None,
                    "status": "ongoing",
                    "total_chapters": 100,
                    "updated_at": "2026-01-10T12:00:00+00:00",
                },
            }
        ]
        tok = make_token(user_id="reader-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as ms,              patch("app.services.chapter_service.get_user_library", return_value=mock_library):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.get("/api/v1/users/me/library", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["novel"]["title"] == "Test Novel Title"
        assert data[0]["last_chapter_read"] == 5
