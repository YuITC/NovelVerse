from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_token(user_id=None, role=None):
    user_id = user_id or "uploader-uuid"
    role = role or "uploader"
    from jose import jwt

    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


NOVEL_ID = "novel-uuid-1"
SOURCE_ID = "source-uuid-1"
QUEUE_ITEM_ID = "queue-item-uuid-1"

MOCK_USER_READER = {
    "id": "reader-uuid", "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 0, "level": 0, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}
MOCK_USER_UPLOADER = {**MOCK_USER_READER, "id": "uploader-uuid", "username": "uploader_user", "role": "uploader"}
MOCK_USER_ADMIN = {**MOCK_USER_READER, "id": "admin-uuid", "username": "admin_user", "role": "admin"}

MOCK_CRAWL_SOURCE = {
    "id": SOURCE_ID, "novel_id": NOVEL_ID, "uploader_id": "uploader-uuid",
    "source_url": "https://biquge.info/book/12345/",
    "last_chapter": 0, "is_active": True, "created_at": "2026-01-01T00:00:00+00:00",
}

MOCK_QUEUE_ITEM = {
    "id": QUEUE_ITEM_ID, "crawl_source_id": SOURCE_ID, "novel_id": NOVEL_ID,
    "chapter_number": 1, "raw_content": "raw chapter content",
    "translated_content": None, "translation_method": None, "status": "crawled",
    "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00",
}

MOCK_QUEUE_ITEM_TRANSLATED = {
    **MOCK_QUEUE_ITEM, "translated_content": "Translated content",
    "translation_method": "opencc", "status": "translated",
}

MOCK_CHAPTER_RESULT = {
    "id": "chapter-uuid-1", "novel_id": NOVEL_ID, "chapter_number": 1,
    "title": None, "word_count": 100, "status": "published",
    "publish_at": None, "published_at": "2026-01-01T00:00:00+00:00",
    "views": 0, "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00",
}


def _make_user_supabase_mock(user):
    r = MagicMock(); r.data = user; c = MagicMock()
    c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = r
    return c


class TestListCrawlSources:
    def test_reader_gets_403(self):
        tok = make_token(user_id="reader-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.get("/api/v1/crawl/sources", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403

    def test_uploader_gets_200(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.get_crawl_sources", return_value=[MOCK_CRAWL_SOURCE]):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.get("/api/v1/crawl/sources", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 1
        assert data[0]["source_url"] == "https://biquge.info/book/12345/"


class TestCreateCrawlSource:
    def test_invalid_domain_returns_422(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post("/api/v1/crawl/sources",
                json={"novel_id": NOVEL_ID, "source_url": "https://evil.com/book/123/"},
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 422

    def test_valid_domain_returns_201(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.create_crawl_source", return_value=MOCK_CRAWL_SOURCE):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post("/api/v1/crawl/sources",
                json={"novel_id": NOVEL_ID, "source_url": "https://biquge.info/book/12345/"},
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 201
        assert r.json()["source_url"] == "https://biquge.info/book/12345/"

    def test_biquge_info_url_returns_201(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        biquge_source = {**MOCK_CRAWL_SOURCE, "source_url": "https://biquge.info/book/99999/"}
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.create_crawl_source", return_value=biquge_source):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post("/api/v1/crawl/sources",
                json={"novel_id": NOVEL_ID, "source_url": "https://biquge.info/book/99999/"},
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 201
        assert "biquge.info" in r.json()["source_url"]


class TestDeleteCrawlSource:
    def test_delete_source_uploader_returns_204(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.delete_crawl_source") as md:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.delete(f"/api/v1/crawl/sources/{SOURCE_ID}",
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 204
        md.assert_called_once_with(SOURCE_ID, "uploader-uuid")


class TestListCrawlQueue:
    def test_reader_gets_403(self):
        tok = make_token(user_id="reader-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            r = client.get("/api/v1/crawl/queue", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403

    def test_uploader_gets_200(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.get_crawl_queue", return_value=[MOCK_QUEUE_ITEM]):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.get("/api/v1/crawl/queue", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 1
        assert data[0]["status"] == "crawled"


class TestTranslateQueueItem:
    def test_invalid_method_returns_422(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post(f"/api/v1/crawl/queue/{QUEUE_ITEM_ID}/translate",
                json={"method": "invalid_method"},
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 422

    def test_opencc_translation_returns_200(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.translate_queue_item", return_value=MOCK_QUEUE_ITEM_TRANSLATED):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post(f"/api/v1/crawl/queue/{QUEUE_ITEM_ID}/translate",
                json={"method": "opencc"},
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        assert r.json()["status"] == "translated"
        assert r.json()["translation_method"] == "opencc"


class TestPublishQueueItem:
    def test_publish_item_returns_201(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.publish_queue_item", return_value=MOCK_CHAPTER_RESULT):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post(f"/api/v1/crawl/queue/{QUEUE_ITEM_ID}/publish",
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 201
        assert r.json()["chapter_number"] == 1


class TestSkipQueueItem:
    def test_skip_item_returns_204(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.services.crawl_service.skip_queue_item") as ms_skip:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.delete(f"/api/v1/crawl/queue/{QUEUE_ITEM_ID}",
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 204
        ms_skip.assert_called_once_with(QUEUE_ITEM_ID, "uploader-uuid")


class TestAdminCrawlTrigger:
    def test_non_admin_gets_403(self):
        tok = make_token(user_id="uploader-uuid", role="uploader")
        with patch("app.core.deps.get_supabase") as ms:
            ms.return_value = _make_user_supabase_mock(MOCK_USER_UPLOADER)
            r = client.post("/api/v1/admin/crawl/trigger",
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403

    def test_admin_gets_200_with_background_task(self):
        tok = make_token(user_id="admin-uuid", role="admin")
        with patch("app.core.deps.get_supabase") as ms, \
             patch("app.workers.crawl_worker.run_crawl_job"):
            ms.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            r = client.post("/api/v1/admin/crawl/trigger",
                headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        assert r.json()["message"] == "Crawl job started"
        assert "novel_id" in r.json()
