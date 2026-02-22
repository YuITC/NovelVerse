"""Tests for VIP subscription and system settings API endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_token(user_id: str = "user-uuid", role: str = "reader") -> str:
    from jose import jwt
    from app.core.config import settings
    return jwt.encode({"sub": user_id, "role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")


MOCK_USER_READER = {
    "id": "user-uuid", "username": "reader_user", "avatar_url": None, "bio": None,
    "social_links": [], "donate_url": None, "role": "reader", "is_banned": False,
    "ban_until": None, "chapters_read": 0, "level": 0, "daily_nominations": 0,
    "nominations_reset_at": None, "vip_tier": "none", "vip_expires_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}

MOCK_USER_ADMIN = {
    **MOCK_USER_READER, "id": "admin-uuid", "username": "admin_user", "role": "admin",
}

MOCK_SETTINGS = [
    {"key": "vip_pro_price_vnd", "value": 99000},
    {"key": "vip_max_price_vnd", "value": 199000},
    {"key": "vip_pro_price_usd_cents", "value": 499},
    {"key": "vip_max_price_usd_cents", "value": 999},
    {"key": "vip_duration_days", "value": 30},
    {"key": "donation_commission_pct", "value": 10},
    {"key": "site_name", "value": "NovelVerse"},
    {"key": "maintenance_mode", "value": False},
]

MOCK_SUBSCRIPTION = {
    "id": "sub-uuid", "user_id": "user-uuid", "vip_tier": "pro",
    "payment_method": "bank_transfer", "status": "pending",
    "starts_at": None, "expires_at": None, "amount_paid": 99000,
    "created_at": "2026-02-22T00:00:00+00:00",
}

MOCK_ACTIVE_SUBSCRIPTION = {
    **MOCK_SUBSCRIPTION, "status": "active",
    "starts_at": "2026-02-22T00:00:00+00:00", "expires_at": "2026-03-24T00:00:00+00:00",
    "confirmed_by": "admin-uuid",
}


def _make_user_supabase_mock(user):
    r = MagicMock()
    r.data = user
    c = MagicMock()
    c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = r
    return c


class TestGetSettings:
    def test_get_settings_no_auth_returns_200(self):
        with patch("app.services.vip_service.get_supabase") as mock_sb:
            mc = MagicMock()
            mock_sb.return_value = mc
            sr = MagicMock()
            sr.data = MOCK_SETTINGS
            mc.table.return_value.select.return_value.execute.return_value = sr
            response = client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        assert "vip_pro_price_vnd" in data
        assert data["vip_pro_price_vnd"] == 99000

    def test_get_settings_returns_all_keys(self):
        with patch("app.services.vip_service.get_supabase") as mock_sb:
            mc = MagicMock()
            mock_sb.return_value = mc
            sr = MagicMock()
            sr.data = MOCK_SETTINGS
            mc.table.return_value.select.return_value.execute.return_value = sr
            response = client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        for key in ["vip_pro_price_vnd", "vip_max_price_vnd", "vip_pro_price_usd_cents",
                    "vip_max_price_usd_cents", "vip_duration_days", "donation_commission_pct",
                    "site_name", "maintenance_mode"]:
            assert key in data


class TestStripeCheckout:
    def test_checkout_requires_auth(self):
        response = client.post("/api/v1/vip/checkout", json={"tier": "pro"})
        assert response.status_code == 401

    def test_checkout_invalid_tier_returns_400(self):
        token = make_token()
        with patch("app.core.deps.get_supabase") as mock_sb:
            mock_sb.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            response = client.post(
                "/api/v1/vip/checkout",
                json={"tier": "diamond"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 400
        assert "Invalid VIP tier" in response.json()["detail"]

    def test_checkout_authenticated_with_mock_stripe_returns_200(self):
        token = make_token()
        mock_session = MagicMock()
        mock_session.id = "cs_test_session_id"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_session_id"
        with (patch("app.core.deps.get_supabase") as mock_dep_sb,
              patch("app.services.vip_service.get_supabase") as mock_svc_sb,
              patch("stripe.checkout.Session.create", return_value=mock_session)):
            mock_dep_sb.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            mock_svc_client = MagicMock()
            mock_svc_sb.return_value = mock_svc_client
            sr = MagicMock()
            sr.data = {"value": 499}
            mock_svc_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = sr
            ir = MagicMock()
            ir.data = [MOCK_SUBSCRIPTION]
            mock_svc_client.table.return_value.insert.return_value.execute.return_value = ir
            response = client.post(
                "/api/v1/vip/checkout",
                json={"tier": "pro"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        assert "url" in response.json()
        assert response.json()["url"] == "https://checkout.stripe.com/pay/cs_test_session_id"


class TestBankTransfer:
    def test_bank_transfer_requires_auth(self):
        response = client.post("/api/v1/vip/bank-transfer", json={"tier": "pro", "amount_paid": 99000})
        assert response.status_code == 401

    def test_bank_transfer_valid_data_returns_200(self):
        token = make_token()
        with (patch("app.core.deps.get_supabase") as mock_dep_sb,
              patch("app.services.vip_service.get_supabase") as mock_svc_sb):
            mock_dep_sb.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            mock_svc_client = MagicMock()
            mock_svc_sb.return_value = mock_svc_client
            ir = MagicMock()
            ir.data = [MOCK_SUBSCRIPTION]
            mock_svc_client.table.return_value.insert.return_value.execute.return_value = ir
            response = client.post(
                "/api/v1/vip/bank-transfer",
                json={"tier": "pro", "amount_paid": 99000},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["payment_method"] == "bank_transfer"
        assert data["vip_tier"] == "pro"

    def test_bank_transfer_invalid_tier_returns_400(self):
        token = make_token()
        with (patch("app.core.deps.get_supabase") as mock_dep_sb,
              patch("app.services.vip_service.get_supabase") as mock_svc_sb):
            mock_dep_sb.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            mock_svc_sb.return_value = MagicMock()
            response = client.post(
                "/api/v1/vip/bank-transfer",
                json={"tier": "platinum", "amount_paid": 99000},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 400
        assert "Invalid VIP tier" in response.json()["detail"]


class TestGetMySubscriptions:
    def test_get_my_subscriptions_requires_auth(self):
        response = client.get("/api/v1/vip/me")
        assert response.status_code == 401

    def test_get_my_subscriptions_returns_list(self):
        token = make_token()
        with (patch("app.core.deps.get_supabase") as mock_dep_sb,
              patch("app.services.vip_service.get_supabase") as mock_svc_sb):
            mock_dep_sb.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            mock_svc_client = MagicMock()
            mock_svc_sb.return_value = mock_svc_client
            lr = MagicMock()
            lr.data = [MOCK_SUBSCRIPTION]
            mock_svc_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = lr
            response = client.get("/api/v1/vip/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) and len(data) == 1
        assert data[0]["vip_tier"] == "pro"
        assert data[0]["status"] == "pending"

    def test_get_my_subscriptions_empty_list(self):
        token = make_token()
        with (patch("app.core.deps.get_supabase") as mock_dep_sb,
              patch("app.services.vip_service.get_supabase") as mock_svc_sb):
            mock_dep_sb.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            mock_svc_client = MagicMock()
            mock_svc_sb.return_value = mock_svc_client
            lr = MagicMock()
            lr.data = []
            mock_svc_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = lr
            response = client.get("/api/v1/vip/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == []


class TestStripeWebhook:
    def test_webhook_without_signature_returns_400(self):
        payload = bytes(chr(123) + chr(34) + "type" + chr(34) + ": " + chr(34) + "checkout.session.completed" + chr(34) + chr(125), "utf-8")
        response = client.post(
            "/api/v1/vip/webhook",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert "Missing Stripe signature" in response.json()["detail"]

    def test_webhook_with_invalid_signature_returns_400(self):
        payload = bytes(chr(123) + chr(34) + "type" + chr(34) + ": " + chr(34) + "checkout.session.completed" + chr(34) + chr(125), "utf-8")
        with patch("stripe.Webhook.construct_event", side_effect=Exception("Invalid signature")):
            response = client.post(
                "/api/v1/vip/webhook",
                content=payload,
                headers={"Content-Type": "application/json", "stripe-signature": "invalid_sig"},
            )
        assert response.status_code == 400


class TestAdminVipConfirm:
    def test_confirm_requires_admin_role(self):
        token = make_token(user_id="user-uuid", role="reader")
        with patch("app.core.deps.get_supabase") as mock_sb:
            mock_sb.return_value = _make_user_supabase_mock(MOCK_USER_READER)
            response = client.patch(
                "/api/v1/admin/vip/sub-uuid/confirm",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 403

    def test_confirm_as_admin_activates_subscription(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as mock_dep_sb,
              patch("app.services.vip_service.get_supabase") as mock_svc_sb,
              patch("app.services.vip_service._get_setting", return_value=30)):
            mock_dep_sb.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            mock_svc_client = MagicMock()
            mock_svc_sb.return_value = mock_svc_client
            sub_r = MagicMock()
            sub_r.data = MOCK_SUBSCRIPTION
            mock_svc_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = sub_r
            upd_r = MagicMock()
            upd_r.data = [MOCK_ACTIVE_SUBSCRIPTION]
            mock_svc_client.table.return_value.update.return_value.eq.return_value.execute.return_value = upd_r
            response = client.patch(
                "/api/v1/admin/vip/sub-uuid/confirm",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_confirm_nonexistent_subscription_returns_404(self):
        token = make_token(user_id="admin-uuid", role="admin")
        with (patch("app.core.deps.get_supabase") as mock_dep_sb,
              patch("app.services.vip_service.get_supabase") as mock_svc_sb):
            mock_dep_sb.return_value = _make_user_supabase_mock(MOCK_USER_ADMIN)
            mock_svc_client = MagicMock()
            mock_svc_sb.return_value = mock_svc_client
            nf_r = MagicMock()
            nf_r.data = None
            mock_svc_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = nf_r
            response = client.patch(
                "/api/v1/admin/vip/nonexistent-sub/confirm",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 404
        assert "Subscription not found" in response.json()["detail"]
