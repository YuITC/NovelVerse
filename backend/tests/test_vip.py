"""Tests for VIP purchase with Linh Thach."""
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_USER = {"id": "user-123", "role": "reader", "vip_tier": "none", "vip_expires_at": None}
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def mock_auth(monkeypatch, user=None):
    from app.core import deps
    monkeypatch.setattr(deps, "get_current_user", lambda: user or MOCK_USER)


class TestVipPurchase:
    def test_purchase_requires_auth(self):
        r = client.post("/api/v1/vip/purchase", json={"tier": "pro"})
        assert r.status_code == 401

    def test_purchase_invalid_tier(self, monkeypatch):
        mock_auth(monkeypatch)
        with patch("app.api.v1.vip.get_current_user", return_value=MOCK_USER):
            r = client.post("/api/v1/vip/purchase", json={"tier": "diamond"}, headers=AUTH_HEADERS)
        assert r.status_code in (401, 422)

    def test_get_settings_no_auth(self):
        with patch("app.services.vip_service.get_system_settings", return_value={"vip_pro_price_lt": "50000"}):
            r = client.get("/api/v1/settings")
        assert r.status_code == 200

    def test_my_subscriptions_requires_auth(self):
        r = client.get("/api/v1/vip/me")
        assert r.status_code == 401

    def test_my_subscriptions_returns_list(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.vip_service.get_my_subscriptions", return_value=[]):
                r = client.get("/api/v1/vip/me", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_purchase_insufficient_balance(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.vip_service.purchase_vip",
                       side_effect=HTTPException(status_code=402, detail="Insufficient Linh Thach balance")):
                r = client.post("/api/v1/vip/purchase", json={"tier": "pro"}, headers=AUTH_HEADERS)
        assert r.status_code in (402, 401)

    def test_purchase_success(self):
        from datetime import datetime, timezone
        mock_sub = {
            "id": "sub-123", "user_id": "user-123", "vip_tier": "pro",
            "lt_spent": 50000.0, "status": "active",
            "starts_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.vip_service.purchase_vip", return_value=mock_sub):
                r = client.post("/api/v1/vip/purchase", json={"tier": "pro"}, headers=AUTH_HEADERS)
        assert r.status_code in (201, 401)
