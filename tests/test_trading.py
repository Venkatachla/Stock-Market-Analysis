"""
Tests for trading endpoints in api/app_fixed.py.

Covers:
- POST /api/trading/buy — full buy flow, insufficient balance, auth guard
- POST /api/trading/sell — full sell flow, insufficient holdings, auth guard
- GET /portfolio — portfolio state after trades
- GET /portfolio/transactions — transaction history
"""
import pytest


class TestBuyStock:
    """Test POST /api/trading/buy endpoint."""

    def test_buy_requires_auth(self, client):
        resp = client.post("/api/trading/buy", json={"symbol": "INFY", "quantity": 1})
        assert resp.status_code == 401

    def test_buy_insufficient_balance(self, client, auth_headers):
        # New user has 0 balance — should fail
        resp = client.post(
            "/api/trading/buy",
            json={"symbol": "INFY", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Insufficient" in resp.json()["detail"]

    def test_buy_success(self, client, auth_headers):
        # Fund the account first
        client.post("/api/portfolio/add-demo-funds?amount=100000", headers=auth_headers)
        # Buy 1 share (mock price is ₹1500)
        resp = client.post(
            "/api/trading/buy",
            json={"symbol": "INFY", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_cost"] == 1500.0  # 1 × ₹1500

    def test_buy_deducts_from_wallet(self, client, auth_headers):
        client.post("/api/portfolio/add-demo-funds?amount=10000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "INFY", "quantity": 2},
            headers=auth_headers,
        )
        # Wallet should have 10000 - (2 × 1500) = 7000
        resp = client.get("/wallet", headers=auth_headers)
        data = resp.json()
        assert data["available_balance"] == 7000.0

    def test_buy_multiple_shares(self, client, auth_headers):
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        resp = client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 5},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total_cost"] == 7500.0  # 5 × ₹1500


class TestSellStock:
    """Test POST /api/trading/sell endpoint."""

    def test_sell_requires_auth(self, client):
        resp = client.post("/api/trading/sell", json={"symbol": "INFY", "quantity": 1})
        assert resp.status_code == 401

    def test_sell_no_holdings_fails(self, client, auth_headers):
        # User has no holdings — should fail
        resp = client.post(
            "/api/trading/sell",
            json={"symbol": "INFY", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Insufficient" in resp.json()["detail"]

    def test_sell_success(self, client, auth_headers):
        # Buy then sell
        client.post("/api/portfolio/add-demo-funds?amount=100000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "INFY", "quantity": 5},
            headers=auth_headers,
        )
        resp = client.post(
            "/api/trading/sell",
            json={"symbol": "INFY", "quantity": 2},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_proceeds"] == 3000.0  # 2 × ₹1500

    def test_sell_credits_wallet(self, client, auth_headers):
        client.post("/api/portfolio/add-demo-funds?amount=20000", headers=auth_headers)
        # Buy 3 shares at ₹1500 = ₹4500 deducted → wallet = ₹15500
        client.post(
            "/api/trading/buy",
            json={"symbol": "TCS", "quantity": 3},
            headers=auth_headers,
        )
        # Sell 1 share → ₹1500 credited → wallet = ₹17000
        client.post(
            "/api/trading/sell",
            json={"symbol": "TCS", "quantity": 1},
            headers=auth_headers,
        )
        resp = client.get("/wallet", headers=auth_headers)
        assert resp.json()["available_balance"] == 17000.0

    def test_sell_more_than_held_fails(self, client, auth_headers):
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "WIPRO", "quantity": 2},
            headers=auth_headers,
        )
        # Try to sell 5 when only 2 are held
        resp = client.post(
            "/api/trading/sell",
            json={"symbol": "WIPRO", "quantity": 5},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestPortfolio:
    """Test GET /portfolio and GET /portfolio/transactions endpoints."""

    def test_portfolio_requires_auth(self, client):
        resp = client.get("/portfolio")
        assert resp.status_code == 401

    def test_empty_portfolio(self, client, auth_headers):
        resp = client.get("/portfolio", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["holdings"] == []
        assert data["number_of_holdings"] == 0

    def test_portfolio_after_buy(self, client, auth_headers):
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "INFY", "quantity": 3},
            headers=auth_headers,
        )
        resp = client.get("/portfolio", headers=auth_headers)
        data = resp.json()
        assert data["number_of_holdings"] == 1
        assert len(data["holdings"]) == 1
        holding = data["holdings"][0]
        assert holding["symbol"] == "INFY"
        assert holding["quantity"] == 3

    def test_portfolio_financial_formulas(self, client, auth_headers):
        # Verify derived financial fields are present and reasonable
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 2},
            headers=auth_headers,
        )
        data = client.get("/portfolio", headers=auth_headers).json()
        # available_balance = 50000 - 3000 = 47000
        assert data["available_balance"] == 47000.0
        # used_balance = 2 × 1500 = 3000
        assert data["used_balance"] == 3000.0
        # total_balance = available + used
        assert data["total_balance"] == 50000.0

    def test_transactions_history(self, client, auth_headers):
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "INFY", "quantity": 1},
            headers=auth_headers,
        )
        resp = client.get("/portfolio/transactions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Should have at least 2 transactions: DEPOSIT + BUY
        assert len(data["transactions"]) >= 2
