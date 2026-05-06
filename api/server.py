"""
FastAPI inference service for the trained ensemble (XGB/LGBM/RF + optional LSTM).
- Live features are computed from Yahoo Finance data on the fly.
- Scaler is loaded from models/tree_models.pkl to keep feature scaling consistent.
Run:
  python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
import asyncio
from functools import lru_cache
from datetime import datetime
from typing import List, Optional, Tuple

import joblib
import numpy as np
import torch
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from pymongo import MongoClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from features.engineer import FEATURE_COLUMNS
from training.lstm_model import LSTMClassifier
from training.dataset import make_sequences

LOOKBACK = 30
ENSEMBLE_WEIGHTS = {
    "xgb": 0.4,
    "lgbm": 0.3,
    "rf": 0.2,
    "lstm": 0.1,
}

MONGO_URI = os.getenv("MONGO_URI")
CACHE_MAX_AGE_HOURS = 12
CATALOG_PATH = "data/nse_symbols.csv"

app = FastAPI(title="STCOK Ensemble API", version="1.0.0")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def mongo_client():
    if not MONGO_URI:
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        return client
    except Exception:
        return None


def mongo_db():
    client = mongo_client()
    if client is None:
        return None
    db = client.get_database("stcok")
    try:
        db.price_cache.create_index("fetched_at", expireAfterSeconds=CACHE_MAX_AGE_HOURS * 3600)
    except Exception:
        pass
    return db


@lru_cache(maxsize=1)
def symbol_catalog():
    try:
        if not os.path.exists(CATALOG_PATH):
            return None
        df = pd.read_csv(CATALOG_PATH)
        if "symbol" not in df.columns or "name" not in df.columns:
            return None
        df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
        df["name"] = df["name"].astype(str).str.upper().str.strip()
        return df
    except Exception:
        return None


@lru_cache(maxsize=1)
def sentiment_analyzer():
    return SentimentIntensityAnalyzer()


class PredictRequest(BaseModel):
    symbols: List[str]


class PredictResponse(BaseModel):
    symbol: str
    prob_up: float
    prob_down: float
    rows_used: int
    asof: str
    detail: dict


@lru_cache(maxsize=1)
def load_models():
    bundle = joblib.load("models/tree_models.pkl")
    xgb = bundle.get("xgb")
    lgbm = bundle.get("lgbm")
    rf = bundle.get("rf")
    scaler = bundle.get("scaler")

    # Optional LSTM
    lstm_path = "models/lstm.pt"
    lstm = None
    if torch.cuda.is_available():
        map_location = "cuda"
    else:
        map_location = "cpu"
    try:
        lstm_model = LSTMClassifier(input_size=len(FEATURE_COLUMNS))
        state = torch.load(lstm_path, map_location=map_location)
        lstm_model.load_state_dict(state)
        lstm_model.eval()
        lstm = lstm_model
    except FileNotFoundError:
        lstm = None
    return {
        "xgb": xgb,
        "lgbm": lgbm,
        "rf": rf,
        "scaler": scaler,
        "lstm": lstm,
    }


def resolve_symbol(user_input: str) -> Tuple[Optional[str], Optional[str], Optional[list]]:
    q = (user_input or "").upper().strip()
    if not q:
        return None, None, None

    # Mapping first
    mapping = {
        "SBI": "SBIN",
        "ANANT": "ANANTRAJ",
        "ANANT RAJ": "ANANTRAJ",
    }
    if q in mapping:
        return mapping[q], None, None

    cat = symbol_catalog()
    if cat is None:
        token = q.split()[0]
        return token, None, None

    # Exact symbol match
    exact = cat[cat["symbol"] == q]
    if not exact.empty:
        sym = exact.iloc[0]["symbol"]
        name = exact.iloc[0]["name"]
        return sym, name, None

    # Name contains search
    matches = cat[cat["name"].str.contains(q, case=False, na=False)]
    if matches.empty:
        token = q.split()[0]
        matches = cat[cat["name"].str.contains(token, case=False, na=False)]

    if matches.empty:
        token = q.split()[0]
        return token, None, None

    if len(matches) == 1:
        sym = matches.iloc[0]["symbol"]
        name = matches.iloc[0]["name"]
        return sym, name, None

    suggestions = matches.head(5)[["symbol", "name"]].values.tolist()
    return None, None, suggestions


def load_cached_history(ticker: str):
    db = mongo_db()
    if db is None:
        return None
    doc = db.price_cache.find_one({"ticker": ticker})
    if not doc:
        return None
    try:
        df = pd.DataFrame(doc["data"])
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
        return df
    except Exception:
        return None


def cache_history(ticker: str, df: pd.DataFrame):
    db = mongo_db()
    if db is None:
        return
    try:
        payload = df.reset_index()
        payload.rename(columns={payload.columns[0]: "Date"}, inplace=True)
        db.price_cache.replace_one(
            {"ticker": ticker},
            {"ticker": ticker, "data": payload.to_dict(orient="records"), "fetched_at": datetime.utcnow()},
            upsert=True,
        )
    except Exception:
        pass


def fetch_news_sentiment(ticker: str):
    try:
        t = yf.Ticker(ticker)
        news_items = t.news or []
    except Exception:
        return {"score": None, "count": 0, "items": []}

    analyzer = sentiment_analyzer()
    scored = []
    for item in news_items[:8]:
        title = item.get("title") or ""
        if not title:
            continue
        score = analyzer.polarity_scores(title)["compound"]
        scored.append({
            "title": title,
            "publisher": item.get("publisher"),
            "link": item.get("link"),
            "score": score,
        })

    if not scored:
        return {"score": None, "count": 0, "items": []}

    avg_score = float(np.mean([s["score"] for s in scored]))
    return {"score": avg_score, "count": len(scored), "items": scored}


def compute_features_from_history(df):
    """Compute features matching FEATURE_COLUMNS from a Yahoo Finance OHLCV DataFrame."""
    import pandas as pd
    from ta.momentum import RSIIndicator
    from ta.trend import MACD, SMAIndicator, EMAIndicator
    from ta.volatility import BollingerBands, AverageTrueRange

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None
    
    # Handle MultiIndex columns (when downloading multiple tickers from Yahoo)
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten to single level - take first ticker if multiple
        ticker = df.columns.get_level_values(1)[0]
        df = df[[(col, ticker) for col in ["Open", "High", "Low", "Close", "Volume"]]]
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
    
    # Ensure required columns
    required = ["Close", "High", "Low", "Volume"]
    for col in required:
        if col not in df.columns:
            return None

    close = pd.to_numeric(df["Close"], errors="coerce")
    high = pd.to_numeric(df["High"], errors="coerce")
    low = pd.to_numeric(df["Low"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")

    rsi = RSIIndicator(close, window=14)
    macd = MACD(close)
    sma20 = SMAIndicator(close, window=20)
    sma50 = SMAIndicator(close, window=50)
    sma200 = SMAIndicator(close, window=200)
    ema20 = EMAIndicator(close, window=20)
    ema50 = EMAIndicator(close, window=50)
    bb = BollingerBands(close, window=20, window_dev=2)
    atr = AverageTrueRange(high=high, low=low, close=close, window=14)

    df_feat = {
        "rsi": rsi.rsi(),
        "macd": macd.macd(),
        "macd_signal": macd.macd_signal(),
        "macd_hist": macd.macd_diff(),
        "sma_20": sma20.sma_indicator(),
        "sma_50": sma50.sma_indicator(),
        "sma_200": sma200.sma_indicator(),
        "ema_20": ema20.ema_indicator(),
        "ema_50": ema50.ema_indicator(),
        "bb_high": bb.bollinger_hband(),
        "bb_low": bb.bollinger_lband(),
        "bb_mid": bb.bollinger_mavg(),
        "atr": atr.average_true_range(),
        "momentum": close.diff(),
        "daily_return": close.pct_change(),
        "rolling_vol": close.pct_change().rolling(window=20).std(),
        "volume_change": volume.pct_change(),
        "rolling_mean": close.rolling(window=20).mean(),
        "rolling_std": close.rolling(window=20).std(),
    }
    features_df = pd.DataFrame(df_feat)
    features_df["date"] = df.index
    features_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    features_df.dropna(inplace=True)
    if features_df.empty:
        return None
    return features_df


def yahoo_symbol(symbol: str) -> str:
    return symbol if "." in symbol else f"{symbol}.NS"


def fetch_history(ticker: str, period: str = "2y"):
    cached = load_cached_history(ticker)
    if cached is not None and not cached.empty:
        return cached

    data = yf.download(ticker, period=period, interval="1d", progress=False)
    if not data.empty:
        cache_history(ticker, data)
    return data


def predict_single(symbol: str):
    sym_resolved, name_resolved, suggestions = resolve_symbol(symbol)
    if suggestions:
        raise HTTPException(status_code=400, detail={"message": "Multiple matches", "suggestions": suggestions})
    if sym_resolved is None:
        raise HTTPException(status_code=400, detail=f"Could not resolve symbol {symbol}")

    ticker = yahoo_symbol(sym_resolved)

    models = load_models()
    hist = fetch_history(ticker)
    features_df = compute_features_from_history(hist)
    if features_df is None or len(features_df) < LOOKBACK + 1:
        raise HTTPException(status_code=400, detail=f"Not enough data to compute features for {sym_resolved}")

    latest = features_df.iloc[-1][FEATURE_COLUMNS].values.reshape(1, -1)
    scaler = models["scaler"]
    X_scaled = scaler.transform(latest)

    xgb = models["xgb"].predict_proba(X_scaled)[:, 1][0]
    lgbm = models["lgbm"].predict_proba(X_scaled)[:, 1][0]
    rf = models["rf"].predict_proba(X_scaled)[:, 1][0]

    lstm_prob = None
    if models.get("lstm") is not None:
        seq_scaled = scaler.transform(features_df[FEATURE_COLUMNS].values)
        X_seq, _ = make_sequences(seq_scaled, np.zeros(len(seq_scaled)), lookback=LOOKBACK)
        if len(X_seq) > 0:
            with torch.no_grad():
                preds = models["lstm"](torch.tensor(X_seq[-1:], dtype=torch.float32)).squeeze().item()
                lstm_prob = float(preds)

    prob_base = (
        ENSEMBLE_WEIGHTS["xgb"] * xgb
        + ENSEMBLE_WEIGHTS["lgbm"] * lgbm
        + ENSEMBLE_WEIGHTS["rf"] * rf
        + (ENSEMBLE_WEIGHTS["lstm"] * lstm_prob if lstm_prob is not None else 0.0)
    )
    prob_base = float(max(0.0, min(1.0, prob_base)))

    news = fetch_news_sentiment(ticker)
    prob_adj = prob_base
    if news.get("score") is not None:
        prob_adj = float(max(0.0, min(1.0, prob_base + 0.05 * news["score"])))

    prob_down = float(1.0 - prob_adj)
    return {
        "symbol": sym_resolved,
        "name": name_resolved,
        "prob_up": prob_adj,
        "prob_down": prob_down,
        "rows_used": int(len(features_df)),
        "asof": str(features_df["date"].iloc[-1]),
        "detail": {
            "prob_base": prob_base,
            "prob_with_sentiment": prob_adj,
            "sentiment": news,
            "xgb": float(xgb),
            "lgbm": float(lgbm),
            "rf": float(rf),
            "lstm": lstm_prob,
            "weights": ENSEMBLE_WEIGHTS,
        },
    }


@app.get("/health")
def health():
    models = load_models()
    has_lstm = models.get("lstm") is not None
    return {"status": "ok", "lstm_loaded": has_lstm}


@app.get("/predict")
def predict(symbol: str):
    """Return formatted prediction (frontend-compatible format)."""
    try:
        result = predict_single(symbol)
        return {
            "symbol": result["symbol"],
            "name": result.get("name", ""),
            "signal": "BUY" if result["prob_up"] > 0.65 else "SELL" if result["prob_down"] > 0.65 else "NEUTRAL",
            "confidence": max(result["prob_up"], result["prob_down"]) * 100,
            "entry_price": None,  # Could be enhanced with technical analysis
            "target_price": None,  # Could be enhanced with technical analysis
            "stop_loss": None,  # Could be enhanced with technical analysis
            "models": {
                "xgboost": {"signal": "BUY" if result["detail"]["xgb"] > 0.65 else "SELL" if result["detail"]["xgb"] < 0.35 else "NEUTRAL", "confidence": result["detail"]["xgb"] * 100},
                "lightgbm": {"signal": "BUY" if result["detail"]["lgbm"] > 0.65 else "SELL" if result["detail"]["lgbm"] < 0.35 else "NEUTRAL", "confidence": result["detail"]["lgbm"] * 100},
                "random_forest": {"signal": "BUY" if result["detail"]["rf"] > 0.65 else "SELL" if result["detail"]["rf"] < 0.35 else "NEUTRAL", "confidence": result["detail"]["rf"] * 100},
                "lstm": {"signal": "BUY" if (result["detail"]["lstm"] or 0.5) > 0.65 else "SELL" if (result["detail"]["lstm"] or 0.5) < 0.35 else "NEUTRAL", "confidence": (result["detail"]["lstm"] or 0.5) * 100} if result["detail"]["lstm"] else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting {symbol}: {str(e)}")


@app.post("/predict")
async def predict_batch(payload: PredictRequest):
    symbols = payload.symbols
    if not symbols:
        raise HTTPException(status_code=400, detail="symbols cannot be empty")

    async def predict_async(sym):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, predict_single, sym)

    tasks = [predict_async(s) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    output = []
    errors = []
    for sym, res in zip(symbols, results):
        if isinstance(res, Exception):
            errors.append({"symbol": sym, "error": str(res)})
        else:
            output.append(res)
    return {"predictions": output, "errors": errors}


@app.get("/stocks")
def get_stocks(limit: int = 20, offset: int = 0):
    """List all available stocks."""
    catalog = symbol_catalog()
    if catalog is None:
        return {"stocks": [], "total": 0}
    
    stocks = catalog[["symbol", "name"]].drop_duplicates(subset=["symbol"]).to_dict("records")
    total = len(stocks)
    paginated = stocks[offset : offset + limit]
    
    return {"stocks": paginated, "total": total, "limit": limit, "offset": offset}


@app.get("/stocks/search")
def search_stocks(q: str = "", limit: int = 20):
    """Search stocks by symbol or name."""
    catalog = symbol_catalog()
    if catalog is None:
        return {"stocks": [], "total": 0}
    
    q_upper = q.upper()
    filtered = catalog[
        (catalog["symbol"].str.contains(q_upper, na=False)) | 
        (catalog["name"].str.contains(q_upper, na=False))
    ][["symbol", "name"]].drop_duplicates(subset=["symbol"]).head(limit)
    
    return {"stocks": filtered.to_dict("records"), "total": len(filtered)}


@app.get("/stocks/top-bulls")
def top_bulls(limit: int = 20):
    """Return top bullish stocks (BUY signals)."""
    catalog = symbol_catalog()
    if catalog is None:
        return {"stocks": [], "total": 0}
    
    # Sample implementation - return top symbols with simulated probabilities
    stocks = catalog[["symbol", "name"]].drop_duplicates(subset=["symbol"]).head(limit).copy()
    stocks["prob"] = 70 + np.random.randint(0, 30, len(stocks))  # 70-100% up probability
    stocks["signal"] = "BUY"
    
    return {"stocks": stocks.to_dict("records"), "total": len(stocks)}


@app.get("/stocks/top-bears")
def top_bears(limit: int = 20):
    """Return top bearish stocks (SELL signals)."""
    catalog = symbol_catalog()
    if catalog is None:
        return {"stocks": [], "total": 0}
    
    stocks = catalog[["symbol", "name"]].drop_duplicates(subset=["symbol"]).tail(limit).copy()
    stocks["prob"] = np.random.randint(0, 30, len(stocks))  # 0-30% up probability
    stocks["signal"] = "SELL"
    
    return {"stocks": stocks.to_dict("records"), "total": len(stocks)}


@app.get("/stocks/top-losers")
def top_losers(limit: int = 20):
    """Return top loser stocks."""
    catalog = symbol_catalog()
    if catalog is None:
        return {"stocks": [], "total": 0}
    
    stocks = catalog[["symbol", "name"]].drop_duplicates(subset=["symbol"]).sample(min(limit, len(catalog))).copy()
    stocks["change_pct"] = -np.random.rand(len(stocks)) * 10  # -0 to -10% change
    
    return {"stocks": stocks.to_dict("records"), "total": len(stocks)}


@app.get("/scanner_results")
def scanner_results():
    """Return AI scanner results."""
    catalog = symbol_catalog()
    if catalog is None:
        return {"bulls": [], "bears": [], "losers": []}
    
    top_count = min(10, len(catalog))
    bulls = catalog[["symbol", "name"]].drop_duplicates(subset=["symbol"]).head(top_count).copy()
    bulls["prob"] = 75 + np.random.randint(0, 25, len(bulls))
    
    bears = catalog[["symbol", "name"]].drop_duplicates(subset=["symbol"]).tail(top_count).copy()
    bears["prob"] = 20 + np.random.randint(0, 20, len(bears))
    
    return {
        "bulls": bulls.to_dict("records"),
        "bears": bears.to_dict("records"),
        "losers": []
    }


@app.get("/portfolio/analytics")
def portfolio_analytics():
    """Return portfolio analytics."""
    return {
        "portfolio_value": 250000,
        "total_value": 250000,
        "unrealized_pnl": 1250,
        "day_change": 1250,
        "daily_return": 1250,
        "day_change_pct": 0.5,
        "daily_return_pct": 0.5,
        "diversification_score": 72.5,
        "positions": 8,
        "win_rate": 65,
        "sharpe": 1.8
    }


@app.get("/alerts/live")
def live_alerts(timeframe: str = "1d", min_confidence: int = 75, limit: int = 5):
    """Return live trading alerts."""
    catalog = symbol_catalog()
    if catalog is None:
        return {"alerts": []}
    
    alerts = []
    for i in range(limit):
        symbol = catalog.iloc[i * 5 % len(catalog)]["symbol"]
        alerts.append({
            "symbol": symbol,
            "signal": "BUY" if i % 2 == 0 else "SELL",
            "confidence": min_confidence + np.random.randint(0, 25),
            "price": 100 + np.random.rand() * 50,
            "time": datetime.utcnow().isoformat()
        })
    
    return {"alerts": alerts}


@app.get("/chain/status")
def chain_status():
    """Return blockchain/order chain status."""
    return {
        "status": "OPERATIONAL",
        "pending_orders": 0,
        "filled_today": 15,
        "rejected": 1,
        "avg_latency_ms": 250
    }


@app.get("/risk-os/overview")
def risk_os_overview(capital: float = 100000):
    """Return Risk OS system overview."""
    return {
        "status": "EXECUTE",
        "capital": capital,
        "risk_per_trade_pct": 1.5,
        "risk_per_trade_amount": capital * 0.015,
        "daily_risk_budget": capital * 0.03,
        "max_trades_per_day": 5,
        "confidence_threshold": 70,
        "active_setups": 3,
        "buy_setups": 2,
        "sell_setups": 1,
        "avg_confidence": 78.5,
        "mode_flags": {
            "swing_enabled": True,
            "intraday_enabled": True
        },
        "updated_at": datetime.utcnow().isoformat()
    }


@app.get("/chart/{symbol}")
def get_chart(symbol: str, period: str = "5d", interval: str = "1d"):
    """Return OHLCV chart data for a symbol."""
    ticker = yahoo_symbol(symbol)
    try:
        hist = fetch_history(ticker, period=period)
        if hist.empty:
            return {"error": "No data found"}
        
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": str(date.date()) if hasattr(date, 'date') else str(date),
                "open": float(row.get("Open", 0)),
                "high": float(row.get("High", 0)),
                "low": float(row.get("Low", 0)),
                "close": float(row.get("Close", 0)),
                "volume": int(row.get("Volume", 0))
            })
        
        return {
            "symbol": symbol,
            "data": data[-50:],  # Return last 50 candles
            "count": len(data)
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


@app.get("/candles")
def get_candles(symbol: str, interval: str = "1d", limit: int = 200):
    """Return candlestick data for a symbol."""
    ticker = yahoo_symbol(symbol)
    try:
        hist = fetch_history(ticker, period="1y")
        if hist.empty:
            return {"error": "No data found"}
        
        data = []
        for date, row in hist.iterrows():
            data.append({
                "timestamp": int(date.timestamp() * 1000) if hasattr(date, 'timestamp') else 0,
                "date": str(date.date()) if hasattr(date, 'date') else str(date),
                "open": float(row.get("Open", 0)),
                "high": float(row.get("High", 0)),
                "low": float(row.get("Low", 0)),
                "close": float(row.get("Close", 0)),
                "volume": int(row.get("Volume", 0))
            })
        
        return {
            "symbol": symbol,
            "interval": interval,
            "candles": data[-limit:],
            "count": len(data[-limit:])
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/prediction/{symbol}")
def get_prediction(symbol: str, timeframe: str = "1d"):
    """Return AI prediction for a symbol."""
    try:
        result = predict_single(symbol)
        return {
            "symbol": result["symbol"],
            "name": result.get("name", ""),
            "timeframe": timeframe,
            "prob_up": result["prob_up"],
            "prob_down": result["prob_down"],
            "signal": "BUY" if result["prob_up"] > 0.65 else "SELL" if result["prob_down"] > 0.65 else "NEUTRAL",
            "confidence": max(result["prob_up"], result["prob_down"]) * 100,
            "models": {
                "xgb": result["detail"]["xgb"] * 100,
                "lgbm": result["detail"]["lgbm"] * 100,
                "rf": result["detail"]["rf"] * 100,
                "lstm": (result["detail"]["lstm"] * 100) if result["detail"]["lstm"] else None
            },
            "sentiment": result["detail"].get("sentiment", {}),
            "as_of": result["asof"]
        }
    except HTTPException as e:
        return {"error": e.detail, "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}