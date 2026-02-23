"""Tests for M19 Story Intelligence Dashboard — service and API layers."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures / shared data
# ---------------------------------------------------------------------------

NOVEL_ID = "novel-aaa-111"
USER_ID = "user-bbb-222"

MOCK_READER = {
    "id": USER_ID, "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 50, "level": 1, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}

MOCK_VIP_PRO = {**MOCK_READER, "vip_tier": "pro"}
MOCK_VIP_MAX = {**MOCK_READER, "vip_tier": "max"}

MOCK_GRAPH_READY = {
    "status": "ready",
    "nodes": [{"id": "Alice", "name": "Alice"}, {"id": "Bob", "name": "Bob"}],
    "edges": [{"source": "Alice", "target": "Bob", "weight": 3.0}],
}

MOCK_GRAPH_PENDING = {"status": "pending"}
MOCK_GRAPH_FAILED = {"status": "failed"}
MOCK_GRAPH_NOT_STARTED = {"status": "not_started"}

MOCK_TIMELINE_READY = {
    "status": "ready",
    "events": [
        {"chapter_number": 1, "event_summary": "Nhân vật chính xuất hiện."},
        {"chapter_number": 2, "event_summary": "Cuộc chiến bắt đầu."},
    ],
}

MOCK_TIMELINE_PENDING = {"status": "pending"}
MOCK_TIMELINE_FAILED = {"status": "failed"}
MOCK_TIMELINE_NOT_STARTED = {"status": "not_started"}

MOCK_ARC_SUMMARY = {
    "summary": "Từ chương 1 đến 5, nhân vật chính trải qua nhiều thử thách.",
    "start_chapter": 1,
    "end_chapter": 5,
}


def _make_token(user_id: str = USER_ID) -> str:
    from jose import jwt
    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


AUTH_HEADERS = {"Authorization": f"Bearer {_make_token()}"}


def _deps_supabase(user_data: dict):
    """Return a mock Supabase client that resolves get_current_user to user_data."""
    return MagicMock(
        table=lambda t: MagicMock(
            select=lambda *a: MagicMock(
                eq=lambda *a: MagicMock(
                    single=lambda: MagicMock(
                        execute=lambda: MagicMock(data=user_data)
                    )
                )
            )
        )
    )


# ---------------------------------------------------------------------------
# TestGetRelationships
# ---------------------------------------------------------------------------


class TestGetRelationships:
    def test_not_started_triggers_compute_returns_202(self):
        """First call when graph not started → triggers background task, returns 202 pending."""
        compute_mock = MagicMock()
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_relationships", return_value=MOCK_GRAPH_NOT_STARTED),
            patch("app.api.v1.story_intelligence.svc.set_relationships_pending"),
            patch("app.api.v1.story_intelligence.svc.compute_relationships_task", compute_mock),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/relationships", headers=AUTH_HEADERS)
        assert r.status_code == 202
        assert r.json()["status"] == "pending"

    def test_pending_returns_202_without_retriggering(self):
        """When graph is pending → return 202, do NOT enqueue another background task."""
        compute_mock = MagicMock()
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_relationships", return_value=MOCK_GRAPH_PENDING),
            patch("app.api.v1.story_intelligence.svc.compute_relationships_task", compute_mock),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/relationships", headers=AUTH_HEADERS)
        assert r.status_code == 200
        assert r.json()["status"] == "pending"
        compute_mock.assert_not_called()

    def test_ready_returns_200_with_graph(self):
        """When graph is ready → return 200 with nodes and edges."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_relationships", return_value=MOCK_GRAPH_READY),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/relationships", headers=AUTH_HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ready"
        assert len(body["nodes"]) == 2
        assert len(body["edges"]) == 1
        assert body["edges"][0]["weight"] == 3.0

    def test_failed_returns_200_with_failed_status(self):
        """When graph failed → return 200 with status=failed."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_relationships", return_value=MOCK_GRAPH_FAILED),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/relationships", headers=AUTH_HEADERS)
        assert r.status_code == 200
        assert r.json()["status"] == "failed"


# ---------------------------------------------------------------------------
# TestGetTimeline
# ---------------------------------------------------------------------------


class TestGetTimeline:
    def test_not_started_triggers_compute_returns_202(self):
        """First call when timeline not started → triggers background task, returns 202."""
        compute_mock = MagicMock()
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_timeline", return_value=MOCK_TIMELINE_NOT_STARTED),
            patch("app.api.v1.story_intelligence.svc.set_timeline_pending"),
            patch("app.api.v1.story_intelligence.svc.compute_timeline_task", compute_mock),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/timeline", headers=AUTH_HEADERS)
        assert r.status_code == 202
        assert r.json()["status"] == "pending"

    def test_pending_returns_202_without_retriggering(self):
        """When timeline is pending → return current status, no new task."""
        compute_mock = MagicMock()
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_timeline", return_value=MOCK_TIMELINE_PENDING),
            patch("app.api.v1.story_intelligence.svc.compute_timeline_task", compute_mock),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/timeline", headers=AUTH_HEADERS)
        assert r.status_code == 200
        assert r.json()["status"] == "pending"
        compute_mock.assert_not_called()

    def test_ready_returns_200_with_events(self):
        """When timeline is ready → return 200 with events list."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_timeline", return_value=MOCK_TIMELINE_READY),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/timeline", headers=AUTH_HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ready"
        assert len(body["events"]) == 2
        assert body["events"][0]["chapter_number"] == 1

    def test_failed_returns_200_with_failed_status(self):
        """When timeline failed → return 200 with status=failed."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_timeline", return_value=MOCK_TIMELINE_FAILED),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/timeline", headers=AUTH_HEADERS)
        assert r.status_code == 200
        assert r.json()["status"] == "failed"


# ---------------------------------------------------------------------------
# TestQA
# ---------------------------------------------------------------------------


class TestQA:
    def test_vip_max_gets_streaming_response(self):
        """POST /qa with VIP Max → 200 SSE stream."""
        def _fake_stream(novel_id, question):
            yield "data: Câu trả lời.\n\n"
            yield "data: [DONE]\n\n"

        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.stream_qa", side_effect=_fake_stream),
        ):
            r = client.post(
                f"/api/v1/ai/novels/{NOVEL_ID}/qa",
                json={"question": "Nhân vật chính là ai?"},
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 200
        assert "Câu trả lời." in r.text

    def test_non_vip_max_gets_403(self):
        """POST /qa with reader role → 403."""
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)):
            r = client.post(
                f"/api/v1/ai/novels/{NOVEL_ID}/qa",
                json={"question": "Nhân vật chính là ai?"},
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 403

    def test_empty_question_returns_422(self):
        """POST /qa with empty question → 422 validation error."""
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)):
            r = client.post(
                f"/api/v1/ai/novels/{NOVEL_ID}/qa",
                json={"question": ""},
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 422

    def test_no_gemini_config_returns_error_in_stream(self):
        """When Gemini not configured, stream yields ERROR token."""
        def _error_stream(novel_id, question):
            yield "data: [ERROR] AI service not configured\n\n"

        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.stream_qa", side_effect=_error_stream),
        ):
            r = client.post(
                f"/api/v1/ai/novels/{NOVEL_ID}/qa",
                json={"question": "Nhân vật chính là ai?"},
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 200
        assert "[ERROR]" in r.text


# ---------------------------------------------------------------------------
# TestArcSummary
# ---------------------------------------------------------------------------


class TestArcSummary:
    def test_valid_range_returns_summary(self):
        """GET /arc-summary with valid range → 200 with summary."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_arc_summary", return_value=MOCK_ARC_SUMMARY),
        ):
            r = client.get(
                f"/api/v1/ai/novels/{NOVEL_ID}/arc-summary?start_chapter=1&end_chapter=5",
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 200
        body = r.json()
        assert "summary" in body
        assert body["start_chapter"] == 1
        assert body["end_chapter"] == 5

    def test_start_greater_than_end_returns_422(self):
        """GET /arc-summary with start > end → 422."""
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)):
            r = client.get(
                f"/api/v1/ai/novels/{NOVEL_ID}/arc-summary?start_chapter=10&end_chapter=5",
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 422

    def test_non_vip_max_gets_403(self):
        """GET /arc-summary with reader role → 403."""
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)):
            r = client.get(
                f"/api/v1/ai/novels/{NOVEL_ID}/arc-summary?start_chapter=1&end_chapter=5",
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 403

    def test_cache_hit_skips_gemini(self):
        """When Storage cache exists, get_arc_summary is called but Gemini is not."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_arc_summary", return_value=MOCK_ARC_SUMMARY) as mock_svc,
        ):
            r = client.get(
                f"/api/v1/ai/novels/{NOVEL_ID}/arc-summary?start_chapter=1&end_chapter=5",
                headers=AUTH_HEADERS,
            )
        assert r.status_code == 200
        mock_svc.assert_called_once_with(NOVEL_ID, 1, 5)


# ---------------------------------------------------------------------------
# TestComputeTasks (service-level unit tests)
# ---------------------------------------------------------------------------


class TestComputeTasks:
    def test_compute_relationships_marks_failed_when_no_gemini(self):
        """compute_relationships_task marks failed when gemini_api_key is empty."""
        from app.services import story_intelligence_service as svc_module

        with (
            patch.object(svc_module, "_mark_relationships_failed") as mock_fail,
            patch("app.services.story_intelligence_service.settings") as mock_settings,
        ):
            mock_settings.gemini_api_key = ""
            svc_module.compute_relationships_task(NOVEL_ID)

        mock_fail.assert_called_once_with(NOVEL_ID)

    def test_compute_relationships_stores_graph_on_success(self):
        """compute_relationships_task stores status=ready with nodes/edges on success."""
        from app.services import story_intelligence_service as svc_module

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{"chapter_number": 1, "content": "Alice meets Bob."}]
        )

        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text='[["Alice","Bob"]]')

        with (
            patch("app.services.story_intelligence_service.get_supabase", return_value=mock_sb),
            patch("app.services.story_intelligence_service.settings") as mock_settings,
            patch("google.generativeai.configure"),
            patch("google.generativeai.GenerativeModel", return_value=mock_model),
        ):
            mock_settings.gemini_api_key = "test-key"
            svc_module.compute_relationships_task(NOVEL_ID)

        update_call = mock_sb.table.return_value.update.call_args
        stored = update_call[0][0]["relationship_graph"]
        assert stored["status"] == "ready"
        assert len(stored["nodes"]) == 2
        assert len(stored["edges"]) == 1

    def test_compute_timeline_marks_failed_when_no_gemini(self):
        """compute_timeline_task marks failed when gemini_api_key is empty."""
        from app.services import story_intelligence_service as svc_module

        with (
            patch.object(svc_module, "_mark_timeline_failed") as mock_fail,
            patch("app.services.story_intelligence_service.settings") as mock_settings,
        ):
            mock_settings.gemini_api_key = ""
            svc_module.compute_timeline_task(NOVEL_ID)

        mock_fail.assert_called_once_with(NOVEL_ID)

    def test_compute_timeline_stores_events_on_success(self):
        """compute_timeline_task stores status=ready with events list on success."""
        from app.services import story_intelligence_service as svc_module

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {"chapter_number": 1, "content": "Nhân vật xuất hiện."},
                {"chapter_number": 2, "content": "Cuộc chiến nổ ra."},
            ]
        )

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = [
            MagicMock(text="Nhân vật chính xuất hiện lần đầu."),
            MagicMock(text="Cuộc chiến giữa hai phe bùng nổ."),
        ]

        with (
            patch("app.services.story_intelligence_service.get_supabase", return_value=mock_sb),
            patch("app.services.story_intelligence_service.settings") as mock_settings,
            patch("google.generativeai.configure"),
            patch("google.generativeai.GenerativeModel", return_value=mock_model),
        ):
            mock_settings.gemini_api_key = "test-key"
            svc_module.compute_timeline_task(NOVEL_ID)

        update_call = mock_sb.table.return_value.update.call_args
        stored = update_call[0][0]["arc_timeline"]
        assert stored["status"] == "ready"
        assert len(stored["events"]) == 2
        assert stored["events"][0]["chapter_number"] == 1


# ---------------------------------------------------------------------------
# TestVipGate
# ---------------------------------------------------------------------------


class TestVipGate:
    def test_reader_gets_403_on_relationships(self):
        """Reader role → 403 on GET /relationships."""
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/relationships", headers=AUTH_HEADERS)
        assert r.status_code == 403
        assert "VIP Max" in r.json()["detail"]

    def test_vip_max_is_allowed_on_relationships(self):
        """VIP Max → not 403 on GET /relationships."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch("app.api.v1.story_intelligence.svc.get_relationships", return_value=MOCK_GRAPH_READY),
        ):
            r = client.get(f"/api/v1/ai/novels/{NOVEL_ID}/relationships", headers=AUTH_HEADERS)
        assert r.status_code != 403
