"""
ML Predictor Service
Runs ensemble predictions using loaded ML models.
Supports multiple ensemble strategies: majority vote, weighted average.
"""
import numpy as np
import torch
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PredictionResult:
    """Container for prediction results"""
    
    def __init__(self, 
                 signal: str,  # BUY, SELL, NEUTRAL
                 confidence: float,  # 0-100
                 models_output: Dict[str, Any]):
        self.signal = signal
        self.confidence = confidence
        self.models_output = models_output
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "signal": self.signal,
            "confidence": self.confidence,
            "models": self.models_output
        }


class Predictor:
    """Ensemble ML predictor"""
    
    # Ensemble weights (configurable)
    WEIGHTS = {
        "xgb": 0.4,
        "lgbm": 0.3,
        "rf": 0.2,
        "lstm": 0.1
    }
    
    # Confidence thresholds
    BUY_THRESHOLD = 65.0  # Confidence > 65% = BUY signal
    SELL_THRESHOLD = 35.0  # Confidence < 35% = SELL signal
    
    def __init__(self, model_loader):
        """
        Initialize Predictor
        
        Args:
            model_loader: ModelLoader instance
        """
        self.model_loader = model_loader
    
    def predict(self, features: np.ndarray) -> PredictionResult:
        """
        Run ensemble prediction
        
        Args:
            features: Input features (numpy array)
        
        Returns:
            PredictionResult with signal and confidence
        """
        models = self.model_loader.get_all_models()
        
        if len(models) == 0:
            logger.warning("No models available - returning NEUTRAL signal")
            return PredictionResult(
                signal="NEUTRAL",
                confidence=50.0,
                models_output={}
            )
        
        # Get predictions from all models
        model_predictions = self._get_model_predictions(features, models)
        
        # Aggregate predictions
        ensemble_signal, confidence = self._aggregate_predictions(model_predictions)
        
        return PredictionResult(
            signal=ensemble_signal,
            confidence=confidence,
            models_output=model_predictions
        )
    
    def _get_model_predictions(self, features: np.ndarray, models: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Get predictions from each individual model
        
        Args:
            features: Input features
            models: Dictionary of loaded models
        
        Returns:
            Dictionary with predictions from each model
        """
        predictions = {}
        
        # Scale features if scaler is available
        scaled_features = self.model_loader.scale_features(features.reshape(1, -1))
        
        # Tree-based models (XGBoost, LightGBM, RandomForest)
        for model_name in ["xgb", "lgbm", "rf"]:
            if model_name in models:
                try:
                    model = models[model_name]
                    
                    # Get probability predictions
                    if hasattr(model, "predict_proba"):
                        probas = model.predict_proba(scaled_features)[0]
                        pred_class = np.argmax(probas)
                        confidence = float(probas[pred_class]) * 100
                    else:
                        pred_class = model.predict(scaled_features)[0]
                        confidence = 50.0
                    
                    signal = "BUY" if pred_class == 1 else "SELL"
                    
                    predictions[model_name] = {
                        "signal": signal,
                        "confidence": round(confidence, 2),
                        "pred_class": int(pred_class)
                    }
                except Exception as e:
                    logger.error(f"Error in {model_name} prediction: {str(e)}")
                    predictions[model_name] = {
                        "signal": "NEUTRAL",
                        "confidence": 50.0,
                        "error": str(e)
                    }
        
        # LSTM model (PyTorch)
        if "lstm" in models:
            try:
                lstm_signal, lstm_confidence = self._predict_lstm(
                    features, models["lstm"]
                )
                predictions["lstm"] = {
                    "signal": lstm_signal,
                    "confidence": lstm_confidence
                }
            except Exception as e:
                logger.error(f"Error in LSTM prediction: {str(e)}")
                predictions["lstm"] = {
                    "signal": "NEUTRAL",
                    "confidence": 50.0,
                    "error": str(e)
                }
        
        logger.debug(f"Model predictions: {predictions}")
        return predictions
    
    def _predict_lstm(self, features: np.ndarray, lstm_model) -> Tuple[str, float]:
        """
        Run LSTM model prediction
        
        Args:
            features: Input features
            lstm_model: Trained LSTM model
        
        Returns:
            Tuple of (signal, confidence)
        """
        try:
            # Convert to tensor
            features_tensor = torch.FloatTensor(features).unsqueeze(0)  # Add batch dimension
            
            # Run model
            with torch.no_grad():
                if hasattr(lstm_model, 'forward'):
                    output = lstm_model(features_tensor)
                else:
                    output = lstm_model(features_tensor)
            
            # Get prediction
            pred_prob = torch.sigmoid(output).item() if len(output.shape) == 0 else torch.sigmoid(output).squeeze().item()
            confidence = float(pred_prob) * 100
            signal = "BUY" if pred_prob >= 0.5 else "SELL"
            
            return signal, round(confidence, 2)
        except Exception as e:
            logger.error(f"LSTM prediction failed: {str(e)}")
            raise
    
    def _aggregate_predictions(self, model_predictions: Dict[str, Dict[str, Any]]) -> Tuple[str, float]:
        """
        Aggregate predictions using weighted ensemble
        
        Args:
            model_predictions: Predictions from each model
        
        Returns:
             Tuple of (ensemble_signal, confidence)
        """
        if len(model_predictions) == 0:
            return "NEUTRAL", 50.0
        
        # Method 1: Majority voting with confidence weighting
        buy_votes = 0  # BUY = 1
        sell_votes = 0  # SELL = 0
        total_weight = 0
        
        for model_name, pred in model_predictions.items():
            if "error" in pred:
                continue
            
            weight = self.WEIGHTS.get(model_name, 0.1)
            confidence = pred.get("confidence", 50.0) / 100.0  # Normalize to 0-1
            
            if pred["signal"] == "BUY":
                buy_votes += weight * confidence
            else:
                sell_votes += weight * confidence
            
            total_weight += weight
        
        # Normalize votes
        if total_weight > 0:
            buy_ratio = buy_votes / total_weight
            sell_ratio = sell_votes / total_weight
        else:
            return "NEUTRAL", 50.0
        
        # Determine ensemble signal and confidence
        return self._determine_signal_and_confidence(buy_ratio, sell_ratio)
    
    def _determine_signal_and_confidence(self, buy_ratio: float, sell_ratio: float) -> Tuple[str, float]:
        """
        Determine final signal and confidence from ratios
        
        Args:
            buy_ratio: Weighted ratio for BUY
            sell_ratio: Weighted ratio for SELL
        
        Returns:
            Tuple of (signal, confidence)
        """
        # Confidence as distance from 50% (neutral)
        max_ratio = max(buy_ratio, sell_ratio)
        confidence = max_ratio * 100
        
        # Determine signal based on threshold
        if buy_ratio > sell_ratio:
            if confidence >= self.BUY_THRESHOLD:
                signal = "BUY"
            else:
                signal = "NEUTRAL"
        else:
            if confidence >= self.SELL_THRESHOLD:
                signal = "SELL"
            else:
                signal = "NEUTRAL"
        
        return signal, round(confidence, 2)
    
    def set_weights(self, weights: Dict[str, float]) -> None:
        """
        Update ensemble weights
        
        Args:
            weights: Dictionary of model_name -> weight
        """
        # Normalize weights to sum to 1
        total = sum(weights.values())
        self.WEIGHTS = {
            model: weight / total
            for model, weight in weights.items()
        }
        logger.info(f"Updated ensemble weights: {self.WEIGHTS}")
    
    def set_thresholds(self, buy_threshold: float, sell_threshold: float) -> None:
        """
        Update prediction thresholds
        
        Args:
            buy_threshold: Confidence threshold for BUY (0-100)
            sell_threshold: Confidence threshold for SELL (0-100)
        """
        self.BUY_THRESHOLD = buy_threshold
        self.SELL_THRESHOLD = sell_threshold
        logger.info(f"Updated thresholds - BUY: {buy_threshold}, SELL: {sell_threshold}")


# Global predictor instance
_predictor: Optional[Predictor] = None


def get_predictor(model_loader) -> Predictor:
    """
    Get or create global predictor instance
    
    Args:
        model_loader: ModelLoader instance
    
    Returns:
        Predictor instance
    """
    global _predictor
    
    if _predictor is None:
        _predictor = Predictor(model_loader)
    
    return _predictor
