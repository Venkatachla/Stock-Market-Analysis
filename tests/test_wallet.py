"""
Tests for wallet endpoints in api/app_fixed.py.

Covers:
- GET /wallet — requires auth, returns balance breakdown
- POST /api/portfolio/add-demo-funds — credits wallet with validation
- Auth guards (401 for unauthenticated requests)
- Edge cases (zero/negative amounts)
"""
import pytest


class TestWalletAuthGuard:
    """Wallet endpoints require authentication."""

    def test_wallet_without_auth_returns_401(self, client):
        # GET /wallet without Authorization header
        resp = client.get("/wallet")
        assert resp.status_code == 401

    def test_wallet_with_invalid_token_returns_401(self, client):
        resp = client.get("/wallet", headers={"Authorization": "Bearer invalid_token"})
        assert resp.status_code == 401


class TestGetWallet:
    """Test GET /wallet endpoint."""

    def test_new_user_wallet_has_zero_balance(self, client, auth_headers):
        # A freshly signed-up user should have zero balance
        resp = client.get("/wallet", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["available_balance"] == 0.0
        assert data["used_balance"] == 0.0
        assert data["total_balance"] == 0.0

    def test_wallet_response_has_required_fields(self, client, auth_headers):
        resp = client.get("/wallet", headers=auth_headers)
        data = resp.json()
        required_fields = ["available_balance", "used_balance", "total_balance",
                          "portfolio_value", "pnl"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestAddDemoFunds:
    """Test POST /api/portfolio/add-demo-funds endpoint."""

    def test_add_demo_funds_success(self, client, auth_headers):
        # Add ₹50,000 demo funds
        resp = client.post(
            "/api/portfolio/add-demo-funds?amount=50000",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["amount"] == 50000.0

    def test_add_demo_funds_reflects_in_wallet(self, client, auth_headers):
        # Add funds then check wallet
        client.post("/api/portfolio/add-demo-funds?amount=25000", headers=auth_headers)
        resp = client.get("/wallet", headers=auth_headers)
        data = resp.json()
        assert data["available_balance"] == 25000.0

    def test_add_demo_funds_accumulates(self, client, auth_headers):
        # Multiple deposits should accumulate
        client.post("/api/portfolio/add-demo-funds?amount=10000", headers=auth_headers)
        client.post("/api/portfolio/add-demo-funds?amount=20000", headers=auth_headers)
        resp = client.get("/wallet", headers=auth_headers)
        data = resp.json()
        assert data["available_balance"] == 30000.0

    def test_add_demo_funds_requires_auth(self, client):
        resp = client.post("/api/portfolio/add-demo-funds?amount=1000")
        assert resp.status_code == 401

    def test_add_demo_funds_rejects_negative_amount(self, client, auth_headers):
        # amount must be > 0 per Query(..., gt=0)
        resp = client.post(
            "/api/portfolio/add-demo-funds?amount=-500",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_add_demo_funds_rejects_zero_amount(self, client, auth_headers):
        resp = client.post(
            "/api/portfolio/add-demo-funds?amount=0",
            headers=auth_headers,
        )
        assert resp.status_code == 422
