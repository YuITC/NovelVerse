"""Tests for rate limiting middleware."""
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRateLimit:
    def test_rate_limit_skipped_without_redis(self):
        """Rate limiter should be a no-op when Redis is not configured."""
        with patch("app.core.rate_limit.get_redis", return_value=None):
            r = client.get("/api/v1/health")
        assert r.status_code == 200

    def test_rate_limit_allows_under_limit(self):
        """Rate limiter should allow requests under the limit."""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [None, None, 50, None]  # count=50 < 100
        with patch("app.core.rate_limit.get_redis", return_value=mock_redis):
            r = client.get("/api/v1/health")
        assert r.status_code == 200

    def test_rate_limit_blocks_over_limit(self):
        """Rate limiter should return 429 when limit exceeded."""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [None, None, 101, None]  # count=101 > 100
        with patch("app.core.rate_limit.get_redis", return_value=mock_redis):
            r = client.get("/api/v1/health")
        assert r.status_code == 429
        assert "Rate limit" in r.json()["detail"]
        assert r.headers.get("Retry-After") == "60"
