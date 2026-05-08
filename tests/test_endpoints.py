"""
Integration test suite for StockPulse backend endpoints.
Tests all critical endpoints: health, auth, wallet, trading, portfolio.

Rewritten from the original manual script to use pytest fixtures
(client, auth_headers) from tests/conftest.py.
"""
import pytest


class TestHealth:
    """Test health check endpoint."""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_alive(self, client):
        data = client.get("/health").json()
        assert data["status"] == "alive"


class TestRegistration:
    """Test user registration via /api/auth/signup."""

    def test_registration_returns_token(self, client):
        import time
        email = f"reg_{int(time.time() * 1000)}@example.com"
        resp = client.post("/api/auth/signup", json={
            "email": email,
            "password": "password123",
            "name": "Test User",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["token"]
        assert data["email"] == email


class TestLogin:
    """Test user login via /api/auth/login."""

    def test_login_returns_new_token(self, client):
        import time
        email = f"login_{int(time.time() * 1000)}@example.com"
        # Register first
        signup_resp = client.post("/api/auth/signup", json={
            "email": email,
            "password": "password123",
            "name": "Test User",
        })
        assert signup_resp.status_code == 200

        # Login
        resp = client.post("/api/auth/login", json={
            "email": email,
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["token"]


class TestWallet:
    """Test GET /wallet endpoint."""

    def test_wallet_returns_200(self, client, auth_headers):
        resp = client.get("/wallet", headers=auth_headers)
        assert resp.status_code == 200

    def test_wallet_has_balance_fields(self, client, auth_headers):
        data = client.get("/wallet", headers=auth_headers).json()
        assert "available_balance" in data
        assert "total_balance" in data


class TestPortfolio:
    """Test GET /portfolio endpoint."""

    def test_portfolio_returns_200(self, client, auth_headers):
        resp = client.get("/portfolio", headers=auth_headers)
        assert resp.status_code == 200

    def test_portfolio_structure(self, client, auth_headers):
        data = client.get("/portfolio", headers=auth_headers).json()
        assert "holdings" in data
        assert isinstance(data["holdings"], list)


class TestBuyStock:
    """Test POST /api/trading/buy endpoint."""

    def test_buy_without_funds_returns_400(self, client, auth_headers):
        resp = client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 1},
            headers=auth_headers,
        )
        # New user has 0 balance — should fail with 400
        assert resp.status_code == 400
        assert "Insufficient" in resp.json()["detail"]

    def test_buy_with_funds_succeeds(self, client, auth_headers):
        # Fund the account
        client.post("/api/portfolio/add-demo-funds?amount=100000", headers=auth_headers)
        resp = client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestTransactions:
    """Test GET /portfolio/transactions endpoint."""

    def test_transactions_returns_200(self, client, auth_headers):
        resp = client.get("/portfolio/transactions", headers=auth_headers)
        assert resp.status_code == 200

    def test_transactions_has_list(self, client, auth_headers):
        data = client.get("/portfolio/transactions", headers=auth_headers).json()
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
