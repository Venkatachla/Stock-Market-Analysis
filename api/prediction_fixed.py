"""
FIXED PREDICTION SYSTEM
- Confidence = PURE ML probability (0-100)
- News = Separate optional signal (not in confidence)
- Fresh data = Every request, no caching
- Timestamp = Included in response
"""

from datetime import datetime
import numpy as np
import torch
import yfinance as yf
from typing import Optional
import pandas as pd

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Fixed Prediction API")

# ==================== RESPONSE MODELS ====================

from pydantic import BaseModel

class FixedStockPredictionResponse(BaseModel):
    """CORRECTED prediction response"""
    symbol: str
    
    # ===== PURE ML CONFIDENCE (0-100) =====
    confidence_score: float  # ← ML probability * 100, NOT affected by news
    probability_up: float    # ← Raw ML prob (0-1)
    probability_down: float  # ← 1 - prob_up
    
    # ===== SIGNAL (based purely on ML confidence threshold) =====
    signal: str  # BUY / SELL / NEUTRAL
    
    # ===== SEPARATE NEWS SIGNAL (optional, informational only) =====
    news_sentiment_score: float  # ← -1 to 1, independent of ML
    news_sentiment_label: str    # POSITIVE / NEUTRAL / NEGATIVE
    
    # ===== COMBINED SCORE =====
    final_score: float           # 0.8 * ML + 0.2 * News
    
    # ===== METADATA =====
    latest_price: float
    timestamp: str  # ISO format, FRESH
    regime: str
    reason: str
    
    # ===== TRADING PLAN (based on ML signal only) =====
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # ===== TECHNICAL CONTEXT (informational) =====
    sma_50: float
    sma_200: float
    rsi: float


# ==================== FIXED PREDICTION FUNCTION ====================

