import pytest
from unittest.mock import patch, mock_open

try:
    from api.services.model_loader import load_models
except ImportError:
    load_models = None

@pytest.mark.skipif(load_models is None, reason="api.services.model_loader not found")
@patch('joblib.load')
@patch('torch.load')
def test_load_models_success(mock_torch_load, mock_joblib_load):
    mock_joblib_load.return_value = {"xgb": "mock_xgb", "lgbm": "mock_lgbm", "rf": "mock_rf", "scaler": "mock_scaler"}
    mock_torch_load.return_value = "mock_state_dict"
    
    with patch('builtins.open', mock_open(read_data=b"data")), patch('pathlib.Path.exists', return_value=True), patch('api.services.model_loader.verify_model_hash', return_value=True):
        models = load_models()
        assert models is not None
        assert "xgb" in models
