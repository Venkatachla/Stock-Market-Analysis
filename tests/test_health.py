"""
Tests for system/health endpoints in api/app_fixed.py.

Covers:
- GET /health — liveness probe
- GET / — root welcome message
- GET /risk-os/overview — risk metrics with default and custom capital
"""
import pytest


class TestHealthEndpoint:
    """Test the /health liveness endpoint."""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_alive_status(self, client):
        data = client.get("/health").json()
        assert data["status"] == "alive"
        assert data["version"] == "2.0.0"


class TestRootEndpoint:
    """Test the / root endpoint."""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_returns_message(self, client):
        data = client.get("/").json()
        assert "message" in data
        assert "Trading API" in data["message"]


class TestRiskOSEndpoint:
    """Test the /risk-os/overview endpoint."""

    def test_risk_os_returns_200(self, client):
        resp = client.get("/risk-os/overview")
        assert resp.status_code == 200

    def test_risk_os_default_capital(self, client):
        data = client.get("/risk-os/overview").json()
        assert data["capital"] == 100000.0
        assert data["status"] == "EXECUTE"
        assert "sharpe" in data
        assert "beta" in data
        assert "max_drawdown" in data
        assert "volatility" in data
        assert "updated_at" in data

    def test_risk_os_custom_capital(self, client):
        # Test with custom capital parameter
        resp = client.get("/risk-os/overview?capital=500000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["capital"] == 500000.0

    def test_risk_os_active_setups_count(self, client):
        # active_setups should equal the number of SIGNALS_CONFIG entries (8)
        data = client.get("/risk-os/overview").json()
        assert data["active_setups"] == 8

    def test_risk_os_invalid_capital_rejected(self, client):
        # capital must be > 0 per the Query constraint
        resp = client.get("/risk-os/overview?capital=-100")
        assert resp.status_code == 422  # Validation error
