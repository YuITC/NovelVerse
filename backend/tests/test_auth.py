"""Tests for JWT auth middleware and /auth/me endpoint."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_valid_token(user_id: str = "test-user-uuid") -> str:
    """Generate a real JWT signed with the configured secret (for unit tests)."""
    from jose import jwt
    from app.core.config import settings

    return jwt.encode(
        {"sub": user_id, "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )


MOCK_USER = {
    "id": "test-user-uuid",
    "username": "Test User",
    "avatar_url": None,
    "bio": None,
    "social_links": [],
    "donate_url": None,
    "role": "reader",
    "is_banned": False,
    "ban_until": None,
    "chapters_read": 0,
    "level": 0,
    "daily_nominations": 0,
    "nominations_reset_at": None,
    "vip_tier": "none",
    "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuthMiddleware:
    def test_missing_token_returns_401(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 401

    def test_valid_token_returns_user(self):
        token = make_valid_token()
        mock_result = MagicMock()
        mock_result.data = MOCK_USER

        with patch("app.core.deps.get_supabase") as mock_supabase:
            mock_client = MagicMock()
            mock_supabase.return_value = mock_client
            mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_result

            response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-uuid"
        assert data["username"] == "Test User"

    def test_banned_user_returns_403(self):
        token = make_valid_token()
        banned_user = {**MOCK_USER, "is_banned": True, "ban_until": None}
        mock_result = MagicMock()
        mock_result.data = banned_user

        with patch("app.core.deps.get_supabase") as mock_supabase:
            mock_client = MagicMock()
            mock_supabase.return_value = mock_client
            mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_result

            response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403


class TestUserEndpoints:
    def test_get_user_not_found(self):
        mock_result = MagicMock()
        mock_result.data = None

        with patch("app.services.user_service.get_supabase") as mock_supabase:
            mock_client = MagicMock()
            mock_supabase.return_value = mock_client
            mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_result

            response = client.get("/api/v1/users/nonexistent-id")

        assert response.status_code == 404

    def test_update_me_requires_auth(self):
        response = client.patch("/api/v1/users/me", json={"bio": "Hello"})
        assert response.status_code == 401
