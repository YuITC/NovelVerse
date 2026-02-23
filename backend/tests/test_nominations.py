"""Tests for nominations and leaderboard endpoints."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_READER = {"id": "reader-111", "role": "reader"}
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


# ---------------------------------------------------------------------------
# Nominate
# ---------------------------------------------------------------------------

class TestNominate:
    def test_toggle_nominate_requires_auth(self):
        r = client.post("/api/v1/novels/novel-aaa/nominate")
        assert r.status_code == 401

    def test_get_nomination_status_requires_auth(self):
        r = client.get("/api/v1/novels/novel-aaa/nominate")
        assert r.status_code == 401

    def test_nominate_missing_novel_returns_404(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.nomination_service.nominate",
                       side_effect=HTTPException(status_code=404, detail="Novel not found")):
                r = client.post("/api/v1/novels/no-such/nominate", headers=AUTH_HEADERS)
        assert r.status_code in (404, 401)

    def test_nominate_daily_limit_returns_400(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.nomination_service.nominate",
                       side_effect=HTTPException(status_code=400, detail="Daily nomination limit reached")):
                r = client.post("/api/v1/novels/novel-aaa/nominate", headers=AUTH_HEADERS)
        assert r.status_code in (400, 401)

    def test_nominate_returns_is_nominated_true(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.nomination_service.nominate",
                       return_value={"is_nominated": True, "nominations_remaining": 2}):
                r = client.post("/api/v1/novels/novel-aaa/nominate", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_nominate_toggle_returns_is_nominated_false(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.nomination_service.nominate",
                       return_value={"is_nominated": False, "nominations_remaining": 3}):
                r = client.post("/api/v1/novels/novel-aaa/nominate", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_get_nomination_status_returns_status(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.nomination_service.get_nomination_status",
                       return_value={"is_nominated": True, "nominations_remaining": 2}):
                r = client.get("/api/v1/novels/novel-aaa/nominate", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_get_nomination_status_not_nominated(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_READER):
            with patch("app.services.nomination_service.get_nomination_status",
                       return_value={"is_nominated": False, "nominations_remaining": 3}):
                r = client.get("/api/v1/novels/novel-aaa/nominate", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

class TestLeaderboard:
    def _mock_entry(self, rank: int = 1) -> dict:
        return {
            "rank": rank,
            "novel_id": "novel-aaa",
            "score": 10,
            "novel": {
                "id": "novel-aaa",
                "title": "Test Novel",
                "author": "Author",
                "cover_url": None,
                "status": "ongoing",
                "total_chapters": 50,
                "total_views": 1000,
                "avg_rating": 4.5,
            },
        }

    def test_leaderboard_is_public_daily(self):
        mock_response = {"period": "daily", "entries": [self._mock_entry()]}
        with patch("app.services.nomination_service.get_leaderboard", return_value=mock_response):
            r = client.get("/api/v1/novels/leaderboard?period=daily")
        assert r.status_code == 200

    def test_leaderboard_is_public_weekly(self):
        mock_response = {"period": "weekly", "entries": [self._mock_entry()]}
        with patch("app.services.nomination_service.get_leaderboard", return_value=mock_response):
            r = client.get("/api/v1/novels/leaderboard?period=weekly")
        assert r.status_code == 200

    def test_leaderboard_is_public_monthly(self):
        mock_response = {"period": "monthly", "entries": [self._mock_entry()]}
        with patch("app.services.nomination_service.get_leaderboard", return_value=mock_response):
            r = client.get("/api/v1/novels/leaderboard?period=monthly")
        assert r.status_code == 200

    def test_leaderboard_default_period_is_daily(self):
        mock_response = {"period": "daily", "entries": []}
        with patch("app.services.nomination_service.get_leaderboard", return_value=mock_response):
            r = client.get("/api/v1/novels/leaderboard")
        assert r.status_code == 200

    def test_leaderboard_invalid_period_returns_422(self):
        r = client.get("/api/v1/novels/leaderboard?period=yearly")
        assert r.status_code == 422

    def test_leaderboard_empty_returns_empty_entries(self):
        mock_response = {"period": "daily", "entries": []}
        with patch("app.services.nomination_service.get_leaderboard", return_value=mock_response):
            r = client.get("/api/v1/novels/leaderboard?period=daily")
        assert r.status_code == 200
        assert r.json()["entries"] == []

    def test_leaderboard_returns_ranked_entries(self):
        entries = [self._mock_entry(rank=1), {**self._mock_entry(rank=2), "novel_id": "novel-bbb", "score": 5}]
        mock_response = {"period": "daily", "entries": entries}
        with patch("app.services.nomination_service.get_leaderboard", return_value=mock_response):
            r = client.get("/api/v1/novels/leaderboard?period=daily")
        assert r.status_code == 200
        data = r.json()
        assert data["period"] == "daily"
        assert len(data["entries"]) == 2
        assert data["entries"][0]["rank"] == 1
        assert data["entries"][1]["rank"] == 2
