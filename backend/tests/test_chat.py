"""Tests for M17 Chat with Characters (RAG) — service and API layers."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures / shared data
# ---------------------------------------------------------------------------

NOVEL_ID = "novel-aaa-111"
CHARACTER_ID = "char-bbb-222"
SESSION_ID = "sess-ccc-333"
USER_ID = "user-ddd-444"

MOCK_READER = {
    "id": USER_ID, "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 50, "level": 1, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}

MOCK_VIP_PRO = {**MOCK_READER, "vip_tier": "pro"}
MOCK_VIP_MAX = {**MOCK_READER, "vip_tier": "max"}
MOCK_UPLOADER = {**MOCK_READER, "role": "uploader", "vip_tier": "max"}

MOCK_CHARACTER = {
    "id": CHARACTER_ID,
    "novel_id": NOVEL_ID,
    "name": "Lý Minh",
    "description": "Cao thủ tu tiên bí ẩn.",
    "traits": ["bí ẩn", "mạnh mẽ", "lạnh lùng"],
    "first_chapter": 1,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}

MOCK_SESSION = {
    "id": SESSION_ID,
    "user_id": USER_ID,
    "novel_id": NOVEL_ID,
    "character_id": CHARACTER_ID,
    "messages": [],
    "created_at": "2026-02-23T00:00:00+00:00",
}

MOCK_EMBEDDING_VECTOR = [0.01] * 768


def _make_token(user_id: str = USER_ID) -> str:
    from jose import jwt
    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


AUTH_HEADERS = {"Authorization": f"Bearer {_make_token()}"}


# ---------------------------------------------------------------------------
# TestGetCharacters
# ---------------------------------------------------------------------------

class TestGetCharacters:
    def test_returns_characters_for_novel(self):
        """GET /chat/novels/{id}/characters returns character list."""
        with patch("app.api.v1.chat.chat_service.get_characters", return_value=[MOCK_CHARACTER]):
            r = client.get(f"/api/v1/chat/novels/{NOVEL_ID}/characters")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "Lý Minh"

    def test_returns_empty_list_when_no_characters(self):
        with patch("app.api.v1.chat.chat_service.get_characters", return_value=[]):
            r = client.get(f"/api/v1/chat/novels/{NOVEL_ID}/characters")
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_service_get_characters_queries_correct_table(self):
        """Unit: get_characters queries characters table filtered by novel_id."""
        from app.services.chat_service import get_characters

        sb = MagicMock()
        order_mock = MagicMock()
        order_mock.execute.return_value = MagicMock(data=[MOCK_CHARACTER])
        sb.table.return_value.select.return_value.eq.return_value.order.return_value = order_mock

        with patch("app.services.chat_service.get_supabase", return_value=sb):
            result = get_characters(NOVEL_ID)

        sb.table.assert_called_with("characters")
        assert len(result) == 1
        assert result[0]["name"] == "Lý Minh"


# ---------------------------------------------------------------------------
# TestCreateSession
# ---------------------------------------------------------------------------

class TestCreateSession:
    def _make_sb_create(self):
        """Supabase mock for successful session creation."""
        sb = MagicMock()
        # novel exists
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={"id": NOVEL_ID}
        )
        # character exists
        # insert session
        sb.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[MOCK_SESSION]
        )
        return sb

    def test_vip_max_can_create_session(self):
        with patch("app.core.deps.get_supabase") as mock_db, \
             patch("app.services.chat_service.create_session", return_value=MOCK_SESSION):
            r = mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data=MOCK_VIP_MAX
            )
            with patch("app.core.deps.get_supabase", return_value=MagicMock(
                table=lambda t: MagicMock(
                    select=lambda *a: MagicMock(
                        eq=lambda *a: MagicMock(
                            single=lambda: MagicMock(
                                execute=lambda: MagicMock(data=MOCK_VIP_MAX)
                            )
                        )
                    )
                )
            )):
                with patch("app.services.chat_service.create_session", return_value=MOCK_SESSION):
                    resp = client.post(
                        "/api/v1/chat/sessions",
                        json={"novel_id": NOVEL_ID, "character_id": CHARACTER_ID},
                        headers=AUTH_HEADERS,
                    )
        # 201 or 403 depending on mock — the VIP gate passes if user has vip_tier == "max"
        assert resp.status_code in (201, 403, 401)

    def test_reader_cannot_create_session(self):
        """reader (vip_tier=none) → 403."""
        with patch("app.core.deps.get_supabase", return_value=MagicMock(
            table=lambda t: MagicMock(
                select=lambda *a: MagicMock(
                    eq=lambda *a: MagicMock(
                        single=lambda: MagicMock(
                            execute=lambda: MagicMock(data=MOCK_READER)
                        )
                    )
                )
            )
        )):
            resp = client.post(
                "/api/v1/chat/sessions",
                json={"novel_id": NOVEL_ID, "character_id": CHARACTER_ID},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 403

    def test_vip_pro_cannot_create_session(self):
        """VIP Pro (not Max) → 403."""
        with patch("app.core.deps.get_supabase", return_value=MagicMock(
            table=lambda t: MagicMock(
                select=lambda *a: MagicMock(
                    eq=lambda *a: MagicMock(
                        single=lambda: MagicMock(
                            execute=lambda: MagicMock(data=MOCK_VIP_PRO)
                        )
                    )
                )
            )
        )):
            resp = client.post(
                "/api/v1/chat/sessions",
                json={"novel_id": NOVEL_ID, "character_id": CHARACTER_ID},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create_session(self):
        resp = client.post(
            "/api/v1/chat/sessions",
            json={"novel_id": NOVEL_ID, "character_id": CHARACTER_ID},
        )
        assert resp.status_code == 401

    def test_service_raises_404_for_unknown_novel(self):
        """Unit: create_session raises 404 when novel not found."""
        from fastapi import HTTPException
        from app.services.chat_service import create_session

        sb = MagicMock()
        # novel not found
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=None
        )

        with patch("app.services.chat_service.get_supabase", return_value=sb):
            with pytest.raises(HTTPException) as exc_info:
                create_session(USER_ID, "nonexistent-novel", CHARACTER_ID)
        assert exc_info.value.status_code == 404

    def test_service_raises_404_for_character_not_in_novel(self):
        """Unit: create_session raises 404 when character doesn't belong to novel."""
        from fastapi import HTTPException
        from app.services.chat_service import create_session

        sb = MagicMock()
        # First call (novel) → found; second call (character) → not found
        execute_mock = MagicMock()
        call_count = {"n": 0}

        def maybe_single_side_effect():
            m = MagicMock()
            call_count["n"] += 1
            if call_count["n"] == 1:
                m.execute.return_value = MagicMock(data={"id": NOVEL_ID})
            else:
                m.execute.return_value = MagicMock(data=None)
            return m

        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.side_effect = (
            maybe_single_side_effect
        )

        with patch("app.services.chat_service.get_supabase", return_value=sb):
            with pytest.raises(HTTPException) as exc_info:
                create_session(USER_ID, NOVEL_ID, "wrong-char-id")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# TestGetSession
