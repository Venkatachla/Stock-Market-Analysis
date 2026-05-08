# 🔴 CRITICAL ISSUE ANALYSIS & FIX

## ROOT CAUSE #1: Confidence Corrupted by News Sentiment

**Location:** `api/app.py` line ~1367

**WRONG CODE:**
```python
prob_up = prob_up + (sentiment_weight * sentiment_score)  # ❌ MIXING NEWS INTO ML PROB
```

**IMPACT:** 
- ML probability (0-1) gets corrupted by news score (-1 to 1)
- Confidence becomes unreliable
- System returns same ~50-60% confidence for many stocks

---

## ROOT CAUSE #2: Confidence = Complex Technical Score

**Location:** `api/app.py` lines 1400-1500

**WRONG CALCULATION:**
```python
total_score = trend_points + momentum_points + macd_points + volume_points + price_points + news_points
confidence_score = total_score  # ❌ NOT ML probability
```

**IMPACT:**
- Confidence isn't from model
- Mixes 6 different signals
- Makes confidence non-probabilistic

---

## ROOT CAUSE #3: Data Caching & Static Responses

**Location:** Backend doesn't invalidate cache per request

**IMPACT:**
- Same data returned for 30s+ 
- Prices don't update dynamically
- Predictions static for each stock

---

## ROOT CAUSE #4: Frontend Only Polls Every 30s

**Location:** `frontend/src/pages/StockDetail.tsx` line ~22

**CURRENT:**
```typescript
const { data: stock } = usePolling<StockSignal>(
  pollStockDetail,
  30000  // ❌ 30 seconds is too long for "real-time"
);
```

---

# ✅ SOLUTION

## STEP 1: Add New Fixed Endpoints to `api/app.py`

Add this import at the top:
```python
from datetime import datetime
```

Add this endpoint (append to end of file before `if __name__ == "__main__"`):

