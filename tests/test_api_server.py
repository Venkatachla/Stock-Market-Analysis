import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.server import app

client = TestClient(app)

def test_health_check():
    with patch('api.server.load_models', return_value={'lstm': True}):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "lstm_loaded": True}

def test_get_stocks():
    mock_catalog = MagicMock()
    mock_catalog[["symbol", "name"]].drop_duplicates.return_value.to_dict.return_value = [{"symbol": "AAPL", "name": "Apple"}]
    
    with patch('api.server.symbol_catalog', return_value=mock_catalog):
        response = client.get("/stocks")
        assert response.status_code == 200
        assert "stocks" in response.json()

def test_search_stocks():
    mock_catalog = MagicMock()
    mock_catalog.__getitem__.return_value.__getitem__.return_value.drop_duplicates.return_value.head.return_value.to_dict.return_value = [{"symbol": "AAPL", "name": "Apple"}]
    mock_catalog.__len__.return_value = 1
    
    with patch('api.server.symbol_catalog', return_value=mock_catalog):
        response = client.get("/stocks/search?q=AAPL")
        assert response.status_code == 200
        assert "stocks" in response.json()

def test_top_bulls():
    mock_catalog = MagicMock()
    mock_df = MagicMock()
    mock_df.copy.return_value = mock_df
    mock_df.__len__.return_value = 1
    mock_df.to_dict.return_value = [{"symbol": "AAPL", "name": "Apple", "prob": 80, "signal": "BUY"}]
    mock_catalog.__getitem__.return_value.drop_duplicates.return_value.head.return_value = mock_df
    
    with patch('api.server.symbol_catalog', return_value=mock_catalog):
        response = client.get("/stocks/top-bulls")
        assert response.status_code == 200
        assert "stocks" in response.json()

@patch('api.server.predict_single')
def test_predict(mock_predict_single):
    mock_predict_single.return_value = {
        "symbol": "AAPL",
        "name": "Apple",
        "prob_up": 0.8,
        "prob_down": 0.2,
        "rows_used": 100,
        "asof": "2023-01-01",
        "detail": {"xgb": 0.8, "lgbm": 0.8, "rf": 0.8, "lstm": 0.8}
    }
    response = client.get("/predict?symbol=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["signal"] == "BUY"

@patch('api.server.predict_single')
def test_predict_batch(mock_predict_single):
    mock_predict_single.return_value = {
        "symbol": "AAPL",
        "name": "Apple",
        "prob_up": 0.8,
        "prob_down": 0.2,
        "rows_used": 100,
        "asof": "2023-01-01",
        "detail": {"xgb": 0.8, "lgbm": 0.8, "rf": 0.8, "lstm": 0.8}
    }
    response = client.post("/predict", json={"symbols": ["AAPL"]})
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 1