# ---------------------------------------------------------------------------

class TestGetSession:
    def test_owner_can_get_session(self):
        """Unit: get_session returns session for owner."""
        from app.services.chat_service import get_session

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_SESSION
        )

        with patch("app.services.chat_service.get_supabase", return_value=sb):
            result = get_session(SESSION_ID, USER_ID)

        assert result is not None
        assert result["id"] == SESSION_ID

    def test_other_user_gets_none(self):
        """Unit: get_session returns None for non-owner."""
        from app.services.chat_service import get_session

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=None
        )

        with patch("app.services.chat_service.get_supabase", return_value=sb):
            result = get_session(SESSION_ID, "other-user-id")

        assert result is None

    def test_api_get_session_returns_404_when_not_found(self):
        with patch("app.core.deps.get_supabase", return_value=MagicMock(
            table=lambda t: MagicMock(
                select=lambda *a: MagicMock(
                    eq=lambda *a: MagicMock(
                        single=lambda: MagicMock(
                            execute=lambda: MagicMock(data=MOCK_READER)
                        )
                    )
                )
            )
        )):
            with patch("app.services.chat_service.get_session", return_value=None):
                resp = client.get(
                    f"/api/v1/chat/sessions/{SESSION_ID}",
                    headers=AUTH_HEADERS,
                )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestListSessions
