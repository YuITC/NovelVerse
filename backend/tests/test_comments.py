"""Tests for comments and reviews API endpoints."""
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_token(user_id: str = "reader-uuid", role: str = "reader") -> str:
    from jose import jwt

    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


NOVEL_ID = "novel-uuid-1"
COMMENT_ID = "comment-uuid-1"
REPLY_ID = "comment-uuid-2"

MOCK_COMMENT = {
    "id": COMMENT_ID,
    "novel_id": NOVEL_ID,
    "chapter_id": None,
    "user_id": "reader-uuid",
    "parent_id": None,
    "content": "This is a great novel!",
    "likes": 0,
    "is_deleted": False,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}

MOCK_REPLY = {
    "id": REPLY_ID,
    "novel_id": NOVEL_ID,
    "chapter_id": None,
    "user_id": "reader-uuid",
    "parent_id": COMMENT_ID,
    "content": "I agree with this comment!",
    "likes": 0,
    "is_deleted": False,
    "created_at": "2026-01-01T01:00:00+00:00",
    "updated_at": "2026-01-01T01:00:00+00:00",
}

MOCK_REVIEW = {
    "id": "review-uuid-1",
    "novel_id": NOVEL_ID,
    "user_id": "reader-uuid",
    "rating": 5,
    "content": "This is a wonderful novel with great character development and plot twists.",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}

MOCK_USER_READER = {
    "id": "reader-uuid", "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 0, "level": 0, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}

MOCK_USER_ADMIN = {
    **MOCK_USER_READER,
    "id": "admin-uuid",
    "username": "admin_user",
    "role": "admin",
}


def _make_user_supabase_mock(user):
    r = MagicMock()
    r.data = user
    c = MagicMock()
    c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = r
    return c


# -- Comment List Tests

class TestListComments:
    def test_list_comments_returns_200_no_auth(self):
        """Test 1: GET /novels/{id}/comments returns 200 with list (no auth needed)."""
        with patch("app.services.comment_service.get_comments_for_novel", return_value=[MOCK_COMMENT]):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/comments")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == COMMENT_ID

    def test_list_comments_empty_list(self):
        """GET /novels/{id}/comments returns empty list when no comments."""
        with patch("app.services.comment_service.get_comments_for_novel", return_value=[]):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/comments")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_comments_sort_param_passed(self):
        """Sort parameter is forwarded to service."""
        with patch("app.services.comment_service.get_comments_for_novel", return_value=[]) as m:
            client.get(f"/api/v1/novels/{NOVEL_ID}/comments?sort=most_liked")
        m.assert_called_once_with(NOVEL_ID, sort="most_liked", limit=20, offset=0)

    def test_list_comments_invalid_sort_returns_422(self):
        """Invalid sort value returns 422."""
        r = client.get(f"/api/v1/novels/{NOVEL_ID}/comments?sort=invalid")
        assert r.status_code == 422


# -- Replies Tests

class TestListReplies:
    def test_list_replies_returns_200(self):
        """Test 2: GET /comments/{id}/replies returns 200."""
        with patch("app.services.comment_service.get_replies_for_comment", return_value=[MOCK_REPLY]):
            r = client.get(f"/api/v1/comments/{COMMENT_ID}/replies")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["parent_id"] == COMMENT_ID

    def test_list_replies_empty(self):
        """GET /comments/{id}/replies returns empty list for comment with no replies."""
        with patch("app.services.comment_service.get_replies_for_comment", return_value=[]):
            r = client.get(f"/api/v1/comments/{COMMENT_ID}/replies")
        assert r.status_code == 200
        assert r.json() == []


# -- Create Comment Tests

class TestCreateComment:
    def test_create_comment_without_auth_returns_401(self):
        """Test 3: POST /novels/{id}/comments without auth returns 401."""
        r = client.post(
            f"/api/v1/novels/{NOVEL_ID}/comments",
            json={"content": "Hello world"},
        )
        assert r.status_code == 401

    def test_create_comment_with_auth_returns_201(self):
        """Test 4: POST /novels/{id}/comments with auth returns 201."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.create_comment", return_value=MOCK_COMMENT):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/comments",
                json={"content": "This is a great novel!"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert r.json()["id"] == COMMENT_ID
        assert r.json()["content"] == "This is a great novel!"

    def test_create_comment_with_parent_id_reply_returns_201(self):
        """Test 5: POST /novels/{id}/comments with parent_id (reply) returns 201."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.create_comment", return_value=MOCK_REPLY):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/comments",
                json={"content": "I agree with this comment!", "parent_id": COMMENT_ID},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert r.json()["parent_id"] == COMMENT_ID

    def test_create_comment_empty_content_returns_422(self):
        """POST with empty content returns 422."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/comments",
                json={"content": "   "},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 422

    def test_create_comment_with_chapter_id(self):
        """POST with chapter_id creates a chapter-level comment."""
        tok = make_token()
        chapter_comment = {**MOCK_COMMENT, "chapter_id": "chapter-uuid-1"}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.create_comment", return_value=chapter_comment):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/comments",
                json={"content": "Chapter comment!", "chapter_id": "chapter-uuid-1"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert r.json()["chapter_id"] == "chapter-uuid-1"


# -- Toggle Like Tests

class TestToggleLike:
    def test_toggle_like_without_auth_returns_401(self):
        """Test 6: POST /comments/{id}/like without auth returns 401."""
        r = client.post(f"/api/v1/comments/{COMMENT_ID}/like")
        assert r.status_code == 401

    def test_toggle_like_with_auth_returns_200(self):
        """Test 7: POST /comments/{id}/like with auth returns 200."""
        tok = make_token()
        liked_comment = {**MOCK_COMMENT, "likes": 1}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.toggle_like", return_value=liked_comment):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/comments/{COMMENT_ID}/like",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 200
        assert r.json()["likes"] == 1

    def test_toggle_like_comment_not_found_returns_404(self):
        """POST like on non-existent comment returns 404."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.toggle_like",
                   side_effect=HTTPException(status_code=404, detail="Comment not found")):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                "/api/v1/comments/nonexistent-id/like",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 404


