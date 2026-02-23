"""Tests for M18 AI Narrator TTS — service and API layers."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.tts_service import _chunk_text

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures / shared data
# ---------------------------------------------------------------------------

CHAPTER_ID = "chap-aaa-111"
USER_ID = "user-bbb-222"
NARRATION_ID = "narr-ccc-333"
AUDIO_URL = "https://storage.example.com/chapter-narrations/chapters/chap-aaa-111.mp3"
VOICE_ID = "test-voice-id"

MOCK_READER = {
    "id": USER_ID, "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 50, "level": 1, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}

MOCK_VIP_PRO = {**MOCK_READER, "vip_tier": "pro"}
MOCK_VIP_MAX = {**MOCK_READER, "vip_tier": "max"}

MOCK_NARRATION_PENDING = {
    "id": NARRATION_ID,
    "chapter_id": CHAPTER_ID,
    "status": "pending",
    "audio_url": None,
    "voice_id": VOICE_ID,
    "created_at": "2026-02-23T00:00:00+00:00",
    "updated_at": "2026-02-23T00:00:00+00:00",
}

MOCK_NARRATION_READY = {
    **MOCK_NARRATION_PENDING,
    "status": "ready",
    "audio_url": AUDIO_URL,
}

MOCK_NARRATION_FAILED = {
    **MOCK_NARRATION_PENDING,
    "status": "failed",
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
# TestGetNarration
# ---------------------------------------------------------------------------


class TestGetNarration:
    def test_returns_404_when_no_narration(self):
        """GET /tts/chapters/{id} → 404 when not yet generated."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)),
            patch("app.api.v1.tts.tts_service.get_narration", return_value=None),
        ):
            r = client.get(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 404

    def test_returns_pending_status(self):
        """GET returns pending narration."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)),
            patch("app.api.v1.tts.tts_service.get_narration", return_value=MOCK_NARRATION_PENDING),
        ):
            r = client.get(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "pending"
        assert body["audio_url"] is None

    def test_returns_ready_with_audio_url(self):
        """GET returns ready narration with audio_url populated."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)),
            patch("app.api.v1.tts.tts_service.get_narration", return_value=MOCK_NARRATION_READY),
        ):
            r = client.get(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ready"
        assert body["audio_url"] == AUDIO_URL

    def test_requires_auth(self):
        """GET requires authentication."""
        r = client.get(f"/api/v1/tts/chapters/{CHAPTER_ID}")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# TestRequestNarration
# ---------------------------------------------------------------------------


class TestRequestNarration:
    def test_vip_max_gets_202_for_new_narration(self):
        """POST with VIP Max creates new narration, returns 202."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch(
                "app.api.v1.tts.tts_service.request_narration",
                return_value=(MOCK_NARRATION_PENDING, True),
            ),
            patch("app.api.v1.tts.tts_service.generate_narration"),
        ):
            r = client.post(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 202
        body = r.json()
        assert body["status"] == "pending"

    def test_reader_gets_403(self):
        """POST with reader role → 403."""
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)):
            r = client.post(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 403

    def test_vip_pro_gets_403(self):
        """POST with VIP Pro → 403 (VIP Max required)."""
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_PRO)):
            r = client.post(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 403

    def test_already_pending_returns_200(self):
        """POST when already pending returns 200 (idempotent), no new background task."""
        generate_mock = MagicMock()
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch(
                "app.api.v1.tts.tts_service.request_narration",
                return_value=(MOCK_NARRATION_PENDING, False),
            ),
            patch("app.api.v1.tts.tts_service.generate_narration", generate_mock),
        ):
            r = client.post(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 200
        generate_mock.assert_not_called()

    def test_already_ready_returns_200(self):
        """POST when already ready returns 200 with audio_url."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch(
                "app.api.v1.tts.tts_service.request_narration",
                return_value=(MOCK_NARRATION_READY, False),
            ),
        ):
            r = client.post(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 200
        assert r.json()["audio_url"] == AUDIO_URL

    def test_chapter_not_found_returns_404(self):
        """POST when chapter doesn't exist → 404."""
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch(
                "app.api.v1.tts.tts_service.request_narration",
                side_effect=ValueError("Chapter not found"),
            ),
        ):
            r = client.post(f"/api/v1/tts/chapters/nonexistent-id", headers=AUTH_HEADERS)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# TestGenerateNarration