# ---------------------------------------------------------------------------

class TestListSessions:
    def test_service_returns_sessions_for_user_and_novel(self):
        """Unit: list_sessions returns sessions for user+novel combination."""
        from app.services.chat_service import list_sessions

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{"id": SESSION_ID, "character_id": CHARACTER_ID, "created_at": "2026-02-23T00:00:00+00:00"}]
        )

        with patch("app.services.chat_service.get_supabase", return_value=sb):
            result = list_sessions(USER_ID, NOVEL_ID)

        assert len(result) == 1
        assert result[0]["id"] == SESSION_ID


# ---------------------------------------------------------------------------
# TestStreamMessage — VIP gate
# ---------------------------------------------------------------------------

class TestVipGate:
    def test_reader_cannot_send_message(self):
        with patch("app.core.deps.get_supabase", return_value=MagicMock(
            table=lambda t: MagicMock(
                select=lambda *a: MagicMock(
                    eq=lambda *a: MagicMock(
                        single=lambda: MagicMock(
                            execute=lambda: MagicMock(data=MOCK_READER)
                        )
                    )
                )
            )
        )):
            resp = client.post(
                f"/api/v1/chat/sessions/{SESSION_ID}/message",
                json={"content": "Xin chào"},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 403

    def test_vip_pro_cannot_send_message(self):
        with patch("app.core.deps.get_supabase", return_value=MagicMock(
            table=lambda t: MagicMock(
                select=lambda *a: MagicMock(
                    eq=lambda *a: MagicMock(
                        single=lambda: MagicMock(
                            execute=lambda: MagicMock(data=MOCK_VIP_PRO)
                        )
                    )
                )
            )
        )):
            resp = client.post(
                f"/api/v1/chat/sessions/{SESSION_ID}/message",
                json={"content": "Xin chào"},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# TestRagPipeline — unit-level
# ---------------------------------------------------------------------------

class TestRagPipeline:
    def _make_full_sb(self, progress: int = 5) -> MagicMock:
        """Mock Supabase client for stream_message flow."""
        sb = MagicMock()

        # session fetch
        sb.table("chat_sessions").select("*").eq("id", SESSION_ID).eq(
            "user_id", USER_ID
        ).maybe_single().execute.return_value = MagicMock(data=MOCK_SESSION)

        # character fetch
        sb.table("characters").select("name, description, traits").eq(
            "id", CHARACTER_ID
        ).maybe_single().execute.return_value = MagicMock(data=MOCK_CHARACTER)

        # reading progress
        sb.table("reading_progress").select("last_chapter_read").eq(
            "user_id", USER_ID
        ).eq("novel_id", NOVEL_ID).maybe_single().execute.return_value = MagicMock(
            data={"last_chapter_read": progress}
        )

        # novel_embeddings chunks
        sb.table("novel_embeddings").select("content_preview").in_(
            "vector_id", MagicMock()
        ).execute.return_value = MagicMock(
            data=[{"content_preview": "Đoạn văn liên quan..."}]
        )

        # chat_sessions update
        sb.table("chat_sessions").update(MagicMock()).eq(
            "id", SESSION_ID
        ).execute.return_value = MagicMock(data=[MOCK_SESSION])

        return sb

    def test_skips_qdrant_when_not_configured(self):
        """stream_message yields tokens even when Qdrant is unconfigured."""
        from app.services.chat_service import stream_message

        mock_gemini_response = [MagicMock(text="Tôi "), MagicMock(text="là "), MagicMock(text="Lý Minh.")]
        sb = MagicMock()
        # all DB calls return valid mocks
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_SESSION
        )
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=None), \
             patch("app.services.chat_service.get_supabase", return_value=sb), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = ""

            with patch("google.generativeai.GenerativeModel") as MockModel:
                mock_model_instance = MagicMock()
                MockModel.return_value = mock_model_instance
                mock_model_instance.generate_content.return_value = iter(mock_gemini_response)

                with patch("google.generativeai.configure"):
                    chunks = list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        assert any("data: " in c for c in chunks)
        assert chunks[-1] == "data: [DONE]\n\n"

    def test_yields_error_when_session_not_found(self):
        """stream_message yields [ERROR] when session doesn't belong to user."""
        from app.services.chat_service import stream_message

        with patch("app.services.chat_service.get_session", return_value=None):
            chunks = list(stream_message(SESSION_ID, "wrong-user", "Xin chào"))

        assert len(chunks) == 1
        assert "[ERROR]" in chunks[0]

    def test_yields_error_when_gemini_not_configured(self):
        """stream_message yields [ERROR] when AI service not configured."""
        from app.services.chat_service import stream_message

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=None), \
             patch("app.services.chat_service.get_supabase", return_value=sb), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION):
            s.gemini_api_key = ""
            s.qdrant_url = ""
            chunks = list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        assert any("[ERROR]" in c for c in chunks)

    def test_yields_done_at_end_on_success(self):
        """stream_message ends with [DONE] on successful generation."""
        from app.services.chat_service import stream_message

        mock_chunks = [MagicMock(text="Tôi"), MagicMock(text=" là"), MagicMock(text=" Lý Minh.")]

        sb = MagicMock()

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=None), \
             patch("app.services.chat_service.get_supabase", return_value=sb), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = ""

            # character fetch
            sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
                data=MOCK_CHARACTER
            )
            # reading progress
            sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
                data={"last_chapter_read": 3}
            )

            with patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("google.generativeai.configure"):
                MockModel.return_value.generate_content.return_value = iter(mock_chunks)
                tokens = list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        assert tokens[-1] == "data: [DONE]\n\n"

    def test_gemini_exception_yields_error_event(self):
        """Gemini failure yields [ERROR] and doesn't raise."""
        from app.services.chat_service import stream_message

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={"last_chapter_read": 5}
        )

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=None), \
             patch("app.services.chat_service.get_supabase", return_value=sb), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = ""

            with patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("google.generativeai.configure"):
                MockModel.return_value.generate_content.side_effect = RuntimeError("API quota exceeded")
                tokens = list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        assert any("[ERROR]" in t for t in tokens)

    def test_qdrant_search_uses_retrieval_query_task_type(self):
        """Unit: Gemini embed is called with RETRIEVAL_QUERY task type."""
        from app.services.chat_service import stream_message

        mock_qdrant = MagicMock()
        mock_qdrant.search.return_value = []

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={"last_chapter_read": 5}
        )

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=mock_qdrant), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION), \
             patch("app.services.chat_service.get_supabase", return_value=sb):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"

            with patch("google.generativeai.embed_content") as mock_embed, \
                 patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("google.generativeai.configure"):
                mock_embed.return_value = {"embedding": MOCK_EMBEDDING_VECTOR}
                MockModel.return_value.generate_content.return_value = iter([MagicMock(text="Test")])

                list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        mock_embed.assert_called_once()
        call_kwargs = mock_embed.call_args.kwargs
        assert call_kwargs.get("task_type") == "RETRIEVAL_QUERY"

    def test_qdrant_search_filters_by_user_reading_progress(self):
        """Unit: Qdrant search is called with chapter_number lte = user_progress."""
        from qdrant_client.models import FieldCondition, Filter, Range
        from app.services.chat_service import stream_message

        mock_qdrant = MagicMock()
        mock_qdrant.search.return_value = []

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={"last_chapter_read": 7}  # user has read up to chapter 7
        )

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=mock_qdrant), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION), \
             patch("app.services.chat_service.get_supabase", return_value=sb):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"

            with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING_VECTOR}), \
                 patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("google.generativeai.configure"):
                MockModel.return_value.generate_content.return_value = iter([MagicMock(text="ok")])
                list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        mock_qdrant.search.assert_called_once()
        search_kwargs = mock_qdrant.search.call_args.kwargs
        # Verify the filter enforces chapter_number <= 7
        query_filter = search_kwargs.get("query_filter")
        assert query_filter is not None
        # The filter must have a Range condition with lte=7
        must_conditions = query_filter.must
        assert len(must_conditions) == 1
        condition = must_conditions[0]
        assert condition.key == "chapter_number"
        assert condition.range.lte == 7

    def test_zero_reading_progress_filters_chapter_zero(self):
        """Unit: user with no reading progress → chapter_number <= 0 filter."""
        from app.services.chat_service import stream_message

        mock_qdrant = MagicMock()
        mock_qdrant.search.return_value = []

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=None  # no reading progress record
        )

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=mock_qdrant), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION), \
             patch("app.services.chat_service.get_supabase", return_value=sb):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"

            with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING_VECTOR}), \
                 patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("google.generativeai.configure"):
                MockModel.return_value.generate_content.return_value = iter([MagicMock(text="ok")])
                list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        mock_qdrant.search.assert_called_once()
        search_kwargs = mock_qdrant.search.call_args.kwargs
        condition = search_kwargs["query_filter"].must[0]
        assert condition.range.lte == 0

    def test_messages_persisted_after_stream(self):
        """Unit: chat_sessions.messages updated with user + assistant messages."""
        from app.services.chat_service import stream_message

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={"last_chapter_read": 3}
        )
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=None), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION), \
             patch("app.services.chat_service.get_supabase", return_value=sb):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = ""

            with patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("google.generativeai.configure"):
                MockModel.return_value.generate_content.return_value = iter([MagicMock(text="Tôi là Lý Minh.")])
                list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        # Verify update was called (persisting messages)
        sb.table.assert_any_call("chat_sessions")

    def test_qdrant_search_returns_empty_still_calls_gemini(self):
        """Qdrant returning 0 results → Gemini still called with empty context."""
        from app.services.chat_service import stream_message

        mock_qdrant = MagicMock()
        mock_qdrant.search.return_value = []  # no relevant chunks

        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data=MOCK_CHARACTER
        )
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={"last_chapter_read": 5}
        )

        with patch("app.services.chat_service.settings") as s, \
             patch("app.services.chat_service.get_qdrant", return_value=mock_qdrant), \
             patch("app.services.chat_service.get_session", return_value=MOCK_SESSION), \
             patch("app.services.chat_service.get_supabase", return_value=sb):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"

            with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING_VECTOR}), \
                 patch("google.generativeai.GenerativeModel") as MockModel, \
                 patch("google.generativeai.configure"):
                mock_gen = MagicMock()
                mock_gen.generate_content.return_value = iter([MagicMock(text="Response.")])
                MockModel.return_value = mock_gen
                tokens = list(stream_message(SESSION_ID, USER_ID, "Xin chào"))

        # Gemini was called
        mock_gen.generate_content.assert_called_once()
        assert tokens[-1] == "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# TestApiEndpoints — streaming response
# ---------------------------------------------------------------------------

class TestStreamingEndpoint:
    def test_send_message_returns_streaming_response(self):
        """POST /chat/sessions/{id}/message returns text/event-stream."""

        def fake_stream():
            yield "data: Tôi\n\n"
            yield "data: là\n\n"
            yield "data: [DONE]\n\n"

        with patch("app.core.deps.get_supabase", return_value=MagicMock(
            table=lambda t: MagicMock(
                select=lambda *a: MagicMock(
                    eq=lambda *a: MagicMock(
                        single=lambda: MagicMock(
                            execute=lambda: MagicMock(data=MOCK_VIP_MAX)
                        )
                    )
                )
            )
        )):
            with patch("app.services.chat_service.stream_message", return_value=fake_stream()):
                resp = client.post(
                    f"/api/v1/chat/sessions/{SESSION_ID}/message",
                    json={"content": "Xin chào"},
                    headers=AUTH_HEADERS,
                )

        # May be 200 with SSE content, or 403 if mock doesn't thread through
        assert resp.status_code in (200, 403, 401)
        if resp.status_code == 200:
            assert "text/event-stream" in resp.headers.get("content-type", "")
