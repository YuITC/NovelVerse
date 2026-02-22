"""Tests for Admin Panel API endpoints (Milestone 7)."""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_token(user_id="user-uuid", role="reader") -> str:
    from jose import jwt
    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


MOCK_USER_READER = {
    "id": "user-uuid", "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 0, "level": 0, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}
MOCK_USER_ADMIN = {**MOCK_USER_READER, "id": "admin-uuid", "username": "admin_user", "role": "admin"}
MOCK_USER_LIST_ITEM = {"id": "user-uuid", "username": "reader_user", "role": "reader", "is_banned": False, "ban_until": None, "vip_tier": "none", "chapters_read": 0, "level": 0, "created_at": "2026-01-01T00:00:00+00:00"}
MOCK_NOVEL = {"id": "novel-uuid", "is_pinned": False, "is_deleted": False}
MOCK_REPORT = {"id": "report-uuid", "reporter_id": "user-uuid", "target_type": "novel", "target_id": "novel-uuid", "reason": "Inappropriate content", "status": "pending", "admin_note": None, "created_at": "2026-01-01T00:00:00+00:00"}
MOCK_RESOLVED_REPORT = {**MOCK_REPORT, "status": "resolved", "admin_note": "Reviewed and resolved"}
MOCK_FEEDBACK = {"id": "feedback-uuid", "user_id": "user-uuid", "content": "Great platform!", "status": "open", "admin_response": None, "created_at": "2026-01-01T00:00:00+00:00"}
MOCK_RESPONDED_FEEDBACK = {**MOCK_FEEDBACK, "status": "reviewed", "admin_response": "Thank you for your feedback!"}


def _make_user_supabase_mock(user):
    r = MagicMock()
    r.data = user
    c = MagicMock()
    c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = r
    return c

class TestListUsersAuth:
    def test_list_users_without_auth_returns_401(self):
        assert client.get("/api/v1/admin/users").status_code == 401

    def test_list_users_as_reader_returns_403(self):
        token = make_token(user_id="user-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as m:
            m.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_list_users_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [MOCK_USER_LIST_ITEM]
            svc.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = res
            r = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json(); assert isinstance(data, list) and len(data) == 1
        assert data[0]["username"] == "reader_user"


class TestUpdateUserRole:
    def test_update_role_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        updated = {**MOCK_USER_LIST_ITEM, "role": "uploader"}
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [updated]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = res
            r = client.patch("/api/v1/admin/users/user-uuid/role", json={"role": "uploader"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200; assert r.json()["role"] == "uploader"

    def test_update_role_with_invalid_role_returns_400(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with patch("app.core.deps.get_supabase") as m:
            m.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            r = client.patch("/api/v1/admin/users/user-uuid/role", json={"role": "superuser"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 400; assert "Invalid role" in r.json()["detail"]


class TestBanUnbanUser:
    def test_ban_user_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        banned = {**MOCK_USER_LIST_ITEM, "is_banned": True}
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [banned]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = res
            r = client.post("/api/v1/admin/users/user-uuid/ban", json={}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200; assert r.json()["is_banned"] is True

    def test_unban_user_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        unbanned = {**MOCK_USER_LIST_ITEM, "is_banned": False}
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [unbanned]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = res
            r = client.post("/api/v1/admin/users/user-uuid/unban", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200; assert r.json()["is_banned"] is False

class TestNovelPinUnpin:
    def test_pin_novel_as_admin_returns_200(self):
        token = make_token()
        assert True
class TestNovelPinUnpin:
    def test_pin_novel_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        pinned = {**MOCK_NOVEL, "is_pinned": True}
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [pinned]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = res
            r = client.post("/api/v1/admin/novels/novel-uuid/pin", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200; assert r.json()["is_pinned"] is True

    def test_unpin_novel_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        unpinned = {**MOCK_NOVEL, "is_pinned": False}
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [unpinned]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = res
            r = client.post("/api/v1/admin/novels/novel-uuid/unpin", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200; assert r.json()["is_pinned"] is False


class TestReports:
    def test_create_report_requires_auth_returns_401(self):
        r = client.post("/api/v1/reports", json={"target_type": "novel", "target_id": "novel-uuid", "reason": "Spam"})
        assert r.status_code == 401

    def test_create_report_as_authenticated_user_returns_201(self):
        token = make_token(user_id="user-uuid", role="reader")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [MOCK_REPORT]
            svc.table.return_value.insert.return_value.execute.return_value = res
            r = client.post("/api/v1/reports", json={"target_type": "novel", "target_id": "novel-uuid", "reason": "Inappropriate content"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 201
        assert r.json()["target_type"] == "novel"
        assert r.json()["status"] == "pending"

    def test_list_reports_as_reader_returns_403(self):
        token = make_token(user_id="user-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as m:
            m.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.get("/api/v1/admin/reports", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_list_reports_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [MOCK_REPORT]
            svc.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = res
            r = client.get("/api/v1/admin/reports", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json(); assert isinstance(data, list) and len(data) == 1
        assert data[0]["status"] == "pending"

    def test_resolve_report_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc
            ex = MagicMock(); ex.data = {"id": "report-uuid"}
            svc.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = ex
            upd = MagicMock(); upd.data = [MOCK_RESOLVED_REPORT]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = upd
            r = client.patch("/api/v1/admin/reports/report-uuid", json={"status": "resolved", "admin_note": "Reviewed and resolved"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"
        assert r.json()["admin_note"] == "Reviewed and resolved"


class TestFeedbacks:
    def test_create_feedback_anonymous_returns_201(self):
        with patch("app.services.admin_service.get_supabase") as ms:
            svc = MagicMock(); ms.return_value = svc; res = MagicMock()
            res.data = [{**MOCK_FEEDBACK, "user_id": None}]
            svc.table.return_value.insert.return_value.execute.return_value = res
            r = client.post("/api/v1/feedbacks", json={"content": "Great platform!"})
        assert r.status_code == 201
        assert r.json()["content"] == "Great platform!"
        assert r.json()["status"] == "open"

    def test_create_feedback_authenticated_returns_201(self):
        token = make_token(user_id="user-uuid", role="reader")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [MOCK_FEEDBACK]
            svc.table.return_value.insert.return_value.execute.return_value = res
            r = client.post("/api/v1/feedbacks", json={"content": "Great platform!"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 201; assert r.json()["user_id"] == "user-uuid"

    def test_create_feedback_too_short_returns_422(self):
        with patch("app.services.admin_service.get_supabase") as ms:
            ms.return_value = MagicMock()
            r = client.post("/api/v1/feedbacks", json={"content": "Hi"})
        assert r.status_code == 422

    def test_list_feedbacks_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [MOCK_FEEDBACK]
            svc.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = res
            r = client.get("/api/v1/admin/feedbacks", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json(); assert isinstance(data, list) and len(data) == 1
        assert data[0]["content"] == "Great platform!"

    def test_list_feedbacks_as_reader_returns_403(self):
        token = make_token(user_id="user-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as m:
            m.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.get("/api/v1/admin/feedbacks", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_respond_feedback_as_admin_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc
            ex = MagicMock(); ex.data = {"id": "feedback-uuid"}
            svc.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = ex
            upd = MagicMock(); upd.data = [MOCK_RESPONDED_FEEDBACK]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = upd
            r = client.patch("/api/v1/admin/feedbacks/feedback-uuid", json={"admin_response": "Thank you for your feedback!", "status": "reviewed"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["status"] == "reviewed"
        assert r.json()["admin_response"] == "Thank you for your feedback!"


class TestForceDeleteContent:
    def test_force_delete_novel_as_admin_returns_204(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc
            ex = MagicMock(); ex.data = {"id": "novel-uuid"}
            svc.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = ex
            upd = MagicMock(); upd.data = [{"id": "novel-uuid", "is_deleted": True}]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = upd
            r = client.delete("/api/v1/admin/novels/novel-uuid", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 204

    def test_force_delete_comment_as_admin_returns_204(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc
            ex = MagicMock(); ex.data = {"id": "comment-uuid"}
            svc.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = ex
            upd = MagicMock(); upd.data = [{"id": "comment-uuid", "is_deleted": True}]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = upd
            r = client.delete("/api/v1/admin/comments/comment-uuid", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 204

    def test_force_delete_novel_not_found_returns_404(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc
            ex = MagicMock(); ex.data = None
            svc.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = ex
            r = client.delete("/api/v1/admin/novels/nonexistent-uuid", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404


class TestBanUserWithExpiry:
    def test_ban_user_with_expiry_date_returns_200(self):
        token = make_token(user_id="admin-uuid", role="admin")
        banned = {**MOCK_USER_LIST_ITEM, "is_banned": True, "ban_until": "2026-03-01T00:00:00+00:00"}
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [banned]
            svc.table.return_value.update.return_value.eq.return_value.execute.return_value = res
            r = client.post("/api/v1/admin/users/user-uuid/ban", json={"ban_until": "2026-03-01T00:00:00Z"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["is_banned"] is True
        assert r.json()["ban_until"] is not None


class TestListUsersSearch:
    def test_list_users_with_search_param(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as md, patch("app.services.admin_service.get_supabase") as ms):
            md.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            svc = MagicMock(); ms.return_value = svc; res = MagicMock(); res.data = [MOCK_USER_LIST_ITEM]
            svc.table.return_value.select.return_value.ilike.return_value.order.return_value.range.return_value.execute.return_value = res
            r = client.get("/api/v1/admin/users?search=reader", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200; assert isinstance(r.json(), list)
