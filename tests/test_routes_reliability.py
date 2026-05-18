import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.app_fixed import app

client = TestClient(app, raise_server_exceptions=False)

@patch("api.app_fixed.yf.Ticker")
def test_safe_get_stock_price_fallback(mock_ticker):
    """Test that get_stock_price gracefully falls back to default on exception."""
    from api.app_fixed import get_stock_price
    
    # Simulate an external API failure
    mock_ticker.side_effect = Exception("Yahoo Finance API Timeout")
    
    # Should not raise an exception, should return fallback data
    result = get_stock_price("RELIANCE_FALLBACK_TEST")
    assert result["price"] == 1500.0

@patch("api.app_fixed.get_user_by_email")
def test_login_exception_handling(mock_get_user):
    """Test the global exception handler catches unhandled DB errors."""
    # Simulate a database disconnection or severe error
    mock_get_user.side_effect = Exception("Database Connection Lost")
    
    response = client.post(
        "/api/auth/login", 
        json={"email": "test@example.com", "password": "password123"}
    )
    
    # The global exception handler should catch it and return a clean 500 JSON
    assert response.status_code == 500
    assert response.json() == {"detail": "An internal server error occurred. Please try again later."}

@patch("api.prediction_fixed.predict_single_FIXED")
def test_predict_endpoint_failure(mock_predict):
    """Test that the prediction endpoint handles None responses safely."""
    # Simulate the prediction function failing and returning None
    mock_predict.return_value = None
    
    response = client.get("/predict/FIXED/INVALID_SYMBOL")
    
    # The endpoint should raise a 404 HTTPException
    assert response.status_code == 404
    assert "Could not predict for" in response.json()["detail"]

@patch("api.app_fixed.verify_auth_token")
@patch("api.app_fixed.get_wallet")
@patch("api.app_fixed.get_stock_price")
def test_buy_insufficient_balance(mock_get_stock_price, mock_get_wallet, mock_verify_token):
    """Test business logic validation: cannot buy with insufficient balance."""
    # Mock token verification to return user ID 1
    mock_verify_token.return_value = 1
    
    # Mock stock price to 150.0
    mock_get_stock_price.return_value = {
        "price": 150.0,
        "change": 0.0,
        "changePercent": 0.0,
        "volume": 1000,
        "name": "Apple"
    }
    
    # Create a mock wallet with 100 balance
    mock_wallet = MagicMock()
    mock_wallet.balance = 100.0
    mock_get_wallet.return_value = mock_wallet
    
    # Make request to buy 1 stock (cost 150.0, wallet 100.0)
    response = client.post(
        "/api/trading/buy",
        headers={"Authorization": "Bearer fake-token"},
        json={"symbol": "AAPL", "quantity": 1}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient balance"

def test_health_check_endpoint():
    """Test that the liveness probe endpoint works."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