# ---------------------------------------------------------------------------


class TestGenerateNarration:
    def test_skips_gracefully_when_not_configured(self):
        """generate_narration marks failed if ElevenLabs keys not set."""
        from app.services import tts_service

        with (
            patch.object(tts_service, "_mark_failed") as mock_fail,
            patch("app.services.tts_service.settings") as mock_settings,
        ):
            mock_settings.elevenlabs_api_key = ""
            mock_settings.elevenlabs_voice_id = ""
            tts_service.generate_narration(CHAPTER_ID)

        mock_fail.assert_called_once_with(CHAPTER_ID)

    def test_calls_elevenlabs_with_correct_headers(self):
        """generate_narration sends xi-api-key header and eleven_multilingual_v2 model."""
        from app.services import tts_service

        mock_chapter = MagicMock()
        mock_chapter.data = {"content": "Hello world"}
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_chapter
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
        mock_supabase.storage.from_.return_value.get_public_url.return_value = AUDIO_URL

        mock_resp = MagicMock()
        mock_resp.content = b"MP3_BYTES"
        mock_resp.raise_for_status = MagicMock()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = mock_resp

        with (
            patch("app.services.tts_service.get_supabase", return_value=mock_supabase),
            patch("app.services.tts_service.settings") as mock_settings,
            patch("app.services.tts_service.httpx.Client", return_value=mock_http),
        ):
            mock_settings.elevenlabs_api_key = "test-key"
            mock_settings.elevenlabs_voice_id = VOICE_ID
            tts_service.generate_narration(CHAPTER_ID)

        call_kwargs = mock_http.post.call_args
        assert call_kwargs is not None
        headers = call_kwargs[1]["headers"]
        assert headers["xi-api-key"] == "test-key"
        payload = call_kwargs[1]["json"]
        assert payload["model_id"] == "eleven_multilingual_v2"

    def test_uploads_to_correct_storage_path(self):
        """generate_narration uploads to chapters/{chapter_id}.mp3 in Storage."""
        from app.services import tts_service

        mock_chapter = MagicMock()
        mock_chapter.data = {"content": "Short content"}
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_chapter
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase.storage.from_.return_value.get_public_url.return_value = AUDIO_URL

        mock_resp = MagicMock()
        mock_resp.content = b"MP3_BYTES"
        mock_resp.raise_for_status = MagicMock()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = mock_resp

        with (
            patch("app.services.tts_service.get_supabase", return_value=mock_supabase),
            patch("app.services.tts_service.settings") as mock_settings,
            patch("app.services.tts_service.httpx.Client", return_value=mock_http),
        ):
            mock_settings.elevenlabs_api_key = "test-key"
            mock_settings.elevenlabs_voice_id = VOICE_ID
            tts_service.generate_narration(CHAPTER_ID)

        upload_call = mock_supabase.storage.from_.return_value.upload.call_args
        assert upload_call[1]["path"] == f"chapters/{CHAPTER_ID}.mp3"

    def test_updates_db_to_ready_with_audio_url(self):
        """generate_narration updates chapter_narrations to status=ready."""
        from app.services import tts_service

        mock_chapter = MagicMock()
        mock_chapter.data = {"content": "Content here"}
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_chapter
        mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
        mock_supabase.storage.from_.return_value.get_public_url.return_value = AUDIO_URL

        mock_resp = MagicMock()
        mock_resp.content = b"MP3_BYTES"
        mock_resp.raise_for_status = MagicMock()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = mock_resp

        with (
            patch("app.services.tts_service.get_supabase", return_value=mock_supabase),
            patch("app.services.tts_service.settings") as mock_settings,
            patch("app.services.tts_service.httpx.Client", return_value=mock_http),
        ):
            mock_settings.elevenlabs_api_key = "test-key"
            mock_settings.elevenlabs_voice_id = VOICE_ID
            tts_service.generate_narration(CHAPTER_ID)

        update_call = mock_supabase.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "ready"
        assert update_data["audio_url"] == AUDIO_URL

    def test_elevenlabs_error_marks_failed_without_raising(self):
        """ElevenLabs failure → marks status=failed, does not raise."""
        from app.services import tts_service

        mock_chapter = MagicMock()
        mock_chapter.data = {"content": "Some content"}
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_chapter

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.side_effect = Exception("ElevenLabs unavailable")

        with (
            patch("app.services.tts_service.get_supabase", return_value=mock_supabase),
            patch("app.services.tts_service.settings") as mock_settings,
            patch("app.services.tts_service.httpx.Client", return_value=mock_http),
            patch.object(tts_service, "_mark_failed") as mock_fail,
        ):
            mock_settings.elevenlabs_api_key = "test-key"
            mock_settings.elevenlabs_voice_id = VOICE_ID
            tts_service.generate_narration(CHAPTER_ID)  # must not raise

        mock_fail.assert_called_once_with(CHAPTER_ID)

    def test_long_content_makes_multiple_elevenlabs_calls(self):
        """Content >4500 chars → chunked into multiple ElevenLabs API calls."""
        from app.services import tts_service

        long_content = "Line\n" * 2000  # ~10000 chars

        mock_chapter = MagicMock()
        mock_chapter.data = {"content": long_content}
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_chapter
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
        mock_supabase.storage.from_.return_value.get_public_url.return_value = AUDIO_URL

        mock_resp = MagicMock()
        mock_resp.content = b"CHUNK"
        mock_resp.raise_for_status = MagicMock()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = mock_resp

        with (
            patch("app.services.tts_service.get_supabase", return_value=mock_supabase),
            patch("app.services.tts_service.settings") as mock_settings,
            patch("app.services.tts_service.httpx.Client", return_value=mock_http),
        ):
            mock_settings.elevenlabs_api_key = "test-key"
            mock_settings.elevenlabs_voice_id = VOICE_ID
            tts_service.generate_narration(CHAPTER_ID)

        assert mock_http.post.call_count >= 2


