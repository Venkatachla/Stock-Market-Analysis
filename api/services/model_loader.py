"""
ML Model Loader Service
Dynamically loads all trained models from MODEL_DIR.
Supports: XGBoost, LightGBM, RandomForest, LSTM
"""
import joblib
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)

def verify_model_hash(file_path: str, expected_hash: str) -> bool:
    """Verifies the SHA256 checksum of a model file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest() == expected_hash
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return False


class ModelLoader:
    """Loads and caches ML models from disk"""
    
    def __init__(self, model_dir: Path, model_type: str = "ensemble"):
        """
        Initialize ModelLoader
        
        Args:
            model_dir: Path to directory containing trained models
            model_type: Type of models to load (ensemble, xgb, lgbm, rf, lstm)
        """
        self.model_dir = Path(model_dir)
        self.model_type = model_type
        self.models: Dict[str, Any] = {}
        self.scaler = None
        self.feature_names = None
        
    def load_all_models(self) -> bool:
        """
        Load all available models from MODEL_DIR
        
        Returns:
            bool: True if at least one model loaded successfully
        """
        if not self.model_dir.exists():
            logger.error(f"Model directory does not exist: {self.model_dir}")
            return False
        
        logger.info(f"Loading models from: {self.model_dir}")
        models_loaded = 0
        
        # Load tree-based models
        tree_models = ["xgb", "lgbm", "rf"]
        for name in tree_models:
            model = self._load_tree_model(name)
            if model is not None:
                self.models[name] = model
                models_loaded += 1
        
        # Load LSTM model
        lstm_model = self._load_lstm_model()
        if lstm_model is not None:
            self.models["lstm"] = lstm_model
            models_loaded += 1
        
        # Load scaler if exists
        self._load_scaler()
        
        # Load feature names if exists
        self._load_feature_names()
        
        if models_loaded == 0:
            logger.warning("No models loaded successfully. System will use dummy predictions.")
            return False
        
        logger.info(f"✅ Successfully loaded {models_loaded} models: {list(self.models.keys())}")
        return True
    
    def _load_tree_model(self, model_name: str) -> Optional[Any]:
        """
        Load tree-based model (XGBoost, LightGBM, RandomForest)
        
        Args:
            model_name: Model type (xgb, lgbm, rf)
        
        Returns:
            Loaded model or None
        """
        possible_paths = [
            self.model_dir / f"{model_name}_model.pkl",
            self.model_dir / f"{model_name}_model.joblib",
            self.model_dir / f"{model_name}.pkl",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    model = joblib.load(str(path))
                    logger.info(f"✅ Loaded {model_name.upper()} from {path.name}")
                    return model
                except Exception as e:
                    logger.error(f"❌ Failed to load {model_name} from {path}: {str(e)}")
                    continue
        
        logger.warning(f"⚠️  {model_name.upper()} model not found")
        return None
    
    def _load_lstm_model(self) -> Optional[Any]:
        """
        Load LSTM model (PyTorch)
        
        Returns:
            Loaded LSTM model or None
        """
        possible_paths = [
            self.model_dir / "lstm_model.pt",
            self.model_dir / "lstm_model.pth",
            self.model_dir / "lstm.pt",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    # Path validation
                    allowed_dir = self.model_dir.resolve()
                    model_path = path.resolve()
                    
                    if not str(model_path).startswith(str(allowed_dir)):
                        logger.error(f"❌ Invalid model path: Path traversal detected for {path}")
                        continue
                        
                    # Hash validation - Pre-calculated trusted SHA256 hash
                    trusted_lstm_hash = "d9883277b1ac35ba8702104c62156ca39c7f00fb861c18f38cfe6021ff8cc8b5"
                    if not verify_model_hash(str(model_path), trusted_lstm_hash):
                        logger.error(f"❌ Model hash verification failed! Potential tampering detected for {path}")
                        continue
                        
                    # Load PyTorch model securely with weights_only=True
                    # Note: You may need to define the model architecture
                    state = torch.load(str(model_path), map_location='cpu', weights_only=True)
                    # Note: Assuming this loader might be adapted for State Dict vs whole models. 
                    # Right now it assumes `torch.load` returns the model or state directly.
                    # We preserve existing return structure but secure the load.
                    model = state
                    
                    # Try to call eval() if it's a full model object rather than a state dict
                    if hasattr(model, 'eval'):
                        model.eval()  # Set to eval mode
                    
                    logger.info(f"✅ Loaded LSTM securely from {path.name}")
                    return model
                except Exception as e:
                    logger.error(f"❌ Failed to load LSTM from {path}: {str(e)}")
                    continue
        
        logger.warning("⚠️  LSTM model not found")
        return None
    
    def _load_scaler(self) -> None:
        """Load feature scaler if exists"""
        possible_paths = [
            self.model_dir / "scaler.pkl",
            self.model_dir / "scaler.joblib",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    self.scaler = joblib.load(str(path))
                    logger.info(f"✅ Loaded scaler from {path.name}")
                    return
                except Exception as e:
                    logger.error(f"❌ Failed to load scaler: {str(e)}")
        
        logger.warning("⚠️  Scaler not found - features will not be scaled")
    
    def _load_feature_names(self) -> None:
        """Load feature column names if exists"""
        possible_paths = [
            self.model_dir / "feature_names.pkl",
            self.model_dir / "feature_columns.pkl",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    self.feature_names = joblib.load(str(path))
                    logger.info(f"✅ Loaded feature names from {path.name}")
                    return
                except Exception as e:
                    logger.error(f"❌ Failed to load feature names: {str(e)}")
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """
        Get a specific model
        
        Args:
            model_name: Name of model (xgb, lgbm, rf, lstm)
        
        Returns:
            Model or None if not loaded
        """
        return self.models.get(model_name, None)
    
    def get_all_models(self) -> Dict[str, Any]:
        """Get all loaded models"""
        return self.models.copy()
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available"""
        return model_name in self.models
    
    def get_available_models(self) -> list:
        """Returns list of available model names"""
        return list(self.models.keys())
    
    def scale_features(self, features: np.ndarray) -> np.ndarray:
        """
        Scale features using loaded scaler
        
        Args:
            features: Input features array
        
        Returns:
            Scaled features or original if no scaler
        """
        if self.scaler is None:
            logger.debug("No scaler available - returning raw features")
            return features
        
        try:
            return self.scaler.transform(features)
        except Exception as e:
            logger.error(f"Failed to scale features: {str(e)}")
            return features


# Global model loader instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader(model_dir: Path, model_type: str = "ensemble") -> ModelLoader:
    """
    Get or create global model loader instance
    
    Args:
        model_dir: Path to models directory
        model_type: Type of models
    
    Returns:
        ModelLoader instance
    """
    global _model_loader
    
    if _model_loader is None:
        _model_loader = ModelLoader(model_dir, model_type)
        _model_loader.load_all_models()
    
    return _model_loader


def initialize_models(model_dir: Path, model_type: str = "ensemble") -> bool:
    """
    Initialize model loader at application startup
    
    Args:
        model_dir: Path to models directory
        model_type: Type of models
    
    Returns:
        True if models loaded successfully
    """
    loader = get_model_loader(model_dir, model_type)
    return len(loader.get_available_models()) > 0