def predict_single_FIXED(symbol: str, timeframe: str = "1d") -> Optional[FixedStockPredictionResponse]:
    """
    FIXED PREDICTION PIPELINE
    
    RULES:
    1. Confidence = model.predict_proba() * 100  (NO news influence)
    2. News = Separate, informational only
    3. Data = Fresh fetch every call
    4. Timestamp = Current time (ISO)
    """
    try:
        # ==================== 1. FETCH FRESH DATA (no cache) ====================
        mapped_symbol = SYMBOL_MAPPING.get(symbol.upper(), symbol)
        ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
        
        # Force fresh data: no caching
        hist = yf.download(ticker, period="2y", interval="1d", progress=False)
        if hist is None or len(hist) < LOOKBACK + 1:
            return None
        
        # ==================== 2. COMPUTE FEATURES ====================
        features_df = compute_features_from_history(hist)
        if features_df is None or len(features_df) < LOOKBACK + 1:
            return None
        
        # ==================== 3. GET ML MODEL PREDICTIONS ====================
        models = load_models()
        trained_cols = models.get("trained_cols", [])
        X_scaled_df = features_df[trained_cols].fillna(0.0)
        X_scaled = models["scaler"].transform(X_scaled_df)
        
        # Get raw ML probabilities
        xgb_prob = _safe_float(models["xgb"].predict_proba(X_scaled)[:, 1][0], 0.5)
        lgbm_prob = _safe_float(models["lgbm"].predict_proba(X_scaled_df)[:, 1][0], 0.5)
        rf_prob = _safe_float(models["rf"].predict_proba(X_scaled)[:, 1][0], 0.5)
        
        lstm_prob = None
        if models.get("lstm") is not None:
            try:
                seq_raw = features_df[trained_cols].reindex(columns=trained_cols).fillna(0.0)
                seq_scaled = models["scaler"].transform(seq_raw)
                X_seq, _ = make_sequences(seq_scaled, np.zeros(len(seq_scaled)), lookback=LOOKBACK)
                if len(X_seq) > 0:
                    with torch.no_grad():
                        preds = models["lstm"](torch.tensor(X_seq[-1:], dtype=torch.float32)).squeeze().item()
                        lstm_prob = float(preds)
            except:
                lstm_prob = 0.5
        
        lstm_val = _safe_float(lstm_prob, 0.5)
        
        # ==================== 4. ENSEMBLE: COMBINE ML MODELS (NO NEWS) ====================
        base_stack = np.array([[xgb_prob, lgbm_prob, rf_prob, lstm_val]])
        if models.get("meta_model") is not None:
            # Stack probabilities and let meta-model blend
            prob_up = float(models["meta_model"].predict_proba(base_stack)[:, 1][0])
        else:
            # Weighted blend of all models
            w = models.get("dynamic_weights", ENSEMBLE_WEIGHTS)
            prob_up = (
                w.get("xgb", 0.4) * xgb_prob
                + w.get("lgbm", 0.3) * lgbm_prob
                + w.get("rf", 0.2) * rf_prob
                + w.get("lstm", 0.1) * lstm_val
            )
        
        # Clamp to [0, 1]
        prob_up = _safe_float(max(0.0, min(1.0, prob_up)), 0.5)
        prob_down = 1.0 - prob_up
        
        # ==================== 5. CONFIDENCE = PURE ML PROBABILITY (0-100) ====================
        # NO news sentiment mixed in
        confidence_score = _safe_float(prob_up * 100.0, 50.0)
        
        # ==================== 6. SIGNAL: Based on confidence threshold ONLY ====================
        if confidence_score >= 65.0:
            signal = "BUY"
        elif confidence_score <= 35.0:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
            
        # ==================== 7. FETCH NEWS SENTIMENT (LIVE API) ====================
        try:
            from api.services.external_apis import get_news, average_sentiment, get_live_stock
            articles = get_news(symbol)
            sentiment_score_0_1 = average_sentiment(articles)
            
            # Map [0, 1] sentiment back to [-1, 1] for label logic compatibility
            sentiment_score = (sentiment_score_0_1 * 2.0) - 1.0
            
            # Fallback handling already done inside average_sentiment (returns 0.5 neutral)
        except Exception as e:
            print(f"News API Fallback used: {e}")
            sentiment_score_0_1 = 0.5
            sentiment_score = 0.0

        # News label
        if sentiment_score > 0.15:
            news_label = "POSITIVE"
        elif sentiment_score < -0.15:
            news_label = "NEGATIVE"
        else:
            news_label = "NEUTRAL"
            
        # ==================== 7.5 FINAL SCORE CALCULATION ====================
        # ML Confidence is 0-100, we convert to 0-1
        model_confidence_0_1 = confidence_score / 100.0
        final_score_0_1 = (0.8 * model_confidence_0_1) + (0.2 * sentiment_score_0_1)
        final_score = final_score_0_1 * 100.0
        
        # ==================== 8. TECHNICAL CONTEXT (informational) ====================
        # Use LIVE STOCK data if available, fallback to hist
        live_data = get_live_stock(symbol)
        if live_data["price"] > 0:
            latest_price = live_data["price"]
        else:
            latest_price = _safe_float(features_df["close"].iloc[-1], 0.0)
        
        latest = features_df.iloc[-1]
        
        sma50 = _safe_float(pd.to_numeric(latest.get("sma_50", latest_price), errors="coerce"), latest_price)
        sma200 = _safe_float(pd.to_numeric(latest.get("sma_200", sma50), errors="coerce"), sma50)
        rsi = _safe_float(pd.to_numeric(latest.get("rsi", 50.0), errors="coerce"), 50.0)
        
        # ==================== 9. TRADING PLAN (from ML signal only) ====================
        # Standard risk management: risk = 2% of recent volatility
        recent_returns = features_df["daily_return"].tail(20)
        volatility = _safe_float(recent_returns.std(), 0.02) * latest_price
        stop_distance = max(volatility * 1.5, latest_price * 0.01)  # Min 1% distance
        
        if signal == "BUY":
            entry_price = latest_price
            stop_loss = latest_price - stop_distance
            take_profit = latest_price + (stop_distance * 2.0)
        elif signal == "SELL":
            entry_price = latest_price
            stop_loss = latest_price + stop_distance
            take_profit = latest_price - (stop_distance * 2.0)
        else:
            entry_price = latest_price
            stop_loss = latest_price - stop_distance
            take_profit = latest_price + stop_distance
        
        # ==================== 10. REGIME & REASON ====================
        if latest_price > sma50 > sma200:
            regime = "UPTREND"
        elif latest_price < sma50 < sma200:
            regime = "DOWNTREND"
        else:
            regime = "MIXED"
        
        reason = f"ML Confidence: {confidence_score:.1f}% ({signal}). News: {news_label} ({sentiment_score:+.2f})"
        
        # ==================== 11. RETURN FIXED RESPONSE ====================
        return FixedStockPredictionResponse(
            symbol=symbol.upper(),
            confidence_score=_safe_float(confidence_score, 50.0),
            probability_up=_safe_float(prob_up, 0.5),
            probability_down=_safe_float(prob_down, 0.5),
            signal=signal,
            news_sentiment_score=_safe_float(sentiment_score_0_1, 0.5),
            news_sentiment_label=news_label,
            final_score=_safe_float(final_score, 50.0),
            latest_price=_safe_float(latest_price, 0.0),
            timestamp=datetime.now().isoformat(),  # ← FRESH TIMESTAMP
            regime=regime,
            reason=reason,
            entry_price=_safe_float(entry_price, 0.0),
            stop_loss=_safe_float(stop_loss, 0.0),
            take_profit=_safe_float(take_profit, 0.0),
            sma_50=_safe_float(sma50, 0.0),
            sma_200=_safe_float(sma200, 0.0),
            rsi=_safe_float(rsi, 50.0),
        )
    
    except Exception as e:
        import traceback
        print(f"Error in predict_single_FIXED({symbol}): {e}")
        traceback.print_exc()
        return None