# ---------------------------------------------------------------------------
# TestChunkText
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_short_content_single_chunk(self):
        text = "Hello world\nSecond line"
        chunks = _chunk_text(text, max_chars=4500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_content_multiple_chunks(self):
        line = "A" * 100
        text = "\n".join([line] * 100)  # 100 lines × 100 chars ≈ 10100 chars
        chunks = _chunk_text(text, max_chars=4500)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 4600  # allow slight overshoot for last line

    def test_splits_at_line_boundaries(self):
        """Chunks must not split any individual line."""
        lines = [f"Line number {i}" for i in range(200)]
        text = "\n".join(lines)
        chunks = _chunk_text(text, max_chars=1000)
        reconstructed = "\n".join(chunks)
        for line in lines:
            assert line in reconstructed


# ---------------------------------------------------------------------------
# TestVipGate
# ---------------------------------------------------------------------------


class TestVipGate:
    def test_reader_cannot_request_narration(self):
        with patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_READER)):
            r = client.post(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 403
        assert "VIP Max" in r.json()["detail"]

    def test_vip_max_can_request_narration(self):
        with (
            patch("app.core.deps.get_supabase", return_value=_deps_supabase(MOCK_VIP_MAX)),
            patch(
                "app.api.v1.tts.tts_service.request_narration",
                return_value=(MOCK_NARRATION_PENDING, True),
            ),
            patch("app.api.v1.tts.tts_service.generate_narration"),
        ):
            r = client.post(f"/api/v1/tts/chapters/{CHAPTER_ID}", headers=AUTH_HEADERS)
        assert r.status_code == 202
