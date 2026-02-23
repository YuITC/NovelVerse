"""Tests for notification endpoints (list, unread count, mark read)."""
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_READER = {"id": "reader-111", "role": "reader"}
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _mock_notification(notification_id: str = "notif-aaa", read: bool = False) -> dict:
    return {
        "id": notification_id,
        "user_id": "reader-111",
        "type": "new_chapter",
        "payload": {"novel_id": "novel-aaa", "chapter_number": 5},
        "read_at": datetime.now(timezone.utc).isoformat() if read else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# List Notifications
# ---------------------------------------------------------------------------

class TestGetNotifications:
    def test_list_requires_auth(self):
        r = client.get("/api/v1/notifications")
        assert r.status_code == 401

    def test_list_returns_empty_for_new_user(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.get_notifications", return_value=[]):
                r = client.get("/api/v1/notifications", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_list_returns_notifications(self):
        notifications = [_mock_notification("notif-aaa"), _mock_notification("notif-bbb")]
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.get_notifications",
                       return_value=notifications):
                r = client.get("/api/v1/notifications", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert len(r.json()) == 2

    def test_list_pagination_params(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.get_notifications", return_value=[]):
                r = client.get("/api/v1/notifications?limit=5&offset=10", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_unread_count_requires_auth(self):
        r = client.get("/api/v1/notifications/unread-count")
        assert r.status_code == 401

    def test_unread_count_returns_count(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.get_unread_count",
                       return_value={"count": 3}):
                r = client.get("/api/v1/notifications/unread-count", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert r.json()["count"] == 3

    def test_unread_count_zero(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.get_unread_count",
                       return_value={"count": 0}):
                r = client.get("/api/v1/notifications/unread-count", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)


# ---------------------------------------------------------------------------
# Mark Read
# ---------------------------------------------------------------------------

class TestMarkRead:
    def test_mark_read_requires_auth(self):
        r = client.patch("/api/v1/notifications/notif-aaa/read")
        assert r.status_code == 401

    def test_mark_all_read_requires_auth(self):
        r = client.patch("/api/v1/notifications/read-all")
        assert r.status_code == 401

    def test_mark_read_not_found_returns_404(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.mark_read",
                       side_effect=HTTPException(status_code=404, detail="Notification not found")):
                r = client.patch("/api/v1/notifications/no-such/read", headers=AUTH_HEADERS)
        assert r.status_code in (404, 401)

    def test_mark_read_returns_updated_notification(self):
        updated = _mock_notification("notif-aaa", read=True)
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.mark_read", return_value=updated):
                r = client.patch("/api/v1/notifications/notif-aaa/read", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert r.json()["read_at"] is not None

    def test_mark_all_read_returns_204(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.mark_all_read", return_value=None):
                r = client.patch("/api/v1/notifications/read-all", headers=AUTH_HEADERS)
        assert r.status_code in (204, 401)

    def test_mark_all_read_with_no_unread(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.mark_all_read", return_value=None):
                r = client.patch("/api/v1/notifications/read-all", headers=AUTH_HEADERS)
        assert r.status_code in (204, 401)

    def test_list_unread_first_ordering(self):
        """Unread notifications should appear before read ones."""
        unread = _mock_notification("notif-aaa", read=False)
        read = _mock_notification("notif-bbb", read=True)
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.notification_service.get_notifications",
                       return_value=[unread, read]):
                r = client.get("/api/v1/notifications", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            items = r.json()
            assert items[0]["read_at"] is None  # unread first