# ==================== API ENDPOINT ====================

@app.get("/predict/FIXED/{symbol}")
async def get_prediction_fixed(symbol: str, timeframe: str = "1d"):
    """
    FIXED PREDICTION ENDPOINT
    
    Returns:
    - confidence_score: Pure ML probability (0-100), NO news influence
    - news_sentiment_score: Separate signal (-1 to 1)
    - timestamp: Fresh, current time
    
    Example response:
    {
        "symbol": "RELIANCE",
        "confidence_score": 78.5,      ← Pure ML, varies per stock
        "probability_up": 0.785,
        "signal": "BUY",
        "news_sentiment_score": 0.12,  ← Separate, informational
        "news_sentiment_label": "POSITIVE",
        "latest_price": 2456.75,
        "timestamp": "2026-04-29T12:34:56.789012",  ← FRESH
        "regime": "UPTREND",
        "entry_price": 2456.75,
        "stop_loss": 2435.20,
        "take_profit": 2498.85
    }
    """
    pred = predict_single_FIXED(symbol, timeframe)
    if pred is None:
        raise HTTPException(status_code=404, detail=f"Could not predict for {symbol}")
    return pred


# ==================== BATCH ENDPOINT ====================

@app.get("/predict-batch/FIXED")
async def get_batch_predictions_fixed(symbols: str = "RELIANCE,TCS,INFY"):
    """
    FIXED BATCH PREDICTION
    
    Returns predictions for multiple stocks with fresh data
    """
    syms = [s.strip().upper() for s in symbols.split(",")]
    results = []
    
    for sym in syms:
        pred = predict_single_FIXED(sym)
        if pred:
            results.append(pred)
    
    return {
        "predictions": results,
        "timestamp": datetime.now().isoformat(),
        "count": len(results)
    }


predict_single = predict_single_FIXED
predict_batch = get_batch_predictions_fixed


if __name__ == "__main__":
    print("✅ FIXED PREDICTION SYSTEM LOADED")
    print("   - Confidence = Pure ML probability")
    print("   - News = Separate signal")
    print("   - Data = Fresh every request")
    print("   - Timestamp = Included")
