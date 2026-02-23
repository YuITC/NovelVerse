"""Tests for M16 AI infrastructure: embedding pipeline + character extraction."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_UPLOADER = {
    "id": "uploader-123", "username": "uploader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "uploader", "is_banned": False,
    "ban_until": None, "chapters_read": 0, "level": 0, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}

MOCK_CHAPTER_DB = {
    "id": "chapter-uuid-1",
    "novel_id": "novel-uuid-1",
    "chapter_number": 5,
    "content": (
        "Lý Minh bước vào đại điện, đôi mắt sắc bén quét qua từng góc.\n\n"
        "Trương Vân đứng ở góc phòng, mặt lạnh như băng."
    ),
    "status": "published",
    "is_deleted": False,
}

MOCK_CHAPTER_RESPONSE = {
    "id": "chapter-uuid-1",
    "novel_id": "novel-uuid-1",
    "chapter_number": 5,
    "title": None,
    "word_count": 50,
    "status": "published",
    "publish_at": None,
    "published_at": "2026-02-23T00:00:00+00:00",
    "views": 0,
    "created_at": "2026-02-23T00:00:00+00:00",
    "updated_at": "2026-02-23T00:00:00+00:00",
}

MOCK_EMBEDDING_VECTOR = [0.1] * 768

MOCK_GEMINI_CHARACTERS = [
    {"name": "Lý Minh", "description": "Cao thủ tu tiên.", "traits": ["bí ẩn", "mạnh mẽ"]},
    {"name": "Trương Vân", "description": "Kiếm khách.", "traits": ["lạnh lùng", "nhanh"]},
]


def _make_token(user_id: str = "uploader-123") -> str:
    """Generate a valid JWT for tests using the app's JWT secret."""
    from jose import jwt
    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


def _make_user_supabase_mock(user: dict) -> MagicMock:
    """Return a Supabase mock that yields `user` on the user-fetch chain."""
    r = MagicMock()
    r.data = user
    c = MagicMock()
    c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = r
    return c


# ── Unit: _chunk_content ─────────────────────────────────────────────────────

class TestChunkContent:
    def test_empty_string_returns_empty_list(self):
        from app.services.embedding_service import _chunk_content
        assert _chunk_content("") == []

    def test_whitespace_only_returns_empty_list(self):
        from app.services.embedding_service import _chunk_content
        assert _chunk_content("   \n\n   ") == []

    def test_single_short_paragraph_is_one_chunk(self):
        from app.services.embedding_service import _chunk_content
        text = "Đây là một đoạn văn ngắn."
        assert _chunk_content(text) == [text]

    def test_multiple_short_paragraphs_merged_into_one_chunk(self):
        from app.services.embedding_service import _chunk_content
        text = "Đoạn 1.\n\nĐoạn 2.\n\nĐoạn 3."
        chunks = _chunk_content(text)
        assert len(chunks) == 1
        assert "Đoạn 1." in chunks[0] and "Đoạn 3." in chunks[0]

    def test_oversized_paragraph_splits_into_multiple_chunks(self):
        from app.services.embedding_service import _chunk_content
        long_para = "A" * 2000
        chunks = _chunk_content(long_para)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 1500

    def test_chunks_have_no_empty_strings(self):
        from app.services.embedding_service import _chunk_content
        text = "\n\n".join(["Para " + str(i) for i in range(20)])
        chunks = _chunk_content(text)
        assert all(c.strip() for c in chunks)


# ── Unit: embed_chapter — graceful skip ──────────────────────────────────────

class TestEmbedChapterGracefulSkip:
    def test_skips_when_gemini_not_configured(self):
        with patch("app.services.embedding_service.settings") as s:
            s.gemini_api_key = ""
            s.qdrant_url = "http://localhost:6333"
            from app.services.embedding_service import embed_chapter
            embed_chapter(chapter_id="c1", novel_id="n1")  # must not raise

    def test_skips_when_qdrant_not_configured(self):
        with patch("app.services.embedding_service.settings") as s:
            s.gemini_api_key = "fake-key"
            s.qdrant_url = ""
            from app.services.embedding_service import embed_chapter
            embed_chapter(chapter_id="c1", novel_id="n1")

    def test_skips_when_qdrant_client_none(self):
        with patch("app.services.embedding_service.settings") as s, \
             patch("app.services.embedding_service.get_qdrant", return_value=None):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"
            from app.services.embedding_service import embed_chapter
            embed_chapter(chapter_id="c1", novel_id="n1")