# -- Delete Comment Tests

class TestDeleteComment:
    def test_delete_comment_without_auth_returns_401(self):
        """Test 8: DELETE /comments/{id} without auth returns 401."""
        r = client.delete(f"/api/v1/comments/{COMMENT_ID}")
        assert r.status_code == 401

    def test_delete_comment_as_owner_returns_204(self):
        """Test 9: DELETE /comments/{id} as owner returns 204."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.soft_delete_comment") as md:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.delete(
                f"/api/v1/comments/{COMMENT_ID}",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 204
        md.assert_called_once_with(COMMENT_ID, "reader-uuid", "reader")

    def test_delete_comment_as_admin_returns_204(self):
        """DELETE /comments/{id} as admin returns 204."""
        tok = make_token(user_id="admin-uuid", role="admin")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.soft_delete_comment") as md:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            r = client.delete(
                f"/api/v1/comments/{COMMENT_ID}",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 204
        md.assert_called_once_with(COMMENT_ID, "admin-uuid", "admin")

    def test_delete_comment_not_owner_returns_403(self):
        """DELETE /comments/{id} as non-owner returns 403."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.soft_delete_comment",
                   side_effect=HTTPException(status_code=403, detail="Not authorized")):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.delete(
                f"/api/v1/comments/{COMMENT_ID}",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 403

    def test_delete_comment_not_found_returns_404(self):
        """DELETE /comments/{id} for non-existent comment returns 404."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.soft_delete_comment",
                   side_effect=HTTPException(status_code=404, detail="Comment not found")):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.delete(
                "/api/v1/comments/nonexistent-id",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 404


# -- Reviews Tests

class TestListReviews:
    def test_list_reviews_returns_200(self):
        """Test 10: GET /novels/{id}/reviews returns 200."""
        with patch("app.services.comment_service.get_reviews_for_novel", return_value=[MOCK_REVIEW]):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/reviews")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["rating"] == 5

    def test_list_reviews_empty(self):
        """GET /novels/{id}/reviews returns empty list."""
        with patch("app.services.comment_service.get_reviews_for_novel", return_value=[]):
            r = client.get(f"/api/v1/novels/{NOVEL_ID}/reviews")
        assert r.status_code == 200
        assert r.json() == []


class TestCreateReview:
    def test_create_review_without_auth_returns_401(self):
        """Test 11: POST /novels/{id}/reviews without auth returns 401."""
        r = client.post(
            f"/api/v1/novels/{NOVEL_ID}/reviews",
            json={"rating": 5, "content": "This is a wonderful novel with great character development and plot twists."},
        )
        assert r.status_code == 401

    def test_create_review_too_few_words_returns_422(self):
        """Test 12: POST /novels/{id}/reviews with too few words returns 422."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/reviews",
                json={"rating": 5, "content": "Too short review."},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 422

    def test_create_review_with_auth_returns_201(self):
        """Test 13: POST /novels/{id}/reviews with auth returns 201."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.create_review", return_value=MOCK_REVIEW):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/reviews",
                json={
                    "rating": 5,
                    "content": "This is a wonderful novel with great character development and plot twists.",
                },
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert r.json()["rating"] == 5

    def test_create_review_invalid_rating_returns_422(self):
        """POST with rating out of range (1-5) returns 422."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/reviews",
                json={"rating": 6, "content": "This novel has some great aspects but also some major flaws in plot."},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 422

    def test_create_review_duplicate_returns_409(self):
        """POST review when user already reviewed returns 409."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.create_review",
                   side_effect=HTTPException(status_code=409, detail="You have already reviewed this novel")):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.post(
                f"/api/v1/novels/{NOVEL_ID}/reviews",
                json={
                    "rating": 4,
                    "content": "This is a wonderful novel with great character development and plot.",
                },
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 409
        assert "already reviewed" in r.json()["detail"]


class TestUpdateReview:
    def test_update_review_with_auth_returns_200(self):
        """Test 14: PATCH /novels/{id}/reviews/me with auth returns 200."""
        tok = make_token()
        updated_review = {**MOCK_REVIEW, "rating": 4}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.update_review", return_value=updated_review):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.patch(
                f"/api/v1/novels/{NOVEL_ID}/reviews/me",
                json={"rating": 4},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 200
        assert r.json()["rating"] == 4

    def test_update_review_without_auth_returns_401(self):
        """PATCH /novels/{id}/reviews/me without auth returns 401."""
        r = client.patch(
            f"/api/v1/novels/{NOVEL_ID}/reviews/me",
            json={"rating": 3},
        )
        assert r.status_code == 401

    def test_update_review_not_found_returns_404(self):
        """PATCH /novels/{id}/reviews/me when no review exists returns 404."""
        tok = make_token()
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.update_review",
                   side_effect=HTTPException(status_code=404, detail="Review not found")):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.patch(
                f"/api/v1/novels/{NOVEL_ID}/reviews/me",
                json={"rating": 3},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 404

    def test_update_review_content_only(self):
        """PATCH /novels/{id}/reviews/me can update just content."""
        tok = make_token()
        updated_content = "This novel has improved greatly over time with superb world building and characters."
        updated_review = {**MOCK_REVIEW, "content": updated_content}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.comment_service.update_review", return_value=updated_review):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.patch(
                f"/api/v1/novels/{NOVEL_ID}/reviews/me",
                json={"content": updated_content},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 200
        assert r.json()["content"] == updated_content
