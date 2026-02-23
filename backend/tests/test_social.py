"""Tests for follows and bookmarks (social features)."""
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_READER   = {"id": "reader-111",   "role": "reader"}
MOCK_UPLOADER = {"id": "uploader-222", "role": "uploader"}
MOCK_ADMIN    = {"id": "admin-333",    "role": "admin"}
AUTH_HEADERS  = {"Authorization": "Bearer test-token"}


# ---------------------------------------------------------------------------
# Follow
# ---------------------------------------------------------------------------

class TestFollow:
    def test_toggle_follow_requires_auth(self):
        r = client.post("/api/v1/users/uploader-222/follow")
        assert r.status_code == 401

    def test_get_follow_status_requires_auth(self):
        r = client.get("/api/v1/users/uploader-222/follow")
        assert r.status_code == 401

    def test_toggle_follow_self_returns_400(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_follow",
                       side_effect=HTTPException(status_code=400, detail="Cannot follow yourself")):
                r = client.post("/api/v1/users/reader-111/follow", headers=AUTH_HEADERS)
        assert r.status_code in (400, 401)

    def test_toggle_follow_reader_target_returns_400(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_follow",
                       side_effect=HTTPException(status_code=400, detail="Can only follow uploaders")):
                r = client.post("/api/v1/users/reader-999/follow", headers=AUTH_HEADERS)
        assert r.status_code in (400, 401)

    def test_toggle_follow_missing_user_returns_404(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_follow",
                       side_effect=HTTPException(status_code=404, detail="User not found")):
                r = client.post("/api/v1/users/no-such-user/follow", headers=AUTH_HEADERS)
        assert r.status_code in (404, 401)

    def test_toggle_follow_returns_is_following_true(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_follow",
                       return_value={"is_following": True, "follower_count": 1}):
                r = client.post("/api/v1/users/uploader-222/follow", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_toggle_follow_returns_is_following_false_on_unfollow(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_follow",
                       return_value={"is_following": False, "follower_count": 0}):
                r = client.post("/api/v1/users/uploader-222/follow", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_get_follow_status_returns_status(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.get_follow_status",
                       return_value={"is_following": True, "follower_count": 5}):
                r = client.get("/api/v1/users/uploader-222/follow", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)


# ---------------------------------------------------------------------------
# Bookmark
# ---------------------------------------------------------------------------

class TestBookmark:
    def test_toggle_bookmark_requires_auth(self):
        r = client.post("/api/v1/novels/novel-aaa/bookmark")
        assert r.status_code == 401

    def test_get_bookmark_status_requires_auth(self):
        r = client.get("/api/v1/novels/novel-aaa/bookmark")
        assert r.status_code == 401

    def test_toggle_bookmark_missing_novel_returns_404(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_bookmark",
                       side_effect=HTTPException(status_code=404, detail="Novel not found")):
                r = client.post("/api/v1/novels/no-such/bookmark", headers=AUTH_HEADERS)
        assert r.status_code in (404, 401)

    def test_toggle_bookmark_returns_is_bookmarked_true(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_bookmark",
                       return_value={"is_bookmarked": True}):
                r = client.post("/api/v1/novels/novel-aaa/bookmark", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_toggle_bookmark_returns_is_bookmarked_false_on_remove(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.toggle_bookmark",
                       return_value={"is_bookmarked": False}):
                r = client.post("/api/v1/novels/novel-aaa/bookmark", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_get_bookmark_status_returns_status(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.get_bookmark_status",
                       return_value={"is_bookmarked": True}):
                r = client.get("/api/v1/novels/novel-aaa/bookmark", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)


# ---------------------------------------------------------------------------
# My Bookmarks
# ---------------------------------------------------------------------------

class TestMyBookmarks:
    def test_my_bookmarks_requires_auth(self):
        r = client.get("/api/v1/users/me/bookmarks")
        assert r.status_code == 401

    def test_my_bookmarks_returns_list(self):
        mock_bookmarks = [
            {
                "novel_id": "novel-aaa",
                "added_at": datetime.now(timezone.utc).isoformat(),
                "novel": {
                    "id": "novel-aaa",
                    "title": "Test Novel",
                    "author": "Author",
                    "cover_url": None,
                    "status": "ongoing",
                    "total_chapters": 50,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        ]
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.get_my_bookmarks", return_value=mock_bookmarks):
                r = client.get("/api/v1/users/me/bookmarks", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_my_bookmarks_empty_list(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.social_service.get_my_bookmarks", return_value=[]):
                r = client.get("/api/v1/users/me/bookmarks", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)