# ── Unit: embed_chapter — full pipeline ──────────────────────────────────────

class TestEmbedChapterPipeline:
    def _make_sb(self):
        sb = MagicMock()
        sb.table("chapters").select().eq().maybe_single().execute.return_value = MagicMock(data=MOCK_CHAPTER_DB)
        sb.table("novel_embeddings").upsert().execute.return_value = MagicMock(data=[])
        return sb

    def test_full_pipeline_calls_qdrant_upsert(self):
        mock_sb = self._make_sb()
        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []

        with patch("app.services.embedding_service.settings") as s, \
             patch("app.services.embedding_service.get_supabase", return_value=mock_sb), \
             patch("app.services.embedding_service.get_qdrant", return_value=mock_qdrant), \
             patch("app.services.embedding_service._embed_texts", return_value=[MOCK_EMBEDDING_VECTOR]):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"
            from app.services.embedding_service import embed_chapter
            embed_chapter(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1")

        mock_qdrant.create_collection.assert_called_once()
        mock_qdrant.upsert.assert_called_once()
        call_kwargs = mock_qdrant.upsert.call_args.kwargs
        assert call_kwargs["collection_name"] == "novel_novel-uuid-1"

    def test_existing_collection_not_recreated(self):
        mock_sb = self._make_sb()
        mock_qdrant = MagicMock()
        col = MagicMock()
        col.name = "novel_novel-uuid-1"
        mock_qdrant.get_collections.return_value.collections = [col]

        with patch("app.services.embedding_service.settings") as s, \
             patch("app.services.embedding_service.get_supabase", return_value=mock_sb), \
             patch("app.services.embedding_service.get_qdrant", return_value=mock_qdrant), \
             patch("app.services.embedding_service._embed_texts", return_value=[MOCK_EMBEDDING_VECTOR]):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"
            from app.services.embedding_service import embed_chapter
            embed_chapter(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1")

        mock_qdrant.create_collection.assert_not_called()

    def test_chapter_not_found_returns_early(self):
        sb = MagicMock()
        sb.table("chapters").select().eq().maybe_single().execute.return_value = MagicMock(data=None)
        mock_qdrant = MagicMock()

        with patch("app.services.embedding_service.settings") as s, \
             patch("app.services.embedding_service.get_supabase", return_value=sb), \
             patch("app.services.embedding_service.get_qdrant", return_value=mock_qdrant):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"
            from app.services.embedding_service import embed_chapter
            embed_chapter(chapter_id="missing", novel_id="novel-uuid-1")

        mock_qdrant.upsert.assert_not_called()

    def test_gemini_failure_does_not_propagate(self):
        mock_sb = self._make_sb()
        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []

        with patch("app.services.embedding_service.settings") as s, \
             patch("app.services.embedding_service.get_supabase", return_value=mock_sb), \
             patch("app.services.embedding_service.get_qdrant", return_value=mock_qdrant), \
             patch("app.services.embedding_service._embed_texts", side_effect=Exception("Gemini error")):
            s.gemini_api_key = "fake-key"
            s.qdrant_url = "http://localhost:6333"
            from app.services.embedding_service import embed_chapter
            embed_chapter(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1")  # must not raise


# ── Unit: extract_characters — graceful skip ─────────────────────────────────

class TestExtractCharactersGracefulSkip:
    def test_skips_when_gemini_not_configured(self):
        with patch("app.services.character_service.settings") as s:
            s.gemini_api_key = ""
            from app.services.character_service import extract_characters
            extract_characters(chapter_id="c1", novel_id="n1", chapter_number=1)


# ── Unit: extract_characters — full pipeline ─────────────────────────────────

class TestExtractCharactersPipeline:
    def _make_sb(self, existing=None):
        """Build a Supabase mock without calling insert/update during setup."""
        sb = MagicMock()
        # chapters fetch chain
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=MOCK_CHAPTER_DB)
        # characters select chain (extra .eq for name filter)
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=existing)
        # insert / update return values — set via .return_value, NOT by calling insert()/update()
        sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        return sb

    def test_inserts_new_characters(self):
        mock_sb = self._make_sb(existing=None)
        with patch("app.services.character_service.settings") as s, \
             patch("app.services.character_service.get_supabase", return_value=mock_sb), \
             patch("app.services.character_service._extract_from_gemini", return_value=MOCK_GEMINI_CHARACTERS):
            s.gemini_api_key = "fake-key"
            from app.services.character_service import extract_characters
            extract_characters(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1", chapter_number=5)

        assert mock_sb.table.return_value.insert.call_count == 2

    def test_updates_existing_character_preserves_lower_first_chapter(self):
        existing = {"id": "char-id", "first_chapter": 3}
        mock_sb = self._make_sb(existing=existing)
        with patch("app.services.character_service.settings") as s, \
             patch("app.services.character_service.get_supabase", return_value=mock_sb), \
             patch("app.services.character_service._extract_from_gemini", return_value=[MOCK_GEMINI_CHARACTERS[0]]):
            s.gemini_api_key = "fake-key"
            from app.services.character_service import extract_characters
            extract_characters(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1", chapter_number=5)

        mock_sb.table.return_value.update.assert_called_once()
        mock_sb.table.return_value.insert.assert_not_called()
        update_payload = mock_sb.table.return_value.update.call_args[0][0]
        assert "first_chapter" not in update_payload  # 3 < 5, so don't overwrite

    def test_updates_first_chapter_when_earlier(self):
        existing = {"id": "char-id", "first_chapter": 10}
        mock_sb = self._make_sb(existing=existing)
        with patch("app.services.character_service.settings") as s, \
             patch("app.services.character_service.get_supabase", return_value=mock_sb), \
             patch("app.services.character_service._extract_from_gemini", return_value=[MOCK_GEMINI_CHARACTERS[0]]):
            s.gemini_api_key = "fake-key"
            from app.services.character_service import extract_characters
            extract_characters(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1", chapter_number=2)

        update_payload = mock_sb.table.return_value.update.call_args[0][0]
        assert update_payload["first_chapter"] == 2

    def test_empty_content_skips_gemini(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={**MOCK_CHAPTER_DB, "content": ""}
        )
        with patch("app.services.character_service.settings") as s, \
             patch("app.services.character_service.get_supabase", return_value=sb), \
             patch("app.services.character_service._extract_from_gemini") as mock_gemini:
            s.gemini_api_key = "fake-key"
            from app.services.character_service import extract_characters
            extract_characters(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1", chapter_number=5)
        mock_gemini.assert_not_called()

    def test_gemini_returns_empty_list(self):
        mock_sb = self._make_sb()
        with patch("app.services.character_service.settings") as s, \
             patch("app.services.character_service.get_supabase", return_value=mock_sb), \
             patch("app.services.character_service._extract_from_gemini", return_value=[]):
            s.gemini_api_key = "fake-key"
            from app.services.character_service import extract_characters
            extract_characters(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1", chapter_number=5)
        mock_sb.table.return_value.insert.assert_not_called()

    def test_gemini_exception_does_not_propagate(self):
        mock_sb = self._make_sb()
        with patch("app.services.character_service.settings") as s, \
             patch("app.services.character_service.get_supabase", return_value=mock_sb), \
             patch("app.services.character_service._extract_from_gemini", side_effect=Exception("API error")):
            s.gemini_api_key = "fake-key"
            from app.services.character_service import extract_characters
            extract_characters(chapter_id="chapter-uuid-1", novel_id="novel-uuid-1", chapter_number=5)


# ── Integration: chapter publish → background tasks triggered ────────────────

class TestChapterPublishTriggersBackgroundTasks:
    def test_create_published_chapter_schedules_both_tasks(self):
        tok = _make_token(user_id="uploader-123")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.chapter_service.create_chapter", return_value=MOCK_CHAPTER_RESPONSE), \
             patch("app.services.embedding_service.embed_chapter") as mock_embed, \
             patch("app.services.character_service.extract_characters") as mock_extract:
            ms.return_value = _make_user_supabase_mock(MOCK_UPLOADER)
            r = client.post(
                "/api/v1/novels/novel-uuid-1/chapters",
                json={"chapter_number": 5, "content": "content", "status": "published"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert mock_embed.call_count == 1
        assert mock_extract.call_count == 1

    def test_create_draft_chapter_does_not_schedule_tasks(self):
        tok = _make_token(user_id="uploader-123")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.chapter_service.create_chapter", return_value={**MOCK_CHAPTER_RESPONSE, "status": "draft"}), \
             patch("app.services.embedding_service.embed_chapter") as mock_embed, \
             patch("app.services.character_service.extract_characters") as mock_extract:
            ms.return_value = _make_user_supabase_mock(MOCK_UPLOADER)
            r = client.post(
                "/api/v1/novels/novel-uuid-1/chapters",
                json={"chapter_number": 5, "content": "content", "status": "draft"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert mock_embed.call_count == 0
        assert mock_extract.call_count == 0

    def test_update_to_published_schedules_tasks(self):
        tok = _make_token(user_id="uploader-123")
        old_chapter = {**MOCK_CHAPTER_RESPONSE, "status": "draft"}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.chapter_service.get_chapter", return_value=old_chapter), \
             patch("app.services.chapter_service.update_chapter", return_value=MOCK_CHAPTER_RESPONSE), \
             patch("app.services.embedding_service.embed_chapter") as mock_embed, \
             patch("app.services.character_service.extract_characters") as mock_extract:
            ms.return_value = _make_user_supabase_mock(MOCK_UPLOADER)
            r = client.patch(
                "/api/v1/novels/novel-uuid-1/chapters/5",
                json={"status": "published"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 200
        assert mock_embed.call_count == 1
        assert mock_extract.call_count == 1

    def test_update_already_published_chapter_does_not_reschedule(self):
        """Editing an already-published chapter (e.g. fixing a typo) does not re-embed."""
        tok = _make_token(user_id="uploader-123")
        already_published = {**MOCK_CHAPTER_RESPONSE, "status": "published"}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.chapter_service.get_chapter", return_value=already_published), \
             patch("app.services.chapter_service.update_chapter", return_value=already_published), \
             patch("app.services.embedding_service.embed_chapter") as mock_embed, \
             patch("app.services.character_service.extract_characters") as mock_extract:
            ms.return_value = _make_user_supabase_mock(MOCK_UPLOADER)
            r = client.patch(
                "/api/v1/novels/novel-uuid-1/chapters/5",
                json={"title": "New title", "status": "published"},
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 200
        assert mock_embed.call_count == 0
        assert mock_extract.call_count == 0


# ── Integration: crawl publish → background tasks triggered ──────────────────

class TestCrawlPublishTriggersBackgroundTasks:
    def test_publish_queue_item_schedules_both_tasks(self):
        tok = _make_token(user_id="uploader-123")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.publish_queue_item", return_value=MOCK_CHAPTER_RESPONSE), \
             patch("app.services.embedding_service.embed_chapter") as mock_embed, \
             patch("app.services.character_service.extract_characters") as mock_extract:
            ms.return_value = _make_user_supabase_mock(MOCK_UPLOADER)
            r = client.post(
                "/api/v1/crawl/queue/queue-item-1/publish",
                headers={"Authorization": f"Bearer {tok}"},
            )
        assert r.status_code == 201
        assert mock_embed.call_count == 1
        assert mock_extract.call_count == 1


# ── Unit: get_qdrant client ───────────────────────────────────────────────────

class TestGetQdrantClient:
    def test_returns_none_when_url_not_configured(self):
        import app.core.qdrant as qdrant_module
        qdrant_module.get_qdrant.cache_clear()
        with patch.object(qdrant_module.settings, "qdrant_url", ""):
            result = qdrant_module.get_qdrant()
        qdrant_module.get_qdrant.cache_clear()
        assert result is None

    def test_returns_client_when_configured(self):
        import app.core.qdrant as qdrant_module
        mock_client = MagicMock()
        qdrant_module.get_qdrant.cache_clear()
        # QdrantClient is a deferred import inside get_qdrant(); patch at source module
        with patch.object(qdrant_module.settings, "qdrant_url", "http://localhost:6333"), \
             patch("qdrant_client.QdrantClient", return_value=mock_client):
            result = qdrant_module.get_qdrant()
        qdrant_module.get_qdrant.cache_clear()
        assert result is mock_client
