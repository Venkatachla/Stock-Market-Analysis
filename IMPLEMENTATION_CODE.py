"""
STOCKPULSE FIX - Implementation Guide

This file contains the EXACT CODE to add to api/app.py

Follow these steps:
1. Copy the endpoint code below
2. Find the line: if __name__ == "__main__":
3. Paste the code BEFORE that line
4. Restart the backend
5. Test with: curl http://localhost:8000/predict-live/RELIANCE
"""

# ==================== COPY THIS TO api/app.py ====================

@app.get("/predict-live/{symbol}")
async def predict_live(symbol: str, timeframe: str = "1d"):
    """
    FIXED LIVE PREDICTION - Pure ML Confidence + Fresh Data
    
    Key differences from /predict/{symbol}:
    1. Confidence = model.predict_proba() * 100 (pure ML, 0-100%)
    2. News sentiment = SEPARATE field (not in confidence)
    3. Data = Fresh fetch every request (no caching)
    4. Timestamp = Current time (ISO format)
    5. Signal = Based on confidence threshold only (BUY/SELL/NEUTRAL)
    
    Returns JSON with:
    - confidence_score: 0-100 (ML probability * 100)
    - probability_up: 0-1 (raw ML probability)
    - signal: "BUY" / "SELL" / "NEUTRAL"
    - news_sentiment_score: -1 to 1 (separate from confidence)
    - timestamp: ISO format (current time)
    """
    try:
        # Step 1: Map symbol and get ticker
        mapped_symbol = SYMBOL_MAPPING.get(symbol.upper(), symbol)
        ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
        
        # Step 2: Fetch fresh data (no caching)
        hist = fetch_history(ticker, period="2y", interval="1d")
        if hist is None or len(hist) < LOOKBACK + 1:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")
        
        # Step 3: Compute features
        features_df = compute_features_from_history(hist)
        if features_df is None or len(features_df) < LOOKBACK + 1:
            raise HTTPException(status_code=400, detail="Feature computation failed")
        
        # Step 4: Load ML models
        models = load_models()
        if not models or "xgb" not in models:
            raise HTTPException(status_code=500, detail="ML models not loaded")
        
        trained_cols = models.get("trained_cols", [])
        X_scaled_df = features_df[trained_cols].fillna(0.0)
        X_scaled = models["scaler"].transform(X_scaled_df)
        
        # Step 5: Get ML predictions from each model
        xgb_prob = _safe_float(models["xgb"].predict_proba(X_scaled)[:, 1][0], 0.5)
        lgbm_prob = _safe_float(models["lgbm"].predict_proba(X_scaled_df)[:, 1][0], 0.5)
        rf_prob = _safe_float(models["rf"].predict_proba(X_scaled)[:, 1][0], 0.5)
        
        # LSTM probability
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
            except Exception:
                lstm_prob = None
        
        lstm_val = _safe_float(lstm_prob, 0.5)
        
        # Step 6: Ensemble predictions (NO NEWS MIXING)
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
        
        # Clamp to valid probability range
        prob_up = _safe_float(max(0.0, min(1.0, prob_up)), 0.5)
        prob_down = 1.0 - prob_up
        
        # Step 7: CRITICAL - Confidence = Pure ML probability (0-100)
        # DO NOT add news sentiment here
        confidence_score = _safe_float(prob_up * 100.0, 50.0)
        
        # Step 8: Generate signal from confidence threshold only
        if confidence_score >= 65.0:
            signal = "BUY"
        elif confidence_score <= 35.0:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        # Step 9: Fetch news sentiment (SEPARATE, NOT in confidence)
        sentiment_score, news_items = fetch_news_sentiment(ticker, symbol, limit=5)
        sentiment_score = _safe_float(sentiment_score, 0.0)
        
        if sentiment_score > 0.15:
            news_label = "POSITIVE"
        elif sentiment_score < -0.15:
            news_label = "NEGATIVE"
        else:
            news_label = "NEUTRAL"
        
        # Step 10: Get technical context
        latest_price = _safe_float(features_df["close"].iloc[-1], 0.0)
        latest = features_df.iloc[-1]
        
        sma50 = _safe_float(pd.to_numeric(latest.get("sma_50", latest_price), errors="coerce"), latest_price)
        sma200 = _safe_float(pd.to_numeric(latest.get("sma_200", sma50), errors="coerce"), sma50)
        rsi = _safe_float(pd.to_numeric(latest.get("rsi", 50.0), errors="coerce"), 50.0)
        
        # Step 11: Build trading plan from signal
        try:
            recent_returns = features_df["daily_return"].tail(20)
            volatility = _safe_float(recent_returns.std(), 0.02) * latest_price
        except:
            volatility = latest_price * 0.02
        
        stop_distance = max(volatility * 1.5, latest_price * 0.01)
        
        if signal == "BUY":
            entry_price = latest_price
            stop_loss = latest_price - stop_distance
            take_profit = latest_price + (stop_distance * 2.0)
        elif signal == "SELL":
            entry_price = latest_price
            stop_loss = latest_price + stop_distance
            take_profit = latest_price - (stop_distance * 2.0)
        else:  # NEUTRAL
            entry_price = latest_price
            stop_loss = latest_price - stop_distance
            take_profit = latest_price + stop_distance
        
        # Step 12: Determine regime
        if latest_price > sma50 > sma200:
            regime = "UPTREND"
        elif latest_price < sma50 < sma200:
            regime = "DOWNTREND"
        else:
            regime = "MIXED"
        
        # Step 13: Return fixed response
        return {
            "symbol": symbol.upper(),
            "confidence_score": _safe_float(confidence_score, 50.0),
            "probability_up": _safe_float(prob_up, 0.5),
            "probability_down": _safe_float(prob_down, 0.5),
            "signal": signal,
            "news_sentiment_score": _safe_float(sentiment_score, 0.0),
            "news_sentiment_label": news_label,
            "latest_price": _safe_float(latest_price, 0.0),
            "timestamp": datetime.now().isoformat(),
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/batch-live")
async def batch_predictions_live(symbols: str = "RELIANCE,TCS,INFY"):
    """
    Batch live predictions with fresh data for multiple stocks
    
    Usage: /batch-live?symbols=RELIANCE,TCS,INFY,WIPRO
    """
    syms = [s.strip().upper() for s in symbols.split(",")]
    results = []
    errors = []
    
    for sym in syms:
        try:
            # Call the fixed prediction endpoint
            pred = await predict_live(sym)
            results.append(pred)
        except HTTPException as e:
            errors.append({"symbol": sym, "error": e.detail})
        except Exception as e:
            errors.append({"symbol": sym, "error": str(e)})
    
    return {
        "predictions": results,
        "errors": errors,
        "timestamp": datetime.now().isoformat(),
        "count": len(results),
        "total_requested": len(syms)
    }


@app.get("/signals-live")
async def get_signals_live(limit: int = 8):
    """
    Get live signals for top tracked symbols with fresh predictions
    """
    symbols = TRACKED_SYMBOLS[:limit]
    results = []
    
    for sym in symbols:
        try:
            pred = await predict_live(sym)
            results.append(pred)
        except:
            pass
    
    # Sort by confidence descending
    results.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
    
    return {
        "signals": results,
        "timestamp": datetime.now().isoformat(),
        "count": len(results)
    }

# ==================== END OF CODE TO COPY ====================

# Add this import at the top of api/app.py if not already there:
# from datetime import datetime
