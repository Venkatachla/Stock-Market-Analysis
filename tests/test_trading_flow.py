"""
Complete End-to-End Trading Flow Test.
Tests: Signup -> Fund -> Buy -> Portfolio check -> Sell -> Final check.

Rewritten from the original manual script to use pytest fixtures
(client, auth_headers) from tests/conftest.py.
"""
import pytest


class TestCompleteTradingFlow:
    """End-to-end trading flow using a single authenticated session."""

    def test_initial_wallet_is_zero(self, client, auth_headers):
        """Step 1: New user wallet should start at zero."""
        resp = client.get("/wallet", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["available_balance"] == 0.0

    def test_add_demo_funds(self, client, auth_headers):
        """Step 2: Add demo funds to wallet."""
        resp = client.post(
            "/api/portfolio/add-demo-funds?amount=10000",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_wallet_reflects_funding(self, client, auth_headers):
        """Step 3: Wallet balance updates after funding."""
        client.post("/api/portfolio/add-demo-funds?amount=10000", headers=auth_headers)
        resp = client.get("/wallet", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["available_balance"] == 10000.0

    def test_empty_portfolio(self, client, auth_headers):
        """Step 4: Portfolio should be empty before any trades."""
        resp = client.get("/portfolio", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["holdings"] == []
        assert data["number_of_holdings"] == 0

    def test_buy_stock(self, client, auth_headers):
        """Step 5: Buy stock succeeds when wallet is funded."""
        client.post("/api/portfolio/add-demo-funds?amount=10000", headers=auth_headers)
        resp = client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_cost"] == 1500.0  # 1 × mocked ₹1500

    def test_portfolio_after_buy(self, client, auth_headers):
        """Step 6: Portfolio shows holding after purchase."""
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 2},
            headers=auth_headers,
        )
        resp = client.get("/portfolio", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["number_of_holdings"] == 1
        holding = data["holdings"][0]
        assert holding["symbol"] == "RELIANCE"
        assert holding["quantity"] == 2

    def test_transactions_after_buy(self, client, auth_headers):
        """Step 7: Transaction history records the purchase."""
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 1},
            headers=auth_headers,
        )
        resp = client.get("/portfolio/transactions", headers=auth_headers)
        assert resp.status_code == 200
        txns = resp.json()["transactions"]
        assert len(txns) >= 2  # DEPOSIT + BUY

    def test_sell_stock(self, client, auth_headers):
        """Step 8: Sell stock succeeds when holdings exist."""
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 3},
            headers=auth_headers,
        )
        resp = client.post(
            "/api/trading/sell",
            json={"symbol": "RELIANCE", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_proceeds"] == 1500.0  # 1 × mocked ₹1500

    def test_portfolio_after_sell(self, client, auth_headers):
        """Step 9: Portfolio reflects reduced holdings after sell."""
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 3},
            headers=auth_headers,
        )
        client.post(
            "/api/trading/sell",
            json={"symbol": "RELIANCE", "quantity": 1},
            headers=auth_headers,
        )
        resp = client.get("/portfolio", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        holding = data["holdings"][0]
        assert holding["symbol"] == "RELIANCE"
        assert holding["quantity"] == 2  # 3 bought - 1 sold

    def test_wallet_after_sell(self, client, auth_headers):
        """Step 10: Wallet balance increases after selling."""
        client.post("/api/portfolio/add-demo-funds?amount=50000", headers=auth_headers)
        client.post(
            "/api/trading/buy",
            json={"symbol": "RELIANCE", "quantity": 2},
            headers=auth_headers,
        )
        # Wallet: 50000 - 3000 = 47000
        client.post(
            "/api/trading/sell",
            json={"symbol": "RELIANCE", "quantity": 1},
            headers=auth_headers,
        )
        # Wallet: 47000 + 1500 = 48500
        resp = client.get("/wallet", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["available_balance"] == 48500.0
