import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app_fixed import app, get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

@patch("api.app_fixed.get_user_holdings")
@patch("api.app_fixed.get_wallet")
@patch("api.app_fixed.verify_auth_token")
@patch("api.app_fixed.get_stock_price")
def test_get_portfolio(mock_get_price, mock_verify_auth, mock_get_wallet, mock_get_holdings):
    """Test the portfolio calculation logic."""
    mock_verify_auth.return_value = 1
    
    # Mock wallet
    mock_wallet = MagicMock()
    mock_wallet.balance = 5000.0
    mock_get_wallet.return_value = mock_wallet
    
    # Mock holdings
    mock_holding_1 = MagicMock()
    mock_holding_1.symbol = "RELIANCE"
    mock_holding_1.quantity = 10
    mock_holding_1.avg_price = 2000.0
    mock_holding_1.purchase_date = "2026-01-01"
    
    mock_holding_2 = MagicMock()
    mock_holding_2.symbol = "TCS"
    mock_holding_2.quantity = 5
    mock_holding_2.avg_price = 3000.0
    mock_holding_2.purchase_date = "2026-01-02"
    
    mock_get_holdings.return_value = [mock_holding_1, mock_holding_2]
    
    # Mock live prices
    def mock_price_side_effect(symbol):
        if "RELIANCE" in symbol:
            return {"price": 2500.0, "name": "Reliance", "change": 0, "changePercent": 0}
        elif "TCS" in symbol:
            return {"price": 2800.0, "name": "TCS", "change": 0, "changePercent": 0}
        return {"price": 0, "name": "", "change": 0, "changePercent": 0}
        
    mock_get_price.side_effect = mock_price_side_effect
    
    response = client.get("/portfolio", headers={"Authorization": "Bearer test_token"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["available_balance"] == 5000.0
    assert data["number_of_holdings"] == 2
    
    # Verify RELIANCE calculation
    rel = next(h for h in data["holdings"] if h["symbol"] == "RELIANCE")
    assert rel["current_price"] == 2500.0
    assert rel["total_investment"] == 20000.0
    assert rel["current_value"] == 25000.0
    assert rel["pnl"] == 5000.0
    assert rel["pnl_percent"] == 25.0
    
    # Verify overall portfolio calculation
    assert data["used_balance"] == 35000.0 # (10*2000) + (5*3000)
    assert data["portfolio_value"] == 39000.0    # (10*2500) + (5*2800)
    assert data["pnl"] == 4000.0
    
@patch("api.app_fixed.get_wallet")
@patch("api.app_fixed.verify_auth_token")
def test_get_portfolio_no_wallet(mock_verify_auth, mock_get_wallet):
    """Test portfolio fails gracefully if wallet doesn't exist."""
    mock_verify_auth.return_value = 1
    mock_get_wallet.return_value = None
    
    response = client.get("/portfolio", headers={"Authorization": "Bearer test_token"})
    assert response.status_code == 200
    assert response.json()["available_balance"] == 0

@patch("api.app_fixed.create_transaction")
@patch("api.app_fixed.add_to_wallet")
@patch("api.app_fixed.verify_auth_token")
def test_add_demo_funds(mock_verify_auth, mock_add_to_wallet, mock_create_txn):
    """Test the add demo funds endpoint."""
    mock_verify_auth.return_value = 1
    mock_add_to_wallet.return_value = True
    
    response = client.post(
        "/api/portfolio/add-demo-funds?amount=1000",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    assert response.json()["amount"] == 1000.0
    
    # Verify negative funds are rejected
    response = client.post(
        "/api/portfolio/add-demo-funds?amount=-500",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 422