```python
# ==================== FIXED PREDICTION ENDPOINTS ====================
# These endpoints provide:
# 1. Confidence = Pure ML probability (0-100)
# 2. News = Separate signal (NOT in confidence)
# 3. Fresh data = No caching
# 4. Timestamp = Current time (ISO format)

@app.get("/predict-live/{symbol}")
async def predict_live(symbol: str, timeframe: str = "1d"):
    """
    FIXED LIVE PREDICTION
    
    Returns:
    {
      "symbol": "RELIANCE",
      "confidence_score": 78.5,      ← Pure ML probability * 100
      "probability_up": 0.785,        ← Raw ML probability
      "probability_down": 0.215,
      "signal": "BUY",                ← Based on confidence threshold only
      "news_sentiment_score": 0.15,   ← Separate, informational
      "news_sentiment_label": "POSITIVE",
      "latest_price": 2456.75,
      "timestamp": "2026-04-29T12:34:56.789012",  ← FRESH
      "regime": "UPTREND",
      "entry_price": 2456.75,
      "stop_loss": 2435.20,
      "take_profit": 2498.85,
      "sma_50": 2445.10,
      "sma_200": 2430.25,
      "rsi": 58.5
    }
    """
    try:
        mapped_symbol = SYMBOL_MAPPING.get(symbol.upper(), symbol)
        ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
        
        # ===== 1. FETCH FRESH DATA (no cache) =====
        hist = fetch_history(ticker, period="2y", interval="1d")
        if hist is None or len(hist) < LOOKBACK + 1:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")
        
        # ===== 2. COMPUTE FEATURES =====
        features_df = compute_features_from_history(hist)
        if features_df is None or len(features_df) < LOOKBACK + 1:
            raise HTTPException(status_code=400, detail="Feature computation failed")
        
        # ===== 3. GET ML MODEL PREDICTIONS =====
        models = load_models()
        trained_cols = models.get("trained_cols", [])
        X_scaled_df = features_df[trained_cols].fillna(0.0)
        X_scaled = models["scaler"].transform(X_scaled_df)
        
        # Get probability from each model
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
            except Exception as e:
                pass
        
        lstm_val = _safe_float(lstm_prob, 0.5)
        
        # ===== 4. ENSEMBLE (NO NEWS) =====
        base_stack = np.array([[xgb_prob, lgbm_prob, rf_prob, lstm_val]])
        if models.get("meta_model") is not None:
            prob_up = float(models["meta_model"].predict_proba(base_stack)[:, 1][0])
        else:
            w = models.get("dynamic_weights", ENSEMBLE_WEIGHTS)
            prob_up = (
                w.get("xgb", 0.4) * xgb_prob
                + w.get("lgbm", 0.3) * lgbm_prob
                + w.get("rf", 0.2) * rf_prob
                + w.get("lstm", 0.1) * lstm_val
            )
        
        # Clamp probability
        prob_up = _safe_float(max(0.0, min(1.0, prob_up)), 0.5)
        prob_down = 1.0 - prob_up
        
        # ===== 5. CONFIDENCE = PURE ML PROBABILITY * 100 (NO NEWS) =====
        confidence_score = _safe_float(prob_up * 100.0, 50.0)
        
        # ===== 6. SIGNAL: Based on confidence threshold only =====
        if confidence_score >= 65.0:
            signal = "BUY"
        elif confidence_score <= 35.0:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        # ===== 7. FETCH NEWS (SEPARATE, INFORMATIONAL) =====
        sentiment_score, news_items = fetch_news_sentiment(ticker, symbol, limit=5)
        sentiment_score = _safe_float(sentiment_score, 0.0)
        
        if sentiment_score > 0.15:
            news_label = "POSITIVE"
        elif sentiment_score < -0.15:
            news_label = "NEGATIVE"
        else:
            news_label = "NEUTRAL"
        
        # ===== 8. TECHNICAL CONTEXT (informational) =====
        latest_price = _safe_float(features_df["close"].iloc[-1], 0.0)
        latest = features_df.iloc[-1]
        
        sma50 = _safe_float(pd.to_numeric(latest.get("sma_50", latest_price), errors="coerce"), latest_price)
        sma200 = _safe_float(pd.to_numeric(latest.get("sma_200", sma50), errors="coerce"), sma50)
        rsi = _safe_float(pd.to_numeric(latest.get("rsi", 50.0), errors="coerce"), 50.0)
        
        # ===== 9. TRADING PLAN (from ML signal only) =====
        recent_returns = features_df["daily_return"].tail(20)
        volatility = _safe_float(recent_returns.std(), 0.02) * latest_price
        stop_distance = max(volatility * 1.5, latest_price * 0.01)
        
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
        
        # ===== 10. REGIME =====
        if latest_price > sma50 > sma200:
            regime = "UPTREND"
        elif latest_price < sma50 < sma200:
            regime = "DOWNTREND"
        else:
            regime = "MIXED"
        
        return {
            "symbol": symbol.upper(),
            "confidence_score": _safe_float(confidence_score, 50.0),
            "probability_up": _safe_float(prob_up, 0.5),
            "probability_down": _safe_float(prob_down, 0.5),
            "signal": signal,
            "news_sentiment_score": _safe_float(sentiment_score, 0.0),
            "news_sentiment_label": news_label,
            "latest_price": _safe_float(latest_price, 0.0),
            "timestamp": datetime.now().isoformat(),  # ← FRESH TIMESTAMP
            "regime": regime,
            "entry_price": _safe_float(entry_price, 0.0),
            "stop_loss": _safe_float(stop_loss, 0.0),
            "take_profit": _safe_float(take_profit, 0.0),
            "sma_50": _safe_float(sma50, 0.0),
            "sma_200": _safe_float(sma200, 0.0),
            "rsi": _safe_float(rsi, 50.0),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/batch-live")
async def batch_predictions_live(symbols: str = "RELIANCE,TCS,INFY"):
    """Batch live predictions with fresh data"""
    syms = [s.strip().upper() for s in symbols.split(",")]
    results = []
    
    for sym in syms:
        try:
            pred_response = await predict_live(sym)
            results.append(pred_response)
        except Exception as e:
            pass
    
    return {
        "predictions": results,
        "timestamp": datetime.now().isoformat(),
        "count": len(results)
    }


print("✅ FIXED PREDICTION ENDPOINTS REGISTERED")
print("   /predict-live/{symbol}  - Pure ML confidence + fresh data")
print("   /batch-live            - Batch predictions")
