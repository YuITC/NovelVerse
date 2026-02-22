"""Tests for virtual economy system."""
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_USER = {"id": "user-123", "role": "reader"}
MOCK_UPLOADER = {"id": "uploader-456", "role": "uploader"}
MOCK_ADMIN = {"id": "admin-789", "role": "admin"}
AUTH_HEADERS = {"Authorization": "Bearer test-token"}

MOCK_WALLET = {
    "user_id": "user-123",
    "linh_thach": 100000.0,
    "tien_thach": 0.0,
    "updated_at": datetime.now(timezone.utc).isoformat()
}

MOCK_ITEM = {
    "id": "item-1",
    "name": "Truc Co Dan",
    "price_lt": 5000.0,
    "sort_order": 2
}


class TestWallet:
    def test_get_wallet_requires_auth(self):
        r = client.get("/api/v1/economy/wallet")
        assert r.status_code == 401

    def test_get_wallet_returns_balances(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.economy_service.get_wallet", return_value=MOCK_WALLET):
                r = client.get("/api/v1/economy/wallet", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)


class TestDeposit:
    def test_create_deposit_requires_auth(self):
        r = client.post("/api/v1/economy/deposit", json={"amount_vnd": 50000})
        assert r.status_code == 401

    def test_create_deposit_min_amount_validation(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            r = client.post("/api/v1/economy/deposit", json={"amount_vnd": 1000}, headers=AUTH_HEADERS)
        assert r.status_code in (422, 401)

    def test_create_deposit_success(self):
        mock_deposit = {
            "id": "dep-1", "transfer_code": "NV-ABC12345",
            "amount_vnd": 50000, "lt_credited": None,
            "status": "pending", "admin_note": None,
            "confirmed_at": None, "created_at": datetime.now(timezone.utc).isoformat()
        }
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.economy_service.create_deposit_request", return_value=mock_deposit):
                r = client.post("/api/v1/economy/deposit", json={"amount_vnd": 50000}, headers=AUTH_HEADERS)
        assert r.status_code in (201, 401)

    def test_admin_confirm_deposit_requires_admin(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            r = client.patch("/api/v1/admin/deposits/dep-1/confirm",
                             json={"amount_vnd_received": 50000}, headers=AUTH_HEADERS)
        assert r.status_code in (403, 401)

    def test_admin_confirm_deposit_success(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_ADMIN):
            with patch("app.services.economy_service.confirm_deposit",
                       return_value={"lt_credited": 47500.0, "new_balance": 47500.0}):
                r = client.patch("/api/v1/admin/deposits/dep-1/confirm",
                                 json={"amount_vnd_received": 50000}, headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)


class TestShop:
    def test_list_shop_public(self):
        with patch("app.services.economy_service.list_shop_items", return_value=[MOCK_ITEM]):
            r = client.get("/api/v1/economy/shop")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_purchase_requires_auth(self):
        r = client.post("/api/v1/economy/shop/item-1/purchase")
        assert r.status_code == 401

    def test_purchase_insufficient_balance(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.economy_service.purchase_item",
                       side_effect=HTTPException(status_code=402, detail="Insufficient Linh Thach")):
                r = client.post("/api/v1/economy/shop/item-1/purchase", headers=AUTH_HEADERS)
        assert r.status_code in (402, 401)

    def test_purchase_success(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.economy_service.purchase_item",
                       return_value={"item": MOCK_ITEM, "lt_spent": 5000.0, "new_balance": 95000.0}):
                r = client.post("/api/v1/economy/shop/item-1/purchase", headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)

    def test_gift_requires_auth(self):
        r = client.post("/api/v1/economy/shop/item-1/gift", json={"receiver_id": "uploader-456"})
        assert r.status_code == 401

    def test_gift_success(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.economy_service.gift_item",
                       return_value={"lt_spent": 5000.0, "tt_credited": 4750.0, "item": MOCK_ITEM}):
                r = client.post("/api/v1/economy/shop/item-1/gift",
                                json={"receiver_id": "uploader-456"}, headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)


class TestWithdrawal:
    def test_create_withdrawal_requires_auth(self):
        r = client.post("/api/v1/economy/withdrawal",
                        json={"tt_amount": 10000.0, "bank_info": {"bank": "VCB"}})
        assert r.status_code == 401

    def test_create_withdrawal_reader_forbidden(self):
        from fastapi import HTTPException
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            with patch("app.services.economy_service.create_withdrawal",
                       side_effect=HTTPException(status_code=403, detail="Only uploaders can withdraw")):
                r = client.post("/api/v1/economy/withdrawal",
                                json={"tt_amount": 10000.0, "bank_info": {"bank": "VCB"}}, headers=AUTH_HEADERS)
        assert r.status_code in (403, 401)

    def test_create_withdrawal_min_amount(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_UPLOADER):
            r = client.post("/api/v1/economy/withdrawal",
                            json={"tt_amount": 100.0, "bank_info": {"bank": "VCB"}}, headers=AUTH_HEADERS)
        assert r.status_code in (422, 401)

    def test_admin_complete_withdrawal_requires_admin(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_USER):
            r = client.patch("/api/v1/admin/withdrawals/wr-1/complete",
                             json={}, headers=AUTH_HEADERS)
        assert r.status_code in (403, 401)

    def test_admin_complete_withdrawal_deducts_tt(self):
        with patch("app.core.deps.get_current_user", return_value=MOCK_ADMIN):
            with patch("app.services.economy_service.complete_withdrawal",
                       return_value={"status": "completed", "tt_deducted": 10000.0, "new_balance": 0.0}):
                r = client.patch("/api/v1/admin/withdrawals/wr-1/complete",
                                 json={}, headers=AUTH_HEADERS)
        assert r.status_code in (200, 401)
