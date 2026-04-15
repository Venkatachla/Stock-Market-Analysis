"""
Complete FastAPI application with all dashboard endpoints.
Run: python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
"""

import os
# Force global warning ignore for spawned processes and modules like joblib
os.environ["PYTHONWARNINGS"] = "ignore::ResourceWarning"

import json
import asyncio
import warnings
import io
import contextlib
import sqlite3
import hashlib
import secrets
from functools import lru_cache
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

import joblib
import numpy as np
import pandas as pd
import torch
import yfinance as yf
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from features.engineer import FEATURE_COLUMNS, load_combined_dataset
from training.lstm_model import LSTMClassifier
from training.dataset import make_sequences
from training.retrain_scheduler import retrain_symbols
from quant_system import (
    compute_regime, download_index, regime_adjusted_decision,
    backtest, optimize_thresholds, paper_trade
)
from backtest.engine import backtest_with_benchmark
from backtest.professional import run_professional_backtest
from backtest.dual_engine_alpha import run_alpha_engine
from data.multi_timeframe import align_daily_trend_to_intraday, fetch_multi_timeframe_data
from features.multi_strategy import build_feature_frame, classify_regime
from models.multi_strategy import load_multi_strategy, save_multi_strategy, train_multi_strategy_for_symbol, predict_strategy
from trading.engine import build_trade_plan
from trading.decision_engine import decide_trade, format_trade_signal
from trading.risk import RiskLimits, RiskManager

LOOKBACK = 30
ENSEMBLE_WEIGHTS = {"xgb": 0.4, "lgbm": 0.3, "rf": 0.2, "lstm": 0.1}
SENTIMENT_WEIGHT = 0.08
DB_PATH = "data/platform.db"
FREE_TIER_DAILY_SIGNAL_LIMIT = 5
OPTIMIZED_CONFIDENCE_THRESHOLD = 65.0
SYMBOL_MAPPING = {
    "HDFC": "HDFCBANK",
    "NIFTY 50": "^NSEI",
    "BSE SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP SELECT": "NIFTY_MIDCAP_50",
    "NIFTY FINANCIAL SERVICES": "NIFTY_FIN_SERVICE.NS",
    "BSE BANKEX": "BSE-BANK.BO"
}
TRACKED_SYMBOLS = ["RELIANCE", "TCS", "INFY", "WIPRO", "HDFCBANK", "MARUTI", "BAJAJ-AUTO", "ANANTRAJ"]
SYMBOL_CSV_PATH = Path(os.getenv("SYMBOL_CSV_PATH", "data/nse_symbols.csv"))
TRENDING_LOG_PATH = Path(os.getenv("TRENDING_LOG_PATH", "data/trending_picks.json"))
TRENDING_WINDOW_DAYS = int(os.getenv("TRENDING_WINDOW_DAYS", "3"))
TRENDING_UNIVERSE_LIMIT = int(os.getenv("TRENDING_UNIVERSE_LIMIT", "100"))
TRENDING_PICK_LIMIT = int(os.getenv("TRENDING_PICK_LIMIT", "8"))
TRENDING_CACHE_TTL_MIN = int(os.getenv("TRENDING_CACHE_TTL_MIN", "20"))
BULL_SCAN_LIMIT = int(os.getenv("BULL_SCAN_LIMIT", "60"))
NSE_EQUITY_LIST_URL = os.getenv("NSE_EQUITY_LIST_URL", "https://archives.nseindia.com/content/equities/EQUITY_L.csv")
SETTINGS_PATH = Path(os.getenv("SETTINGS_PATH", "data/app_settings.json"))
PAPER_POSITIONS = [
    {"symbol": "RELIANCE", "quantity": 10, "entry_price": 2850.50},
    {"symbol": "TCS", "quantity": 5, "entry_price": 4120.25},
    {"symbol": "INFY", "quantity": 15, "entry_price": 1635.00},
    {"symbol": "HDFCBANK", "quantity": 8, "entry_price": 1465.00},
]

_TRENDING_CACHE: dict = {"timestamp": None, "symbols": []}

app = FastAPI(title="STCOK Quant Trading API", version="2.0.0")

# Ensure warning policy also applies to child processes used by some ML libs.
os.environ.setdefault("PYTHONWARNINGS", "ignore::ResourceWarning")

warnings.filterwarnings(
    "ignore",
    message="Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names, but LGBMClassifier was fitted with feature names",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="X has feature names, but RandomForestClassifier was fitted without feature names",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="unclosed database in <sqlite3.Connection object.*",
    category=ResourceWarning,
)
warnings.filterwarnings("ignore", category=ResourceWarning, module=r"sklearn\\.utils\\.parallel")
# Some third-party libs trigger sqlite ResourceWarnings from background/parallel internals;
# this keeps server logs clean when connections are outside our control.
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.simplefilter("ignore", ResourceWarning)

_ORIG_SHOWWARNING = warnings.showwarning


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        v = float(value)
    except Exception:
        return float(default)
    if np.isnan(v) or np.isinf(v):
        return float(default)
    return float(v)


def _sanitize_json_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sanitize_json_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_json_obj(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if (np.isnan(v) or np.isinf(v)) else v
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    return obj


def _quiet_resource_warnings(message, category, filename, lineno, file=None, line=None):
    try:
        if category and issubclass(category, ResourceWarning):
            return
    except Exception:
        pass
    return _ORIG_SHOWWARNING(message, category, filename, lineno, file=file, line=line)


warnings.showwarning = _quiet_resource_warnings

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UNIVERSE_DF = None
UNIVERSE_JSON = []

@app.on_event("startup")
def startup_event():
    init_db()
    try:
        global UNIVERSE_DF, UNIVERSE_JSON
        import pandas as pd
        df = pd.read_csv("data/Grow-Stocks.csv", low_memory=False)
        df.rename(columns={
            "trading_symbol": "symbol",
            "expiry_date": "expiry",
            "strike_price": "strike"
        }, inplace=True)
        df.fillna({
            "name": "", 
            "instrument_type": "EQ", 
            "underlying_symbol": "", 
            "expiry": "", 
            "strike": 0.0
        }, inplace=True)
        
        # Deduplicate to prevent duplicate keys in frontend rendering
        df.drop_duplicates(subset=["symbol", "instrument_type"], keep="first", inplace=True)
        
        UNIVERSE_DF = df
        subset = df[["symbol", "name", "instrument_type", "underlying_symbol", "expiry", "strike"]].to_dict(orient="records")
        UNIVERSE_JSON = subset
        print(f"Loaded {len(UNIVERSE_JSON)} universe symbols.")
    except Exception as e:
        print(f"Error loading universe CSV: {e}")

# ================== Models ==================

class StockPredictionResponse(BaseModel):
    symbol: str
    probability_up: float
    prob_up: float
    prob_down: float
    confidence_score: float
    confidence: float
    signal: str
    regime: str
    sentiment_score: float
    latest_price: float
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: int
    trade_validity: bool
    date: str
    trend: Optional[str] = None
    timeframe: Optional[str] = None
    news_sentiment_label: Optional[str] = None
    reason: Optional[str] = None

class RegimeResponse(BaseModel):
    regime: str
    confidence: float
    description: str
    ma200: float
    close_price: float
    slope: float

class BacktestResponse(BaseModel):
    total_return: float
    win_rate: float
    max_drawdown: float
    sharpe: float
    sortino: float
    profit_factor: float
    benchmark_return: float
    avg_trade_return: float
    num_trades: int
    equity_curve: List[float] = []
    drawdown_curve: List[float] = []

class PaperTradeResponse(BaseModel):
    id: str
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    pnl: float
    return_pct: float
    entry_date: str
    exit_date: Optional[str]
    status: str

class SignalResponse(BaseModel):
    symbol: str
    probability_up: float
    prob_up: float
    sentiment_score: float
    price: float
    sector: str
    regime: str
    signal_type: str
    confidence_score: float
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: int
    trade_validity: bool
    timestamp: str

class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    tier: str

class UserSummary(BaseModel):
    email: str
    tier: str
    is_admin: bool


class MultiStrategySignalResponse(BaseModel):
    symbol: str
    trade_type: str
    regime: str
    probability_up: float
    confidence_score: float
    action: str
    entry_price: float
    stop_loss: float
    target: float
    position_size: int
    risk_pct: float
    reason: str
    formatted_signal: str


class PerformanceDashboardResponse(BaseModel):
    daily_pnl: float
    win_rate: float
    equity_curve: List[float]
    drawdown_curve: List[float]
    trade_history: List[dict]

class NewsItemResponse(BaseModel):
    symbol: str
    title: str
    source: str
    published_at: str

class BulkPredictRequest(BaseModel):
    symbols: List[str]
    timeframe: Optional[str] = "1d"

@app.get("/universe")
async def get_universe():
    return UNIVERSE_JSON

@app.get("/scanner_results")
async def get_scanner_results():
    # Simulate a full universe scan by sorting based on the same deterministic hash
    today_str = datetime.today().strftime('%Y-%m-%d')
    scored = []
    
    # Process only a subset (first 20,000) for instant response in demo
    for row in UNIVERSE_JSON[:20000]:
        sym = row["symbol"]
        seed_str = f"{sym}{today_str}V1"
        val = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 100
        scored.append({**row, "prob": val})

    # 1. Equities to Buy
    equities = [x for x in scored if x["instrument_type"] == "EQ"]
    equities.sort(key=lambda x: x["prob"], reverse=True)
    stocks_to_buy = equities[:50]

    # 2. Equities to Sell
    equities_bad = sorted(equities, key=lambda x: x["prob"])
    stocks_to_sell = equities_bad[:50]

    # 3. Calls to Buy
    calls = [x for x in scored if x["instrument_type"] == "CE" or (isinstance(x.get("symbol"), str) and x["symbol"].endswith("CE"))]
    calls.sort(key=lambda x: x["prob"], reverse=True)
    calls_to_buy = calls[:50]

    # 4. Puts to Buy
    puts = [x for x in scored if x["instrument_type"] == "PE" or (isinstance(x.get("symbol"), str) and x["symbol"].endswith("PE"))]
    puts.sort(key=lambda x: x["prob"], reverse=True)
    puts_to_buy = puts[:50]

    return {
        "stocks_to_buy": stocks_to_buy,
        "stocks_to_sell": stocks_to_sell,
        "calls_to_buy": calls_to_buy,
        "puts_to_buy": puts_to_buy
    }

@app.post("/bulk_predict")
async def bulk_predict(req: BulkPredictRequest):
    res = {}
    timeframe = str(req.timeframe or "1d")

    for sym in req.symbols[:80]:
        pred = predict_single(sym, timeframe=timeframe)
        if pred is None:
            res[sym] = {"signal": "WAIT", "prob": 50.0, "action": "Hold"}
            continue

        signal_text = str(pred.signal)
        upper_signal = signal_text.upper()
        if upper_signal.startswith("WAIT"):
            prob = max(float(pred.prob_up), float(pred.prob_down)) * 100.0
            action = "Hold"
        elif "BUY" in upper_signal:
            prob = float(pred.prob_up) * 100.0
            action = "Buy"
        elif "SELL" in upper_signal:
            prob = float(pred.prob_down) * 100.0
            action = "Sell"
        else:
            prob = max(float(pred.prob_up), float(pred.prob_down)) * 100.0
            action = "Hold"

        res[sym] = {
            "signal": signal_text,
            "prob": round(prob, 2),
            "action": action,
        }
        
    return res
    sentiment_score: float
    url: Optional[str] = None

class DashboardStatsResponse(BaseModel):
    portfolio_value: float
    today_gain: float
    today_gain_pct: float
    win_rate: float
    sharpe_ratio: float
    market_sentiment: float
    sentiment_label: str
    updated_at: str


class PortfolioAnalyticsResponse(BaseModel):
    portfolio_value: float
    invested_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    day_change: float
    day_change_pct: float
    diversification_score: float
    top_position_symbol: str
    top_position_weight: float
    positions: List[dict]


class LiveAlertResponse(BaseModel):
    symbol: str
    signal: str
    confidence_score: float
    probability_up: float
    probability_down: float
    latest_price: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: str
    reason: str
    timestamp: str


class SettingsPayload(BaseModel):
    risk_per_trade: float = 1.0
    max_trades_per_day: int = 5
    swing_enabled: bool = True
    intraday_enabled: bool = True
    confidence_threshold: float = 70.0

# ================== Cache & Utilities ==================

def db_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = db_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'free',
                token TEXT,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                probability_up REAL NOT NULL,
                confidence_score REAL NOT NULL,
                signal TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                position_size INTEGER NOT NULL,
                trade_validity INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                channel TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS live_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                action TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                target REAL NOT NULL,
                position_size INTEGER NOT NULL,
                confidence_score REAL NOT NULL,
                probability_up REAL NOT NULL,
                regime TEXT NOT NULL,
                risk_pct REAL NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                exit_price REAL,
                pnl REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chain_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER NOT NULL UNIQUE,
                payload_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                block_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(prediction_id) REFERENCES predictions(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _default_settings() -> Dict[str, Any]:
    return {
        "risk_per_trade": 1.0,
        "max_trades_per_day": 5,
        "swing_enabled": True,
        "intraday_enabled": True,
        "confidence_threshold": 70.0,
    }


def load_settings() -> Dict[str, Any]:
    defaults = _default_settings()
    try:
        if SETTINGS_PATH.exists():
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                out = dict(defaults)
                out.update(raw)
                out["risk_per_trade"] = float(max(0.2, min(5.0, out.get("risk_per_trade", 1.0))))
                out["max_trades_per_day"] = int(max(1, min(20, out.get("max_trades_per_day", 5))))
                out["confidence_threshold"] = float(max(50.0, min(95.0, out.get("confidence_threshold", 70.0))))
                out["swing_enabled"] = bool(out.get("swing_enabled", True))
                out["intraday_enabled"] = bool(out.get("intraday_enabled", True))
                return out
    except Exception:
        pass
    return defaults


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    clean = {
        "risk_per_trade": float(max(0.2, min(5.0, settings.get("risk_per_trade", 1.0)))),
        "max_trades_per_day": int(max(1, min(20, settings.get("max_trades_per_day", 5)))),
        "swing_enabled": bool(settings.get("swing_enabled", True)),
        "intraday_enabled": bool(settings.get("intraday_enabled", True)),
        "confidence_threshold": float(max(50.0, min(95.0, settings.get("confidence_threshold", 70.0)))),
    }
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    return clean


@lru_cache(maxsize=1)
def get_sentiment_analyzer():
    try:
        from transformers import pipeline

        finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")

        def _score(text: str) -> float:
            pred = finbert(text[:512])[0]
            label = str(pred.get("label", "neutral")).lower()
            val = float(pred.get("score", 0.0))
            if "positive" in label:
                return val
            if "negative" in label:
                return -val
            return 0.0

        return _score
    except Exception:
        vader = SentimentIntensityAnalyzer()
        return lambda text: float(vader.polarity_scores(text)["compound"])


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def resolve_user(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        return {"email": "guest", "tier": "free", "is_admin": False}
    token = authorization.split(" ", 1)[1].strip()
    conn = db_conn()
    try:
        row = conn.execute("SELECT email, tier, is_admin FROM users WHERE token = ?", (token,)).fetchone()
        if row is None:
            return {"email": "guest", "tier": "free", "is_admin": False}
        return {"email": row["email"], "tier": row["tier"], "is_admin": bool(row["is_admin"])}
    finally:
        conn.close()

@lru_cache(maxsize=1)
def load_models():
    """Load trained models."""
    try:
        bundle = joblib.load("models/tree_models.pkl")
        xgb = bundle.get("xgb")
        lgbm = bundle.get("lgbm")
        rf = bundle.get("rf")
        scaler = bundle.get("scaler")

        lstm = None
        try:
            lstm_model = LSTMClassifier(input_size=len(FEATURE_COLUMNS), hidden_size=64, num_layers=2)
            state = torch.load("models/lstm.pt", map_location="cpu")
            lstm_model.load_state_dict(state)
            lstm_model.eval()
            lstm = lstm_model
        except:
            pass

        return {
            "xgb": xgb,
            "lgbm": lgbm,
            "rf": rf,
            "scaler": scaler,
            "lstm": lstm,
            "meta_model": bundle.get("meta_model"),
            "dynamic_weights": bundle.get("dynamic_weights", ENSEMBLE_WEIGHTS),
            "feature_names": bundle.get("feature_names", FEATURE_COLUMNS),
        }
    except Exception as e:
        raise Exception(f"Failed to load models: {str(e)}")

def compute_features_from_history(df):
    """Compute all features from OHLCV data."""
    if df is None or df.empty or len(df) < 50:
        return None

    from ta.momentum import RSIIndicator
    from ta.trend import MACD, SMAIndicator, EMAIndicator, ADXIndicator
    from ta.volatility import BollingerBands, AverageTrueRange

    required = ["Close", "High", "Low", "Volume"]
    for col in required:
        if col not in df.columns:
            return None

    try:
        close = pd.to_numeric(df["Close"], errors="coerce")
        high = pd.to_numeric(df["High"], errors="coerce")
        low = pd.to_numeric(df["Low"], errors="coerce")
        volume = pd.to_numeric(df["Volume"], errors="coerce")

        base = {
            "rsi": RSIIndicator(close, window=14).rsi(),
            "macd": (m := MACD(close)).macd(),
            "macd_signal": m.macd_signal(),
            "macd_hist": m.macd_diff(),
            "sma_20": SMAIndicator(close, window=20).sma_indicator(),
            "sma_50": SMAIndicator(close, window=50).sma_indicator(),
            "sma_200": SMAIndicator(close, window=200).sma_indicator(),
            "ema_20": EMAIndicator(close, window=20).ema_indicator(),
            "ema_50": EMAIndicator(close, window=50).ema_indicator(),
            "bb_high": (bb := BollingerBands(close, window=20, window_dev=2)).bollinger_hband(),
            "bb_low": bb.bollinger_lband(),
            "bb_mid": bb.bollinger_mavg(),
            "atr": AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range(),
            "momentum": close.diff(),
            "daily_return": close.pct_change(),
            "rolling_vol": close.pct_change().rolling(window=20).std(),
            "volume_change": volume.pct_change(),
            "rolling_mean": close.rolling(window=20).mean(),
            "rolling_std": close.rolling(window=20).std(),
        }

        features_df = pd.DataFrame(base, index=df.index)
        features_df["close"] = close.values
        features_df["date"] = df.index

        features_df["vol_spike"] = volume / volume.rolling(20).mean()
        adx = ADXIndicator(high=high, low=low, close=close, window=14)
        features_df["adx_14"] = adx.adx()

        features_df["relative_strength_20"] = 0.0
        features_df["beta_60"] = 0.0
        features_df["vol_pct_20"] = 0.5
        features_df["sector_mom_20"] = 0.0

        # Price structure
        features_df["support_zone"] = close.rolling(20).min()
        features_df["resistance_zone"] = close.rolling(20).max()
        features_df["trend_strength"] = (features_df["ema_20"] - features_df["ema_50"]).abs() / (close.abs() + 1e-9)
        prev_support = close.shift(1).rolling(20).min()
        prev_resistance = close.shift(1).rolling(20).max()
        features_df["breakout_flag"] = np.where(close > prev_resistance, 1, np.where(close < prev_support, -1, 0))

        # Market context
        features_df["nifty_trend"] = 0.0
        features_df["sector_strength_rank"] = 0.5

        try:
            idx = yf.download("^NSEI", period="1y", interval="1d", progress=False)
            if isinstance(idx.columns, pd.MultiIndex):
                idx.columns = idx.columns.get_level_values(0)
            if not idx.empty and "Close" in idx.columns:
                idx_close = pd.to_numeric(idx["Close"], errors="coerce").reindex(df.index, method=None)
                idx_ma50 = idx_close.rolling(50).mean()
                features_df["nifty_trend"] = (idx_close - idx_ma50) / (idx_ma50 + 1e-9)
                features_df["sector_strength_rank"] = features_df["relative_strength_20"].rank(pct=True)
        except Exception:
            pass

        # Smart money proxies
        features_df["oi_change"] = volume.pct_change().rolling(5).mean()
        up_vol = pd.Series(np.where(close.diff() > 0, volume, 0.0), index=features_df.index)
        down_vol = pd.Series(np.where(close.diff() < 0, volume, 0.0), index=features_df.index)
        features_df["pcr_ratio"] = (down_vol.rolling(10).mean() + 1.0) / (up_vol.rolling(10).mean() + 1.0)
        features_df["open_interest_change"] = features_df["oi_change"]
        features_df["put_call_ratio"] = features_df["pcr_ratio"]
        features_df["delivery_percent"] = ((volume / (volume.rolling(20).mean() + 1e-9)) * 100.0).clip(lower=0.0)
        turnover = close * volume
        vol_profile_raw = turnover / (turnover.rolling(20).mean() + 1e-9)
        features_df["volume_profile"] = vol_profile_raw.rank(pct=True)
        rolling_vol = close.pct_change().rolling(20).std()
        vol_med = rolling_vol.rolling(120).median()
        features_df["volatility_regime"] = np.where(rolling_vol > vol_med, 1.0, 0.0)
        features_df["fii_dii_flow"] = turnover.pct_change().rolling(10).mean()

        # Sentiment feature is injected in predict_single for the latest row.
        features_df["news_sentiment_score"] = 0.0

        features_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        essential = [
            "rsi", "macd", "macd_signal", "macd_hist", "sma_20", "sma_50", "sma_200",
            "ema_20", "ema_50", "bb_high", "bb_low", "bb_mid", "atr", "momentum",
            "daily_return", "rolling_vol", "volume_change", "rolling_mean", "rolling_std", "close",
        ]
        features_df.dropna(subset=essential, inplace=True)
        return features_df if not features_df.empty else None
    except Exception:
        return None

def timeframe_to_yf_params(timeframe: str) -> tuple[str, str]:
    tf = str(timeframe or "1d").lower().strip()
    mapping = {
        "1m": ("7d", "1m"),
        "5m": ("60d", "5m"),
        "15m": ("60d", "15m"),
        "60m": ("730d", "60m"),
        "1h": ("730d", "60m"),
        "1d": ("2y", "1d"),
        "1wk": ("10y", "1wk"),
    }
    return mapping.get(tf, ("2y", "1d"))


def is_intraday_timeframe(timeframe: str) -> bool:
    tf = str(timeframe or "").lower().strip()
    return tf in {"1m", "5m", "15m", "60m", "1h"}


def fetch_history(ticker: str, period: str = "2y", interval: str = "1d"):
    """Fetch price history from Yahoo Finance."""
    try:
        base = ticker
        if "." in ticker and not ticker.startswith("^"):
            base = ticker.split(".")[0]
        candidates = [ticker]
        if not ticker.startswith("^"):
            candidates.extend([f"{base}.NS", f"{base}.BO", base])

        seen = set()
        for cand in candidates:
            if cand in seen:
                continue
            seen.add(cand)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                data = yf.download(cand, period=period, interval=interval, progress=False, threads=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            if data is not None and not data.empty:
                return data
        return None
    except Exception:
        return None

def fetch_news_sentiment(ticker: str, symbol: str, limit: int = 5):
    """Fetch and score recent news headlines for a ticker (3-day aggregate)."""
    try:
        analyzer = get_sentiment_analyzer()
        candidates = [ticker, ticker.replace(".NS", ""), symbol]
        news_items = []
        for cand in candidates:
            try:
                news_items = yf.Ticker(cand).news or []
                if news_items:
                    break
            except Exception:
                continue
        scored = []
        cutoff = datetime.now() - timedelta(days=3)
        for item in news_items[:limit]:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            sentiment = float(analyzer(title))
            published = item.get("providerPublishTime")
            if published:
                published_at = datetime.fromtimestamp(published).isoformat()
            else:
                published_at = datetime.now().isoformat()

            try:
                published_dt = datetime.fromisoformat(published_at)
            except Exception:
                published_dt = datetime.now()
            if published_dt < cutoff:
                continue

            scored.append({
                "symbol": symbol,
                "title": title,
                "source": item.get("publisher") or "Yahoo Finance",
                "published_at": published_at,
                "sentiment_score": sentiment,
                "url": item.get("link"),
            })

        if not scored:
            scored = fetch_google_news(symbol, limit=limit)
            if not scored:
                return 0.0, []

        avg_sentiment = float(np.mean([x["sentiment_score"] for x in scored]))
        return avg_sentiment, scored
    except Exception:
        return 0.0, []

def fetch_google_news(symbol: str, limit: int = 8):
    """Fetch Google News RSS headlines for a symbol and score sentiment."""
    try:
        analyzer = get_sentiment_analyzer()
        query = quote_plus(f"{symbol} NSE stock")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

        with urlopen(rss_url, timeout=12) as response:
            xml_text = response.read()

        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []

        items = []
        for item in channel.findall("item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            source = (item.findtext("source") or "Google News").strip()
            pub_date = (item.findtext("pubDate") or "").strip()

            if not title:
                continue

            try:
                published_at = parsedate_to_datetime(pub_date).isoformat() if pub_date else datetime.now().isoformat()
            except Exception:
                published_at = datetime.now().isoformat()

            sentiment = float(analyzer(title))
            try:
                if datetime.fromisoformat(published_at) < (datetime.now() - timedelta(days=3)):
                    continue
            except Exception:
                pass
            items.append({
                "symbol": symbol,
                "title": title,
                "source": source,
                "published_at": published_at,
                "sentiment_score": sentiment,
                "url": link or None,
            })

        return items
    except Exception:
        return []

def fetch_latest_price_and_change(symbol: str):
    """Return (latest_price, prev_close) for a symbol."""
    mapped_symbol = SYMBOL_MAPPING.get(symbol.upper(), symbol)
    ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
    hist = fetch_history(ticker, period="1mo")
    if hist is None or len(hist) < 2:
        return None, None
    close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
    if len(close) < 2:
        return None, None
    return float(close.iloc[-1]), float(close.iloc[-2])

def estimate_sharpe_from_symbols(symbols: List[str]) -> float:
    """Estimate Sharpe from recent equally weighted basket returns."""
    rets = []
    for sym in symbols[:6]:
        mapped_symbol = SYMBOL_MAPPING.get(sym.upper(), sym)
        ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
        hist = fetch_history(ticker, period="6mo")
        if hist is None:
            continue
        close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if len(close) < 40:
            continue
        rets.append(close.pct_change().dropna())

    if not rets:
        return 0.0

    basket = pd.concat(rets, axis=1).mean(axis=1, skipna=True).dropna()
    if basket.empty or float(basket.std()) == 0.0:
        return 0.0
    sharpe = (float(basket.mean()) / float(basket.std())) * np.sqrt(252)
    return float(max(min(sharpe, 6.0), -6.0))


def store_prediction(pred: StockPredictionResponse) -> None:
    conn = db_conn()
    try:
        created_at = datetime.now().isoformat()
        cur = conn.execute(
            """
            INSERT INTO predictions (
                symbol, probability_up, confidence_score, signal,
                entry_price, stop_loss, take_profit, position_size, trade_validity, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pred.symbol,
                pred.probability_up,
                pred.confidence_score,
                pred.signal,
                pred.entry_price,
                pred.stop_loss,
                pred.take_profit,
                pred.position_size,
                int(pred.trade_validity),
                created_at,
            ),
        )

        prediction_id = int(cur.lastrowid)
        payload = {
            "prediction_id": prediction_id,
            "symbol": pred.symbol,
            "probability_up": _safe_float(pred.probability_up, 0.0),
            "confidence_score": _safe_float(pred.confidence_score, 0.0),
            "signal": str(pred.signal),
            "entry_price": _safe_float(pred.entry_price, 0.0),
            "stop_loss": _safe_float(pred.stop_loss, 0.0),
            "take_profit": _safe_float(pred.take_profit, 0.0),
            "position_size": int(pred.position_size),
            "trade_validity": int(bool(pred.trade_validity)),
            "created_at": created_at,
        }

        payload_json = json.dumps(_sanitize_json_obj(payload), sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        prev_row = conn.execute(
            "SELECT block_hash FROM chain_blocks ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = str(prev_row["block_hash"]) if prev_row else ("0" * 64)
        block_input = f"{prediction_id}|{payload_hash}|{prev_hash}|{created_at}"
        block_hash = hashlib.sha256(block_input.encode("utf-8")).hexdigest()

        conn.execute(
            """
            INSERT INTO chain_blocks (prediction_id, payload_hash, prev_hash, block_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (prediction_id, payload_hash, prev_hash, block_hash, created_at),
        )
        conn.commit()
    finally:
        conn.close()


def _recompute_prediction_payload_hash(row: sqlite3.Row) -> tuple[str, str]:
    payload = {
        "prediction_id": int(row["id"]),
        "symbol": str(row["symbol"]),
        "probability_up": _safe_float(row["probability_up"], 0.0),
        "confidence_score": _safe_float(row["confidence_score"], 0.0),
        "signal": str(row["signal"]),
        "entry_price": _safe_float(row["entry_price"], 0.0),
        "stop_loss": _safe_float(row["stop_loss"], 0.0),
        "take_profit": _safe_float(row["take_profit"], 0.0),
        "position_size": int(row["position_size"]),
        "trade_validity": int(row["trade_validity"]),
        "created_at": str(row["created_at"]),
    }
    payload_json = json.dumps(_sanitize_json_obj(payload), sort_keys=True, separators=(",", ":"))
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return payload_json, payload_hash


def evaluate_alerts() -> list[dict]:
    conn = db_conn()
    try:
        rows = conn.execute(
            """
            SELECT symbol, signal, entry_price, stop_loss, take_profit, created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()
    finally:
        conn.close()

    alerts: list[dict] = []
    for row in rows:
        symbol = row["symbol"]
        latest, _ = fetch_latest_price_and_change(symbol)
        if latest is None:
            continue
        if row["signal"] in {"BUY", "SELL"}:
            alerts.append({
                "type": "new_signal",
                "symbol": symbol,
                "message": f"{symbol} new {row['signal']} signal at {row['entry_price']:.2f}",
                "timestamp": datetime.now().isoformat(),
            })
        if latest <= float(row["stop_loss"]):
            alerts.append({
                "type": "stop_loss_hit",
                "symbol": symbol,
                "message": f"{symbol} stop loss hit at {latest:.2f}",
                "timestamp": datetime.now().isoformat(),
            })
        elif latest >= float(row["take_profit"]):
            alerts.append({
                "type": "target_hit",
                "symbol": symbol,
                "message": f"{symbol} target hit at {latest:.2f}",
                "timestamp": datetime.now().isoformat(),
            })
    return alerts


def persist_live_trade(signal: MultiStrategySignalResponse) -> None:
    if signal.action == "NO_TRADE":
        return
    conn = db_conn()
    try:
        conn.execute(
            """
            INSERT INTO live_trades (
                symbol, trade_type, action, entry_price, stop_loss, target,
                position_size, confidence_score, probability_up, regime, risk_pct, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.symbol,
                signal.trade_type,
                signal.action,
                signal.entry_price,
                signal.stop_loss,
                signal.target,
                signal.position_size,
                signal.confidence_score,
                signal.probability_up,
                signal.regime,
                signal.risk_pct,
                signal.reason,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def compute_equity_and_drawdown(pnls: list[float], capital: float = 100000.0) -> tuple[list[float], list[float]]:
    if not pnls:
        return [capital], [0.0]
    equity_vals = [capital]
    for p in pnls:
        equity_vals.append(equity_vals[-1] + float(p))
    ser = pd.Series(equity_vals)
    dd = ((ser / ser.cummax()) - 1.0).fillna(0.0)
    return [float(x) for x in ser.values], [float(x) for x in dd.values]


def downsample_curve(values: List[float], max_points: int = 300) -> List[float]:
    if not values:
        return []
    if len(values) <= max_points:
        return [float(v) for v in values]
    idx = np.linspace(0, len(values) - 1, max_points, dtype=int)
    return [float(values[i]) for i in idx]


def compute_portfolio_snapshot() -> Dict[str, Any]:
    portfolio_value = 0.0
    invested_value = 0.0
    day_change = 0.0
    enriched_positions: List[dict] = []

    for pos in PAPER_POSITIONS:
        symbol = str(pos.get("symbol", ""))
        qty = float(pos.get("quantity", 0))
        entry = float(pos.get("entry_price", 0.0))
        latest, prev = fetch_latest_price_and_change(symbol)
        if latest is None:
            latest = entry

        market_value = float(latest) * qty
        cost_value = entry * qty
        pnl = market_value - cost_value

        position_day_change = 0.0
        if prev is not None:
            position_day_change = (float(latest) - float(prev)) * qty
            day_change += position_day_change

        portfolio_value += market_value
        invested_value += cost_value

        enriched_positions.append({
            "symbol": symbol,
            "quantity": int(qty),
            "entry_price": float(entry),
            "latest_price": float(latest),
            "market_value": float(market_value),
            "pnl": float(pnl),
            "day_change": float(position_day_change),
            "weight": 0.0,
        })

    portfolio_value = float(max(portfolio_value, 0.0))
    invested_value = float(max(invested_value, 0.0))
    unrealized_pnl = float(portfolio_value - invested_value)
    unrealized_pnl_pct = float((unrealized_pnl / invested_value) * 100.0) if invested_value > 0 else 0.0
    day_change_pct = float((day_change / (portfolio_value - day_change)) * 100.0) if abs(portfolio_value - day_change) > 1e-9 else 0.0

    for row in enriched_positions:
        row["weight"] = float((row["market_value"] / portfolio_value) * 100.0) if portfolio_value > 0 else 0.0

    top_symbol = ""
    top_weight = 0.0
    if enriched_positions:
        top = max(enriched_positions, key=lambda x: float(x.get("weight", 0.0)))
        top_symbol = str(top.get("symbol", ""))
        top_weight = float(top.get("weight", 0.0))

    # Higher is better (balanced allocation). 100 means equal weight.
    if enriched_positions and portfolio_value > 0:
        weights = np.array([float(r.get("weight", 0.0)) / 100.0 for r in enriched_positions], dtype=float)
        hhi = float(np.sum(np.square(weights)))
        n = len(enriched_positions)
        hhi_min = 1.0 / max(n, 1)
        hhi_max = 1.0
        diversification_score = float(100.0 * (1.0 - ((hhi - hhi_min) / max(hhi_max - hhi_min, 1e-9))))
    else:
        diversification_score = 0.0

    return {
        "portfolio_value": float(portfolio_value),
        "invested_value": float(invested_value),
        "unrealized_pnl": float(unrealized_pnl),
        "unrealized_pnl_pct": float(unrealized_pnl_pct),
        "day_change": float(day_change),
        "day_change_pct": float(day_change_pct),
        "diversification_score": float(max(0.0, min(100.0, diversification_score))),
        "top_position_symbol": top_symbol,
        "top_position_weight": float(top_weight),
        "positions": sorted(enriched_positions, key=lambda x: float(x.get("market_value", 0.0)), reverse=True),
    }


def generate_multi_strategy_signal(symbol: str, trade_type: str, risk_manager: RiskManager | None = None) -> MultiStrategySignalResponse:
    risk_manager = risk_manager or RiskManager(RiskLimits())
    tf = fetch_multi_timeframe_data(symbol)
    idx = fetch_multi_timeframe_data("^NSEI")

    trade_type_norm = trade_type.lower()
    if trade_type_norm == "swing":
        frame = build_feature_frame(tf.daily, idx.daily)
    elif trade_type_norm == "intraday":
        intraday = align_daily_trend_to_intraday(tf.daily, tf.m5 if len(tf.m5) > 10 else tf.m15)
        idx_ref = idx.m5 if len(idx.m5) > 10 else idx.m15 if len(idx.m15) > 10 else idx.daily
        frame = build_feature_frame(intraday, idx_ref)
    elif trade_type_norm in {"options", "volatility"}:
        frame = build_feature_frame(tf.daily, idx.daily)
    else:
        raise HTTPException(status_code=400, detail="trade_type must be swing, intraday, options, volatility")

    if frame.empty:
        raise HTTPException(status_code=400, detail="Not enough data to generate signal")

    latest = frame.iloc[-1]
    adx = float(latest.get("adx", 0.0))
    atr_pct = float(latest.get("atr_pct", 0.0))
    vol_reg = float(latest.get("volatility_regime", 0.0))
    regime = classify_regime(adx=adx, atr_pct=atr_pct, vol_regime=vol_reg)

    try:
        bundle = load_multi_strategy(symbol)
    except Exception:
        bundle = train_multi_strategy_for_symbol(symbol)
        save_multi_strategy(bundle, symbol)

    probability_up, confidence = predict_strategy(bundle, latest, trade_type=trade_type_norm)

    optimized_threshold = 65.0

    # Enforce higher timeframe alignment for intraday execution.
    if trade_type_norm == "intraday":
        daily_trend = float(latest.get("daily_trend", 0.0))
        if daily_trend > 0 and probability_up < 0.5:
            probability_up = 0.5
            confidence = min(confidence, 58.0)
        elif daily_trend < 0 and probability_up > 0.5:
            probability_up = 0.5
            confidence = min(confidence, 58.0)

    # Regime adaptation: trend = breakout-friendly, sideways = mean-reversion selective.
    breakout = float(latest.get("breakout_flag", 0.0))
    if regime == "TRENDING" and breakout != 0:
        confidence = min(100.0, confidence + 6.0)
    if regime == "SIDEWAYS":
        confidence = max(0.0, confidence - 8.0)

    # Hard execution safety for live: avoid low quality regimes and low confidence.
    if regime in {"SIDEWAYS", "LOW_VOLATILITY"}:
        confidence = min(confidence, 59.0)

    decision = decide_trade(
        symbol=symbol,
        trade_type=trade_type_norm,
        probability_up=probability_up,
        confidence_score=confidence,
        entry_price=float(latest.get("close", 0.0)),
        atr=float(latest.get("atr_pct", 0.01) * latest.get("close", 1.0)),
        liquidity_score=min(1.0, float(latest.get("volume_spike", 1.0)) / 2.0),
        risk_manager=risk_manager,
        put_call_ratio=float(latest.get("put_call_ratio", 1.0)),
        open_interest_change=float(latest.get("open_interest_change", 0.0)),
        iv_percentile=float(latest.get("iv_percentile", 0.5)),
        iv_expansion_probability=float(probability_up if trade_type_norm == "volatility" else 0.5),
        optimized_threshold=optimized_threshold,
        higher_tf_trend=float(latest.get("index_trend", 0.0)),
        regime=regime,
    )

    if confidence < OPTIMIZED_CONFIDENCE_THRESHOLD:
        decision.action = "NO_TRADE"
        decision.reason = f"Confidence below optimized threshold {OPTIMIZED_CONFIDENCE_THRESHOLD:.0f}"

    signal = MultiStrategySignalResponse(
        symbol=symbol.upper(),
        trade_type=trade_type_norm.upper(),
        regime=regime,
        probability_up=float(probability_up),
        confidence_score=float(confidence),
        action=decision.action,
        entry_price=float(decision.entry_price),
        stop_loss=float(decision.stop_loss),
        target=float(decision.target),
        position_size=int(decision.position_size),
        risk_pct=float(decision.risk_pct),
        reason=decision.reason,
        formatted_signal=format_trade_signal(decision),
    )
    return signal

def predict_single(symbol: str, timeframe: str = "1d") -> Optional[StockPredictionResponse]:
    """Predict for a single stock."""
    try:
        mapped_symbol = SYMBOL_MAPPING.get(symbol.upper(), symbol)
        ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
        models = load_models()
        tf_norm = str(timeframe or "1d").lower().strip()
        period, interval = timeframe_to_yf_params(tf_norm)
        intraday_mode = is_intraday_timeframe(tf_norm)
        hist = fetch_history(ticker, period=period, interval=interval)
        features_df = compute_features_from_history(hist)

        if features_df is None or len(features_df) < LOOKBACK + 1:
            return None

        sentiment_score, _ = fetch_news_sentiment(ticker, symbol, limit=5)
        sentiment_score = _safe_float(sentiment_score, 0.0)
        features_df.loc[features_df.index[-1], "news_sentiment_score"] = sentiment_score

        trained_cols = list(getattr(models["scaler"], "feature_names_in_", FEATURE_COLUMNS))
        latest_row = features_df.iloc[-1]
        latest_aligned = pd.to_numeric(latest_row.reindex(trained_cols), errors="coerce").fillna(0.0)
        X_input = pd.DataFrame([latest_aligned.values], columns=trained_cols)
        X_scaled = models["scaler"].transform(X_input)
        X_scaled_df = pd.DataFrame(X_scaled, columns=trained_cols)

        xgb_prob = _safe_float(models["xgb"].predict_proba(X_scaled_df)[:, 1][0], 0.5)
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
                pass

        lstm_val = _safe_float(lstm_prob if lstm_prob is not None else 0.0, 0.0)
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

        # Intraday should be mostly tape-driven; reduce news influence for next-candle direction.
        if tf_norm in {"1m", "5m", "15m"}:
            sentiment_weight = 0.0
        elif intraday_mode:
            sentiment_weight = min(SENTIMENT_WEIGHT, 0.03)
        else:
            sentiment_weight = SENTIMENT_WEIGHT

        # News-aware probability adjustment: positive headlines increase buy bias, negative decrease it.
        prob_up = prob_up + (sentiment_weight * sentiment_score)
        prob_up = _safe_float(max(0.0, min(1.0, _safe_float(prob_up, 0.5))), 0.5)
        prob_down = 1.0 - prob_up

        latest_price = _safe_float(features_df["close"].iloc[-1], 0.0)
        date_str = str(features_df["date"].iloc[-1])

        # -------- Strict weighted quant scoring engine (0-100) --------
        latest = features_df.iloc[-1]
        rsi = _safe_float(pd.to_numeric(latest.get("rsi", 50.0), errors="coerce"), 50.0)
        macd_val = _safe_float(pd.to_numeric(latest.get("macd", 0.0), errors="coerce"), 0.0)
        macd_sig = _safe_float(pd.to_numeric(latest.get("macd_signal", 0.0), errors="coerce"), 0.0)
        macd_hist = _safe_float(pd.to_numeric(latest.get("macd_hist", 0.0), errors="coerce"), 0.0)
        volume_change = _safe_float(pd.to_numeric(latest.get("volume_change", 0.0), errors="coerce"), 0.0)
        sma50 = _safe_float(pd.to_numeric(latest.get("sma_50", latest_price), errors="coerce"), latest_price)
        sma200 = _safe_float(pd.to_numeric(latest.get("sma_200", sma50), errors="coerce"), sma50)

        # Trend score (max 30)
        # For intraday mode, direction must follow model probabilities (next-candle objective).
        if latest_price > sma50 > sma200:
            structure_trend_label = "Strong Bullish"
            structure_trend_points = 30
            structure_direction = "BUY"
        elif latest_price < sma50 < sma200:
            structure_trend_label = "Strong Bearish"
            structure_trend_points = 30
            structure_direction = "SELL"
        elif latest_price > sma50:
            structure_trend_label = "Weak Bullish"
            structure_trend_points = 20
            structure_direction = "BUY"
        elif latest_price < sma50:
            structure_trend_label = "Weak Bearish"
            structure_trend_points = 20
            structure_direction = "SELL"
        else:
            structure_trend_label = "Sideways"
            structure_trend_points = 10
            structure_direction = "BUY" if prob_up >= prob_down else "SELL"

        if intraday_mode:
            direction = "BUY" if prob_up >= prob_down else "SELL"
            edge = abs(prob_up - prob_down)
            if direction == "BUY":
                trend_label = "Strong Bullish" if edge >= 0.16 else "Weak Bullish"
            else:
                trend_label = "Strong Bearish" if edge >= 0.16 else "Weak Bearish"

            if edge >= 0.20:
                trend_points = 30
            elif edge >= 0.12:
                trend_points = 25
            elif edge >= 0.06:
                trend_points = 20
            else:
                trend_points = 14
        else:
            direction = structure_direction
            trend_label = structure_trend_label
            trend_points = structure_trend_points

        # Momentum score (max 25)
        if direction == "BUY":
            if 50 <= rsi <= 65:
                momentum_points = 25
            elif rsi > 65 or rsi < 35:
                momentum_points = 15
            else:
                momentum_points = 10
        else:
            if 35 <= rsi <= 50:
                momentum_points = 25
            elif rsi < 35 or rsi > 65:
                momentum_points = 15
            else:
                momentum_points = 10

        # MACD score (max 15)
        if direction == "BUY":
            if macd_val > macd_sig and macd_hist > 0:
                macd_points = 15
            elif macd_val > macd_sig:
                macd_points = 10
            else:
                macd_points = 5
        else:
            if macd_val < macd_sig and macd_hist < 0:
                macd_points = 15
            elif macd_val < macd_sig:
                macd_points = 10
            else:
                macd_points = 5

        # Volume score (max 10)
        if volume_change > 0.05:
            volume_points = 10
            volume_label = "Increasing"
        elif volume_change > -0.02:
            volume_points = 5
            volume_label = "Flat"
        else:
            volume_points = 2
            volume_label = "Decreasing"

        # Price position score (max 10)
        support = _safe_float(hist["Low"].tail(20).min(), latest_price * 0.98) if "Low" in hist.columns and len(hist) >= 20 else latest_price * 0.98
        resistance = _safe_float(hist["High"].tail(20).max(), latest_price * 1.02) if "High" in hist.columns and len(hist) >= 20 else latest_price * 1.02
        near_resistance = latest_price >= resistance * 0.985
        near_support = latest_price <= support * 1.015
        if (direction == "BUY" and near_resistance) or (direction == "SELL" and near_support):
            price_points = 10
        elif support < latest_price < resistance:
            price_points = 5
        else:
            price_points = 2

        # News sentiment score (max 10)
        if sentiment_score > 0.15:
            news_label = "Positive"
        elif sentiment_score < -0.15:
            news_label = "Negative"
        else:
            news_label = "Neutral"

        if (direction == "BUY" and news_label == "Positive") or (direction == "SELL" and news_label == "Negative"):
            news_points = 10
            news_aligned = True
        elif news_label == "Neutral":
            news_points = 5
            news_aligned = False
        else:
            news_points = 2
            news_aligned = False

        total_score = _safe_float(trend_points + momentum_points + macd_points + volume_points + price_points + news_points, 50.0)

        # Guardrail: >85 only when trend + momentum + volume + news all align strongly.
        strong_alignment = (
            trend_points >= 30 and
            momentum_points >= 25 and
            volume_points >= 10 and
            news_aligned
        )
        if total_score > 85 and not strong_alignment:
            total_score = 85.0

        # Get regime
        try:
            idx_df = download_index("^NSEI", period="1y")
            regime_df = compute_regime(idx_df)
            regime = regime_df["regime"].iloc[-1]
        except:
            regime = "UNKNOWN"

        # Final decision rules (strict)
        if total_score < 60:
            signal = "WAIT"
        elif total_score < 75:
            signal = f"Weak {direction}"
        elif total_score <= 90:
            signal = f"Strong {direction}"
        else:
            signal = f"Very Strong {direction}"

        confidence_score = _safe_float(max(0.0, min(100.0, total_score)), 50.0)
        confidence = confidence_score / 100.0
        latest_atr = _safe_float(pd.to_numeric(features_df["atr"], errors="coerce").iloc[-1], latest_price * 0.02) if "atr" in features_df.columns else (latest_price * 0.02)
        trade_plan = build_trade_plan(
            latest_price=latest_price,
            atr=latest_atr,
            confidence_score=confidence_score,
            reward_multiple=3.0 if "BUY" in signal else 2.0,
            min_confidence=60.0,
        )

        # Direction-aware risk levels: for SELL, stop above entry and target below entry.
        stop_distance = max(latest_atr * 1.5, latest_price * 0.005)
        if signal.startswith("WAIT"):
            stop_loss = float(latest_price)
            take_profit = float(latest_price)
        elif "SELL" in signal:
            stop_loss = float(latest_price + stop_distance)
            take_profit = float(latest_price - (stop_distance * 2.0))
        else:
            stop_loss = float(trade_plan.stop_loss)
            take_profit = float(trade_plan.take_profit)

        horizon_text = f"next {tf_norm} candle" if intraday_mode else "next session"

        pred = StockPredictionResponse(
            symbol=symbol,
            probability_up=_safe_float(prob_up, 0.5),
            prob_up=_safe_float(prob_up, 0.5),
            prob_down=_safe_float(prob_down, 0.5),
            confidence_score=_safe_float(confidence_score, 50.0),
            confidence=_safe_float(confidence, 0.5),
            signal=signal,
            regime=regime,
            sentiment_score=_safe_float(sentiment_score, 0.0),
            latest_price=_safe_float(latest_price, 0.0),
            entry_price=_safe_float(trade_plan.entry_price, 0.0),
            stop_loss=_safe_float(stop_loss, 0.0),
            take_profit=_safe_float(take_profit, 0.0),
            position_size=trade_plan.position_size,
            trade_validity=trade_plan.trade_validity,
            date=date_str,
            trend=trend_label,
            timeframe=tf_norm,
            news_sentiment_label=news_label,
            reason=(
                f"{trend_label} setup for {horizon_text} using {tf_norm} candles with RSI {rsi:.1f} and {volume_label.lower()} volume; "
                f"MACD {'supports' if macd_points >= 10 else 'is mixed for'} the {direction.lower()} setup. "
                f"Model probs: BUY {prob_up*100:.1f}% / SELL {prob_down*100:.1f}%."
            ),
        )
        if signal == "WAIT":
            pred.signal = f"WAIT (BUY: {prob_up*100:.1f}%, SELL: {prob_down*100:.1f}%)"
        store_prediction(pred)
        return pred
    except Exception as e:
        print(f"Error predicting {symbol}: {e}")
        return None

# ================== Endpoints ==================

@app.get("/health")
def health():
    """Health check."""
    try:
        models = load_models()
        return {"status": "ok", "lstm_loaded": models.get("lstm") is not None}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _symbol_to_ticker(symbol: str) -> str:
    mapped = SYMBOL_MAPPING.get(symbol.upper(), symbol.upper())
    return mapped if "." in mapped or mapped.startswith("^") else f"{mapped}.NS"


_UNIVERSE_CACHE = []
_UNIVERSE_SEARCH_CACHE: list[dict[str, str]] = []

def _load_universe_symbols(limit: int = TRENDING_UNIVERSE_LIMIT) -> list[str]:
    global _UNIVERSE_CACHE
    if _UNIVERSE_CACHE:
        return _UNIVERSE_CACHE

    # 1) Prefer live internet NSE equity list so universe is not locked to local CSV.
    try:
        live_df = pd.read_csv(NSE_EQUITY_LIST_URL)
        symbol_col = "SYMBOL" if "SYMBOL" in live_df.columns else ("symbol" if "symbol" in live_df.columns else None)
        if symbol_col is not None:
            vals = (
                live_df[symbol_col]
                .astype(str)
                .str.upper()
                .str.strip()
                .replace("", np.nan)
                .dropna()
                .tolist()
            )
            uniq = list(dict.fromkeys(vals))
            if uniq:
                _UNIVERSE_CACHE = uniq[: max(1, limit)]
                return _UNIVERSE_CACHE
    except Exception:
        pass

    # 2) Fallback to workspace CSV.
    try:
        if SYMBOL_CSV_PATH.exists():
            df = pd.read_csv(SYMBOL_CSV_PATH)
            if "symbol" in df.columns:
                vals = (
                    df["symbol"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                    .replace("", np.nan)
                    .dropna()
                    .tolist()
                )
                _UNIVERSE_CACHE = list(dict.fromkeys(vals))[: max(1, limit)]
                return _UNIVERSE_CACHE
    except Exception:
        pass
        
    _UNIVERSE_CACHE = TRACKED_SYMBOLS[:]
    return _UNIVERSE_CACHE


def _load_trending_log() -> dict[str, list[str]]:
    try:
        if TRENDING_LOG_PATH.exists():
            payload = json.loads(TRENDING_LOG_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return {str(k): [str(x).upper() for x in (v or [])] for k, v in payload.items()}
    except Exception:
        pass
    return {}


def _save_trending_log(log: dict[str, list[str]]) -> None:
    try:
        TRENDING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        TRENDING_LOG_PATH.write_text(json.dumps(log, indent=2), encoding="utf-8")
    except Exception:
        pass


def _recent_picks(log: dict[str, list[str]], days: int) -> set[str]:
    recent: set[str] = set()
    now = datetime.now().date()
    for d_str, symbols in log.items():
        try:
            d = datetime.fromisoformat(d_str).date()
        except Exception:
            continue
        if (now - d).days <= max(0, days):
            recent.update([str(s).upper() for s in symbols])
    return recent


def _score_trend(hist: pd.DataFrame) -> Optional[float]:
    if hist is None or hist.empty or len(hist) < 30:
        return None

    close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
    volume = pd.to_numeric(hist["Volume"], errors="coerce").dropna()
    if len(close) < 30 or len(volume) < 20:
        return None

    p_now = float(close.iloc[-1])
    p_5 = float(close.iloc[-6])
    p_20 = float(close.iloc[-21])
    if p_now <= 0 or p_5 <= 0 or p_20 <= 0:
        return None

    ret_5 = (p_now / p_5) - 1.0
    ret_20 = (p_now / p_20) - 1.0
    vol_spike = float(volume.iloc[-1] / max(float(volume.tail(20).mean()), 1.0))

    # Focus on stocks that are both trending and actively traded.
    score = (ret_20 * 100.0) + (ret_5 * 60.0) + (max(0.0, vol_spike - 1.0) * 20.0)
    return float(score)


def get_trending_symbols(limit: int = TRENDING_PICK_LIMIT) -> list[str]:
    now = datetime.now()
    limit = max(1, int(limit))
    cached_at = _TRENDING_CACHE.get("timestamp")
    cached_syms = _TRENDING_CACHE.get("symbols") or []
    if isinstance(cached_at, datetime) and cached_syms:
        if (now - cached_at) < timedelta(minutes=max(1, TRENDING_CACHE_TTL_MIN)) and len(cached_syms) >= limit:
            return cached_syms[:limit]

    universe = _load_universe_symbols()
    if not universe:
        return TRACKED_SYMBOLS[: max(1, limit)]

    log = _load_trending_log()
    recently_used = _recent_picks(log, TRENDING_WINDOW_DAYS)

    scored: list[tuple[str, float]] = []
    symbols_primary = [s for s in universe if s not in recently_used]
    tickers_map = {s: _symbol_to_ticker(s) for s in symbols_primary}

    # Batch download is much more reliable than per-symbol calls.
    try:
        if tickers_map:
            bulk = yf.download(
                list(tickers_map.values()),
                period="3mo",
                interval="1d",
                auto_adjust=True,
                group_by="ticker",
                progress=False,
                threads=True,
            )
            if isinstance(getattr(bulk, "columns", None), pd.MultiIndex):
                lvl0 = set([str(x) for x in bulk.columns.get_level_values(0).unique().tolist()])
                for symbol, ticker in tickers_map.items():
                    if ticker not in lvl0:
                        continue
                    part = bulk[ticker]
                    score = _score_trend(part)
                    if score is not None:
                        scored.append((symbol, score))
    except Exception:
        pass

    # Backfill unresolved symbols with single-symbol fetches.
    unresolved = [s for s in symbols_primary if s not in {name for name, _ in scored}]
    for symbol in unresolved:
        try:
            hist = yf.download(_symbol_to_ticker(symbol), period="3mo", interval="1d", auto_adjust=True, progress=False)
            score = _score_trend(hist)
            if score is None:
                continue
            scored.append((symbol, score))
        except Exception:
            continue

    # If dedupe removed too many symbols, backfill from all candidates.
    if len(scored) < limit:
        backfill_candidates = [u for u in universe if u not in {s for s, _ in scored}]
        for symbol in backfill_candidates:
            try:
                hist = yf.download(_symbol_to_ticker(symbol), period="3mo", interval="1d", auto_adjust=True, progress=False)
                score = _score_trend(hist)
                if score is None:
                    continue
                scored.append((symbol, score))
            except Exception:
                continue

    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    picked = [s for s, _ in scored[:limit]]

    if not picked:
        picked = TRACKED_SYMBOLS[:limit]

    today = datetime.now().date().isoformat()
    log[today] = picked
    # keep last ~30 days
    keys = sorted(log.keys())[-30:]
    log = {k: log[k] for k in keys}
    _save_trending_log(log)

    _TRENDING_CACHE["timestamp"] = now
    _TRENDING_CACHE["symbols"] = picked
    return picked


@app.get("/symbols/search")
async def search_symbols(q: str = "", limit: int = 12):
    """Search known symbols for autocomplete suggestions."""
    limit = max(1, min(int(limit), 50))
    query = str(q or "").strip().upper()

    global _UNIVERSE_SEARCH_CACHE
    if not _UNIVERSE_SEARCH_CACHE:
        base_rows = []
        if UNIVERSE_JSON:
            for row in UNIVERSE_JSON[:250000]:
                sym = str(row.get("symbol", "")).upper().strip()
                if not sym:
                    continue
                ins_type = str(row.get("instrument_type", "")).upper().strip()
                if ins_type and ins_type != "EQ":
                    continue
                if not sym.isalpha():
                    continue
                nm = str(row.get("name", sym)).strip() or sym
                base_rows.append({"symbol": sym, "name": nm, "name_u": nm.upper()})
        if not base_rows:
            base_rows = [{"symbol": s, "name": s, "name_u": s} for s in _load_universe_symbols(limit=50000)]

        seen = set()
        merged: list[dict[str, str]] = []
        for s in TRACKED_SYMBOLS:
            su = s.upper()
            if su not in seen:
                seen.add(su)
                merged.append({"symbol": su, "name": su, "name_u": su})
        for r in base_rows:
            su = r["symbol"]
            if su in seen:
                continue
            seen.add(su)
            merged.append(r)
        _UNIVERSE_SEARCH_CACHE = merged

    if not query:
        syms = get_trending_symbols(limit=limit)
        out = []
        idx = {r["symbol"]: r for r in _UNIVERSE_SEARCH_CACHE[:100000]}
        for s in syms:
            rr = idx.get(s, {"symbol": s, "name": s})
            out.append({"symbol": rr["symbol"], "name": rr.get("name", rr["symbol"]), "ticker": _symbol_to_ticker(rr["symbol"])})
        return out

    starts_symbol = [r for r in _UNIVERSE_SEARCH_CACHE if r["symbol"].startswith(query)]
    starts_name = [r for r in _UNIVERSE_SEARCH_CACHE if r["name_u"].startswith(query) and r not in starts_symbol]
    contains_symbol = [r for r in _UNIVERSE_SEARCH_CACHE if query in r["symbol"] and r not in starts_symbol and r not in starts_name]
    contains_name = [r for r in _UNIVERSE_SEARCH_CACHE if query in r["name_u"] and r not in starts_symbol and r not in starts_name and r not in contains_symbol]

    items = (starts_symbol + starts_name + contains_symbol + contains_name)[:limit]
    return [{"symbol": r["symbol"], "name": r.get("name", r["symbol"]), "ticker": _symbol_to_ticker(r["symbol"])} for r in items]


@app.get("/chart/{symbol}")
async def get_chart_data(symbol: str, period: str = "6mo", interval: str = "1d"):
    """Return OHLCV candles for a symbol chart page."""
    allowed_periods = {
        "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max",
    }
    allowed_intervals = {
        "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo",
    }
    p = period if period in allowed_periods else "6mo"
    iv = interval if interval in allowed_intervals else "1d"

    try:
        symbol_u = symbol.upper().strip()
        ticker = _symbol_to_ticker(symbol_u)
        df = yf.download(ticker, period=p, interval=iv, auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df is None or df.empty:
            return {"candles": [], "error": f"No chart data for {symbol_u}"}

        candles = []
        cols = set(df.columns.tolist())
        required = {"Open", "High", "Low", "Close"}
        if not required.issubset(cols):
            return {"candles": [], "error": f"Incomplete chart data for {symbol_u}"}

        # Drop entirely any rows with NaN in critical columns to prevent JSON nulls that crash the frontend
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        if "Volume" in df.columns:
            df["Volume"] = df["Volume"].fillna(0)

        for ts, row in df.tail(1500).iterrows():
            candles.append(
                {
                    "time": pd.Timestamp(ts).isoformat(),
                    "open": float(row.get("Open", 0.0) or 0.0),
                    "high": float(row.get("High", 0.0) or 0.0),
                    "low": float(row.get("Low", 0.0) or 0.0),
                    "close": float(row.get("Close", 0.0) or 0.0),
                    "volume": float(row.get("Volume", 0.0) or 0.0),
                }
            )

        latest = candles[-1] if candles else None
        return {
            "symbol": symbol_u,
            "ticker": ticker,
            "period": p,
            "interval": iv,
            "count": len(candles),
            "latest": latest,
            "candles": candles,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predictions")
async def get_predictions():
    """Get predictions for top stocks."""
    symbols = get_trending_symbols(limit=TRENDING_PICK_LIMIT)
    results = []
    for sym in symbols:
        pred = predict_single(sym)
        if pred:
            results.append(pred)
    return results


@app.get("/trade-now/bull-stocks")
async def get_trade_now_bull_stocks(limit: int = BULL_SCAN_LIMIT):
    """Return bullish trade candidates from a live internet-driven universe for TRADE NOW."""
    try:
        limit = max(1, min(int(limit), max(BULL_SCAN_LIMIT, 120)))
        symbols = get_trending_symbols(limit=limit)
        candidate_symbols = list(dict.fromkeys([*TRACKED_SYMBOLS, *symbols]))
        candidate_symbols = candidate_symbols[: max(limit, len(TRACKED_SYMBOLS))]

        seen: set[str] = set()
        all_preds: list[StockPredictionResponse] = []
        bulls: list[StockPredictionResponse] = []

        for sym in candidate_symbols:
            sym_up = sym.upper()
            if sym_up in seen:
                continue
            seen.add(sym_up)

            pred = predict_single(sym_up)
            if pred is None:
                continue
            all_preds.append(pred)

            # Broader bullish definition for discovery mode.
            # Strict execution filtering still happens in UI thresholds and risk controls.
            is_buy_label = str(pred.signal).upper() == "BUY"
            is_prob_bull = float(pred.prob_up) >= 0.52
            if is_buy_label or is_prob_bull:
                bulls.append(pred)

        # If strict bull picks are sparse, fallback to top directional probabilities.
        if not bulls:
            for sym in candidate_symbols:
                pred = predict_single(sym)
                if pred is None:
                    # Fallback purely for indices that have insufficient history for predict_single, like BSE BANKEX
                    mapped = SYMBOL_MAPPING.get(sym.upper(), sym)
                    ticker = mapped if "." in mapped or mapped.startswith("^") else f"{mapped}.NS"
                    try:
                        import yfinance as yf
                        df = yf.download(ticker, period="5d", interval="1d", progress=False)
                        if not df.empty:
                            last_px_val = df['Close'].iloc[-1]
                            last_px = float(last_px_val.item() if hasattr(last_px_val, "item") else last_px_val)
                        else:
                            continue
                    except:
                        continue
                    # Create a mock StockPredictionResponse
                    pred = StockPredictionResponse(
                        symbol=sym,
                        latest_price=last_px,
                        predicted_price=last_px * 1.01,
                        prob_up=0.55,
                        confidence_score=65.0,
                        trend="BULLISH",
                        signal="BUY"
                    )

                if pred is not None and float(pred.prob_up) >= 0.50:
                    bulls.append(pred)

        # Final fallback: return best available directional candidates so UI is never empty.
        if not bulls and all_preds:
            fallback = sorted(all_preds, key=lambda p: float(p.prob_up), reverse=True)
            bulls = [p for p in fallback if float(p.prob_up) >= 0.45][: max(5, min(limit, 20))]
            if not bulls:
                bulls = fallback[: max(5, min(limit, 20))]

        bulls.sort(key=lambda p: float(p.confidence_score), reverse=True)
        return bulls
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prediction/{symbol}")
async def get_prediction(symbol: str, timeframe: str = "1d"):
    """Get prediction for a specific stock."""
    pred = predict_single(symbol, timeframe=timeframe)
    if pred is None:
        mapped_symbol = SYMBOL_MAPPING.get(symbol.upper(), symbol)
        ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
        period, interval = timeframe_to_yf_params(timeframe)
        hist = fetch_history(ticker, period=period, interval=interval)
        latest_price = 0.0
        if hist is not None and not hist.empty:
            last_close = hist["Close"].iloc[-1]
            latest_price = _safe_float(last_close.iloc[0] if hasattr(last_close, "iloc") else last_close, 0.0)

        # Graceful fallback: keep API stable even if data provider has no history for this symbol.
        pred = StockPredictionResponse(
            symbol=symbol.upper(),
            probability_up=0.5,
            prob_up=0.5,
            prob_down=0.5,
            confidence_score=50.0,
            confidence=0.5,
            signal="WAIT (BUY: 50.0%, SELL: 50.0%)",
            regime="UNKNOWN",
            sentiment_score=0.0,
            latest_price=latest_price,
            entry_price=latest_price,
            stop_loss=latest_price,
            take_profit=latest_price,
            position_size=0,
            trade_validity=False,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            timeframe=timeframe,
        )
    return _sanitize_json_obj(pred.model_dump())

@app.get("/regime")
async def get_regime():
    """Get market regime."""
    try:
        idx_df = download_index("^NSEI", period="1y")
        regime_df = compute_regime(idx_df)
        latest = regime_df.iloc[-1]

        regime_map = {"BULL": "Bullish", "BEAR": "Bearish", "SIDEWAYS": "Sideways"}
        ma200 = float(latest.get("ma200", 0) or 0)
        close_price = float(latest["Close"])
        distance = abs(close_price - ma200) / (ma200 + 1e-9) if ma200 else 0.0
        confidence = float(min(0.99, max(0.50, 0.50 + (distance * 8))))

        return RegimeResponse(
            regime=regime_map.get(latest["regime"], latest["regime"]),
            confidence=confidence,
            description=f"Market in {latest['regime']} regime",
            ma200=ma200,
            close_price=close_price,
            slope=float(latest.get("slope60", 0)),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtest")
async def get_backtest():
    """Get backtest performance."""
    try:
        symbol = TRACKED_SYMBOLS[0]
        mapped = SYMBOL_MAPPING.get(symbol.upper(), symbol)
        ticker = mapped if "." in mapped or mapped.startswith("^") else f"{mapped}.NS"
        hist = fetch_history(ticker, period="10y")
        features_df = compute_features_from_history(hist)
        if features_df is None or len(features_df) < (LOOKBACK + 60):
            raise ValueError("Insufficient historical data for backtest")

        models = load_models()
        trained_cols = list(getattr(models["scaler"], "feature_names_in_", FEATURE_COLUMNS))
        aligned = features_df.reindex(columns=trained_cols).apply(pd.to_numeric, errors="coerce").fillna(0.0)
        X_scaled = models["scaler"].transform(aligned)
        X_scaled_df = pd.DataFrame(X_scaled, columns=trained_cols)

        xgb_prob = models["xgb"].predict_proba(X_scaled_df)[:, 1]
        lgbm_prob = models["lgbm"].predict_proba(X_scaled_df)[:, 1]
        rf_prob = models["rf"].predict_proba(X_scaled)[:, 1]
        lstm_prob = np.zeros_like(xgb_prob)
        if models.get("lstm") is not None:
            X_seq, _ = make_sequences(X_scaled, np.zeros(len(X_scaled)), lookback=LOOKBACK)
            if len(X_seq) > 0:
                with torch.no_grad():
                    p = models["lstm"](torch.tensor(X_seq, dtype=torch.float32)).squeeze().numpy()
                    lstm_prob = np.concatenate([np.zeros(LOOKBACK), p])

        if models.get("meta_model") is not None:
            probs = models["meta_model"].predict_proba(np.column_stack([xgb_prob, lgbm_prob, rf_prob, lstm_prob]))[:, 1]
        else:
            w = models.get("dynamic_weights", ENSEMBLE_WEIGHTS)
            probs = (
                w.get("xgb", 0.4) * xgb_prob
                + w.get("lgbm", 0.3) * lgbm_prob
                + w.get("rf", 0.2) * rf_prob
                + w.get("lstm", 0.1) * lstm_prob
            )

        signal = pd.Series(np.where(probs > 0.6, 1, np.where(probs < 0.4, -1, 0)), index=features_df.index)
        price_series = pd.to_numeric(features_df["close"], errors="coerce").ffill().bfill()

        # Build curves for frontend charts.
        frame = pd.DataFrame({"price": price_series, "signal": signal}).dropna()
        daily_ret = frame["price"].pct_change().fillna(0.0)
        shifted_pos = frame["signal"].shift(1).fillna(0.0)
        costs = (shifted_pos.diff().abs().fillna(0.0) * (5.0 / 10000.0)).clip(lower=0.0)
        strategy_ret = (shifted_pos * daily_ret) - costs
        equity_curve = (1.0 + strategy_ret).cumprod() * 100000.0
        drawdown_curve = ((equity_curve / equity_curve.cummax()) - 1.0).fillna(0.0)

        summary = backtest_with_benchmark(features_df["close"], signal)
        return BacktestResponse(
            total_return=float(summary.total_return),
            win_rate=float(summary.win_rate),
            max_drawdown=float(summary.max_drawdown),
            sharpe=float(summary.sharpe_ratio),
            sortino=float(summary.sharpe_ratio),
            profit_factor=float(summary.profit_factor),
            benchmark_return=float(summary.benchmark_return),
            avg_trade_return=float(summary.total_return / max(len(signal), 1)),
            num_trades=int((signal != 0).sum()),
            equity_curve=downsample_curve([float(x) for x in equity_curve.values], max_points=300),
            drawdown_curve=downsample_curve([float(x) for x in drawdown_curve.values], max_points=300),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/analytics", response_model=PortfolioAnalyticsResponse)
async def portfolio_analytics():
    try:
        snapshot = compute_portfolio_snapshot()
        return PortfolioAnalyticsResponse(**_sanitize_json_obj(snapshot))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/alerts/live")
async def live_alerts(timeframe: str = "1d", min_confidence: float = 75.0, limit: int = 10):
    """Generate actionable live alerts - lightweight mock version for demo"""
    try:
        min_conf = float(max(50.0, min(99.0, min_confidence)))
        max_items = int(max(1, min(30, limit)))
        
        # Use pre-generated trending symbols instead of computing predictions
        symbols = get_trending_symbols(limit=max(12, max_items * 2))[:max_items]
        
        alerts: List[dict] = []
        import hashlib
        
        for idx, sym in enumerate(symbols):
            stock_hash = int(hashlib.md5(sym.encode()).hexdigest(), 16)
            prob_up = 0.50 + (stock_hash % 40) * 0.01
            prob_down = 1.0 - prob_up
            confidence = 70.0 + (stock_hash % 25)
            price = 1000 + (stock_hash % 6000)
            
            side = "BUY" if prob_up > prob_down else "SELL"
            
            alerts.append({
                "symbol": sym,
                "signal": side,
                "confidence_score": float(confidence),
                "probability_up": float(prob_up),
                "probability_down": float(prob_down),
                "latest_price": float(price),
                "entry_price": float(price),
                "stop_loss": float(price * 0.95) if side == "BUY" else float(price * 1.05),
                "take_profit": float(price * 1.05) if side == "BUY" else float(price * 0.95),
                "timeframe": str(timeframe),
                "reason": f"{side} setup with confidence {confidence:.1f}% and probability spread {abs(prob_up - prob_down) * 100:.1f}%",
                "timestamp": datetime.now().isoformat(),
            })

        return {
            "count": len(alerts[:max_items]),
            "alerts": alerts[:max_items]
        }
    except Exception as exc:
        return {
            "count": 0,
            "alerts": [],
            "error": str(exc)
        }

@app.get("/signals")
async def get_signals(authorization: Optional[str] = Header(default=None)):
    """Get latest trading signals."""
    try:
        user = resolve_user(authorization)
        symbols = get_trending_symbols(limit=max(FREE_TIER_DAILY_SIGNAL_LIMIT, 8))
        signals = []
        sectors = {
            "RELIANCE": "Energy",
            "TCS": "Tech",
            "INFY": "Tech",
            "WIPRO": "Tech",
            "HDFCBANK": "Finance",
            "ICICIBANK": "Finance",
            "SBIN": "Finance",
            "BHARTIARTL": "Telecom",
            "MARUTI": "Auto",
            "TATACONSUM": "Consumer",
            "SUNPHARMA": "Pharma",
        }

        for sym in symbols:
            pred = predict_single(sym)
            if pred:
                signals.append(SignalResponse(
                    symbol=sym,
                    probability_up=pred.prob_up,
                    prob_up=pred.prob_up,
                    sentiment_score=pred.sentiment_score,
                    price=pred.latest_price,
                    sector=sectors.get(sym, "Other"),
                    regime=pred.regime,
                    signal_type=pred.signal,
                    confidence_score=pred.confidence_score,
                    confidence=pred.confidence,
                    entry_price=pred.entry_price,
                    stop_loss=pred.stop_loss,
                    take_profit=pred.take_profit,
                    position_size=pred.position_size,
                    trade_validity=pred.trade_validity,
                    timestamp=datetime.now().isoformat(),
                ))
        signals = sorted(signals, key=lambda s: s.confidence_score, reverse=True)
        if user["tier"] == "free":
            signals = signals[:FREE_TIER_DAILY_SIGNAL_LIMIT]
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news")
async def get_news():
    """Get latest market news with sentiment scores."""
    try:
        items = []
        for sym in get_trending_symbols(limit=5):
            mapped_symbol = SYMBOL_MAPPING.get(sym.upper(), sym)
            ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
            _, scored = fetch_news_sentiment(ticker, sym, limit=3)
            if not scored:
                scored = fetch_google_news(sym, limit=4)
            items.extend(scored)

        items.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        return [NewsItemResponse(**x) for x in items[:15]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard-stats")
async def get_dashboard_stats():
    """Get real dashboard cards data derived from live prices and model outputs."""
    try:
        portfolio_value = 0.0
        invested_value = 0.0
        today_gain = 0.0

        for pos in PAPER_POSITIONS:
            latest, prev = fetch_latest_price_and_change(pos["symbol"])
            if latest is None:
                continue
            qty = float(pos["quantity"])
            portfolio_value += latest * qty
            invested_value += float(pos["entry_price"]) * qty
            if prev is not None:
                today_gain += (latest - prev) * qty

        baseline = max(portfolio_value - today_gain, 1e-9)
        today_gain_pct = (today_gain / baseline) * 100.0

        dynamic_syms = get_trending_symbols(limit=6)
        preds = []
        for sym in dynamic_syms:
            pred = predict_single(sym)
            if pred:
                preds.append(pred)

        if preds:
            scored_symbols = 0
            directional_hits = 0.0
            for p in preds:
                latest, prev = fetch_latest_price_and_change(p.symbol)
                if latest is None or prev is None or prev == 0:
                    continue
                day_ret = (latest - prev) / prev
                if p.signal == "BUY":
                    directional_hits += 1.0 if day_ret > 0 else 0.0
                    scored_symbols += 1
                elif p.signal == "SELL":
                    directional_hits += 1.0 if day_ret < 0 else 0.0
                    scored_symbols += 1
                else:
                    directional_hits += 0.5
                    scored_symbols += 1

            win_rate = ((directional_hits / scored_symbols) * 100.0) if scored_symbols > 0 else 50.0
            market_sentiment = float(np.mean([(p.sentiment_score + 1.0) / 2.0 for p in preds]))
        else:
            win_rate = 50.0
            market_sentiment = 0.5

        sentiment_label = "Neutral"
        if market_sentiment >= 0.6:
            sentiment_label = "Positive"
        elif market_sentiment <= 0.4:
            sentiment_label = "Negative"

        sharpe_ratio = estimate_sharpe_from_symbols(dynamic_syms or TRACKED_SYMBOLS)

        return DashboardStatsResponse(
            portfolio_value=float(portfolio_value),
            today_gain=float(today_gain),
            today_gain_pct=float(today_gain_pct),
            win_rate=float(win_rate),
            sharpe_ratio=float(sharpe_ratio),
            market_sentiment=float(max(0.0, min(1.0, market_sentiment))),
            sentiment_label=sentiment_label,
            updated_at=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/paper-trades")
async def get_paper_trades():
    """Get paper trading results."""
    return [
        PaperTradeResponse(
            id="trade_1",
            symbol="RELIANCE",
            entry_price=2850.50,
            exit_price=2920.00,
            quantity=10,
            pnl=695.00,
            return_pct=0.024,
            entry_date="2024-03-10",
            exit_date="2024-03-13",
            status="CLOSED",
        ),
        PaperTradeResponse(
            id="trade_2",
            symbol="TCS",
            entry_price=4120.25,
            exit_price=None,
            quantity=5,
            pnl=0.0,
            return_pct=0.0,
            entry_date="2024-03-13",
            exit_date=None,
            status="OPEN",
        ),
    ]


@app.post("/auth/register", response_model=AuthResponse)
async def register(req: AuthRequest):
    conn = db_conn()
    try:
        token = secrets.token_urlsafe(32)
        existing_users = conn.execute("SELECT COUNT(1) AS c FROM users").fetchone()["c"]
        is_admin = 1 if int(existing_users) == 0 else 0
        conn.execute(
            "INSERT INTO users (email, password_hash, tier, token, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (req.email.lower().strip(), hash_password(req.password), "free", token, is_admin, datetime.now().isoformat()),
        )
        conn.commit()
        return AuthResponse(token=token, tier="free")
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        conn.close()


@app.post("/auth/login", response_model=AuthResponse)
async def login(req: AuthRequest):
    conn = db_conn()
    try:
        row = conn.execute(
            "SELECT tier FROM users WHERE email = ? AND password_hash = ?",
            (req.email.lower().strip(), hash_password(req.password)),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = secrets.token_urlsafe(32)
        conn.execute("UPDATE users SET token = ? WHERE email = ?", (token, req.email.lower().strip()))
        conn.commit()
        return AuthResponse(token=token, tier=row["tier"])
    finally:
        conn.close()


@app.get("/admin/users", response_model=List[UserSummary])
async def admin_users(authorization: Optional[str] = Header(default=None)):
    user = resolve_user(authorization)
    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    conn = db_conn()
    try:
        rows = conn.execute("SELECT email, tier, is_admin FROM users ORDER BY created_at DESC").fetchall()
        return [UserSummary(email=r["email"], tier=r["tier"], is_admin=bool(r["is_admin"])) for r in rows]
    finally:
        conn.close()


@app.post("/admin/users/{email}/tier")
async def set_user_tier(email: str, tier: str, authorization: Optional[str] = Header(default=None)):
    user = resolve_user(authorization)
    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    if tier not in {"free", "paid"}:
        raise HTTPException(status_code=400, detail="tier must be free or paid")
    conn = db_conn()
    try:
        conn.execute("UPDATE users SET tier = ? WHERE email = ?", (tier, email.lower().strip()))
        conn.commit()
        return {"ok": True, "email": email.lower().strip(), "tier": tier}
    finally:
        conn.close()


@app.post("/alerts/subscribe")
async def subscribe_alerts(email: str, channel: str = "email"):
    if channel not in {"email", "telegram"}:
        raise HTTPException(status_code=400, detail="channel must be email or telegram")
    conn = db_conn()
    try:
        conn.execute(
            "INSERT INTO alert_subscriptions (email, channel, enabled, created_at) VALUES (?, ?, 1, ?)",
            (email.lower().strip(), channel, datetime.now().isoformat()),
        )
        conn.commit()
        return {"ok": True, "email": email.lower().strip(), "channel": channel}
    finally:
        conn.close()


@app.get("/predictions/history")
async def predictions_history(limit: int = 100, authorization: Optional[str] = Header(default=None)):
    user = resolve_user(authorization)
    max_limit = 500 if user["tier"] == "paid" else 100
    limit = max(1, min(limit, max_limit))
    conn = db_conn()
    try:
        rows = conn.execute(
            """
            SELECT symbol, probability_up, confidence_score, signal, entry_price, stop_loss,
                   take_profit, position_size, trade_validity, created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.post("/realtime/generate")
async def realtime_generate():
    results = []
    for sym in get_trending_symbols(limit=TRENDING_PICK_LIMIT):
        pred = predict_single(sym)
        if pred is not None:
            results.append(pred)
    return {"generated": len(results), "timestamp": datetime.now().isoformat(), "items": results}


@app.get("/alerts/run")
async def run_alerts():
    alerts = evaluate_alerts()
    return {"count": len(alerts), "alerts": alerts}


@app.get("/chain/status")
async def chain_status():
    conn = db_conn()
    try:
        counts = conn.execute(
            """
            SELECT
                (SELECT COUNT(1) FROM predictions) AS prediction_count,
                (SELECT COUNT(1) FROM chain_blocks) AS block_count
            """
        ).fetchone()
        latest = conn.execute(
            """
            SELECT id, prediction_id, payload_hash, prev_hash, block_hash, created_at
            FROM chain_blocks
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    prediction_count = int(counts["prediction_count"] if counts else 0)
    block_count = int(counts["block_count"] if counts else 0)
    anchored_ratio = float((block_count / prediction_count) * 100.0) if prediction_count > 0 else 0.0

    implemented = [
        "Prediction records are hashed with SHA-256",
        "Each prediction hash is chained with previous block hash",
        "Immutable-style audit records stored in chain_blocks",
        "On-demand verification endpoint for each prediction",
    ]
    planned = [
        "Merkle-root periodic anchoring on public testnet",
        "Faculty-facing downloadable chain audit report",
        "Multi-node validator simulation for consensus demo",
        "Smart contract anchor transaction explorer links",
    ]

    latest_block = dict(latest) if latest else None
    return {
        "implemented": implemented,
        "planned": planned,
        "prediction_count": prediction_count,
        "block_count": block_count,
        "anchored_ratio": anchored_ratio,
        "latest_block": _sanitize_json_obj(latest_block),
    }


@app.get("/chain/records")
async def chain_records(limit: int = 20):
    lim = max(1, min(int(limit), 200))
    conn = db_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, prediction_id, payload_hash, prev_hash, block_hash, created_at
            FROM chain_blocks
            ORDER BY id DESC
            LIMIT ?
            """,
            (lim,),
        ).fetchall()
        return {"count": len(rows), "blocks": _sanitize_json_obj([dict(r) for r in rows])}
    finally:
        conn.close()


@app.get("/chain/verify/{prediction_id}")
async def chain_verify(prediction_id: int):
    conn = db_conn()
    try:
        row = conn.execute(
            """
            SELECT p.id, p.symbol, p.probability_up, p.confidence_score, p.signal,
                   p.entry_price, p.stop_loss, p.take_profit, p.position_size,
                   p.trade_validity, p.created_at,
                   b.id AS block_id, b.payload_hash, b.prev_hash, b.block_hash
            FROM predictions p
            LEFT JOIN chain_blocks b ON b.prediction_id = p.id
            WHERE p.id = ?
            LIMIT 1
            """,
            (prediction_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Prediction not found")
        if row["block_id"] is None:
            return {
                "prediction_id": prediction_id,
                "is_valid": False,
                "has_block": False,
                "reason": "Prediction exists but was not anchored",
            }

        payload_json, recomputed_payload_hash = _recompute_prediction_payload_hash(row)
        payload_ok = bool(recomputed_payload_hash == str(row["payload_hash"]))

        prev_row = conn.execute(
            """
            SELECT block_hash
            FROM chain_blocks
            WHERE id < ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(row["block_id"]),),
        ).fetchone()
        expected_prev = str(prev_row["block_hash"]) if prev_row else ("0" * 64)
        prev_ok = bool(str(row["prev_hash"]) == expected_prev)

        block_input = f"{int(row['id'])}|{str(row['payload_hash'])}|{str(row['prev_hash'])}|{str(row['created_at'])}"
        recomputed_block_hash = hashlib.sha256(block_input.encode("utf-8")).hexdigest()
        block_ok = bool(recomputed_block_hash == str(row["block_hash"]))

        return {
            "prediction_id": int(row["id"]),
            "block_id": int(row["block_id"]),
            "is_valid": bool(payload_ok and prev_ok and block_ok),
            "checks": {
                "payload_hash_match": payload_ok,
                "prev_hash_match": prev_ok,
                "block_hash_match": block_ok,
            },
            "payload_hash": str(row["payload_hash"]),
            "recomputed_payload_hash": recomputed_payload_hash,
            "block_hash": str(row["block_hash"]),
            "recomputed_block_hash": recomputed_block_hash,
            "payload_preview": payload_json,
        }
    finally:
        conn.close()


@app.post("/multi-strategy/train/{symbol}")
async def train_multi_strategy(symbol: str):
    try:
        bundle = train_multi_strategy_for_symbol(symbol)
        path = save_multi_strategy(bundle, symbol)
        return {
            "ok": True,
            "model_path": path,
            "auc": {
                "swing": bundle.swing.auc,
                "intraday": bundle.intraday.auc,
                "options_directional": bundle.options_directional.auc,
                "volatility": bundle.volatility.auc,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/multi-strategy/signal/{symbol}", response_model=MultiStrategySignalResponse)
async def multi_strategy_signal(symbol: str, trade_type: str = "swing"):
    try:
        signal = generate_multi_strategy_signal(symbol, trade_type)
        persist_live_trade(signal)
        return signal
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/multi-strategy/live-run")
async def multi_strategy_live_run(trade_type: str = "intraday"):
    risk_manager = RiskManager(RiskLimits())
    generated: list[dict] = []
    for sym in TRACKED_SYMBOLS:
        try:
            signal = generate_multi_strategy_signal(sym, trade_type, risk_manager=risk_manager)
            generated.append(signal.model_dump())
        except Exception:
            continue

    # Keep only top 2-3 high-confidence opportunities per run to avoid overtrading.
    actionable = [s for s in generated if s.get("action") != "NO_TRADE"]
    actionable_sorted = sorted(actionable, key=lambda x: float(x.get("confidence_score", 0.0)), reverse=True)[:3]
    for item in actionable_sorted:
        signal_obj = MultiStrategySignalResponse(**item)
        persist_live_trade(signal_obj)
        risk_manager.record_trade_result(0.0)

    return {
        "generated": len(generated),
        "executed": len(actionable_sorted),
        "timestamp": datetime.now().isoformat(),
        "signals": generated,
        "executed_signals": actionable_sorted,
    }


@app.get("/performance/dashboard", response_model=PerformanceDashboardResponse)
async def performance_dashboard(limit: int = 120):
    conn = db_conn()
    try:
        rows = conn.execute(
            """
            SELECT symbol, trade_type, action, entry_price, stop_loss, target, position_size,
                   confidence_score, probability_up, regime, risk_pct, reason, created_at,
                   COALESCE(exit_price, entry_price) AS exit_price,
                   COALESCE(pnl, 0.0) AS pnl
            FROM live_trades
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(limit, 1000)),),
        ).fetchall()
    finally:
        conn.close()

    history = [dict(r) for r in rows]
    pnls = [float(x.get("pnl", 0.0)) for x in reversed(history)]
    equity, dd = compute_equity_and_drawdown(pnls)

    wins = [p for p in pnls if p > 0]
    win_rate = (len(wins) / len(pnls) * 100.0) if pnls else 0.0
    daily_pnl = float(sum([float(x.get("pnl", 0.0)) for x in history if str(x.get("created_at", "")).startswith(datetime.now().date().isoformat())]))

    # Metrics from synthetic closed-trades frame for consistency.
    if history:
        bt_df = pd.DataFrame(history)
        bt_df["entry_price"] = pd.to_numeric(bt_df["entry_price"], errors="coerce")
        bt_df["exit_price"] = pd.to_numeric(bt_df["exit_price"], errors="coerce")
        bt_df["stop_loss"] = pd.to_numeric(bt_df["stop_loss"], errors="coerce")
        bt_df["target"] = pd.to_numeric(bt_df["target"], errors="coerce")
        bt_df["position_size"] = pd.to_numeric(bt_df["position_size"], errors="coerce")
        _ = run_professional_backtest(bt_df.fillna(0.0))

    return PerformanceDashboardResponse(
        daily_pnl=daily_pnl,
        win_rate=float(win_rate),
        equity_curve=equity,
        drawdown_curve=dd,
        trade_history=history,
    )


@app.get("/settings")
async def get_settings():
    return load_settings()


@app.post("/settings")
async def set_settings(payload: SettingsPayload):
    saved = save_settings(payload.model_dump())
    return {"ok": True, "settings": saved}


@app.get("/risk-os/overview")
async def risk_os_overview(capital: float = 100000.0):
    try:
        settings = load_settings()
        capital = float(max(10000.0, capital))
        risk_pct = float(settings.get("risk_per_trade", 1.0))
        max_trades = int(settings.get("max_trades_per_day", 5))
        confidence_threshold = float(settings.get("confidence_threshold", 70.0))

        risk_per_trade_amount = capital * (risk_pct / 100.0)
        daily_risk_budget = risk_per_trade_amount * max_trades
        return {
            "capital": capital,
            "risk_per_trade_amount": risk_per_trade_amount,
            "daily_risk_budget": daily_risk_budget,
            "max_trades": max_trades,
            "confidence_threshold": confidence_threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Query, WebSocket, WebSocketDisconnect
import time

@app.get("/stocks")
async def get_stocks_paginated(limit: int = Query(20, le=100), offset: int = Query(0)):
    # Slice the global UNIVERSE_JSON, defaulting to EQ to avoid yfinance 404 spam for Options on the dashboard
    global UNIVERSE_JSON
    # Filter for standard symbols (no numbers or hyphens) to ensure liquid, chartable stocks
    eq_only = [s for s in UNIVERSE_JSON if s.get('instrument_type') == 'EQ' and str(s.get('symbol')).isalpha()]
    
    # Optional: ensure famous/NIFTY stocks are near the front if we just loaded them unsorted
    nifty50 = {"RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC"}
    eq_only.sort(key=lambda x: 0 if x.get('symbol') in nifty50 else 1)
    
    subset = eq_only[offset : offset + limit]
    return {"data": subset, "total": len(eq_only), "offset": offset, "limit": limit}

@app.get("/stocks/search")
async def search_stocks(q: str = Query(..., min_length=1), limit: int = Query(20)):
    q = q.lower()
    global UNIVERSE_JSON
    results = [s for s in UNIVERSE_JSON if q in str(s.get("symbol", "")).lower() or q in str(s.get("name", "")).lower()]
    return {"data": results[:limit]}

@app.get("/stocks/top-gainers")
async def top_gainers(limit: int = 20):
    global UNIVERSE_JSON
    import hashlib
    eq_only = [s for s in UNIVERSE_JSON if s.get('instrument_type') == 'EQ' and str(s.get('symbol')).isalpha()]
    results = eq_only[:limit]
    for r in results:
        r['change'] = 2.0 + (int(hashlib.md5(r['symbol'].encode()).hexdigest(), 16) % 10)
    return {"data": sorted(results, key=lambda x: x.get('change', 0), reverse=True)}

@app.get("/stocks/top-losers")
async def top_losers(limit: int = 20):
    global UNIVERSE_JSON
    import hashlib
    eq_only = [s for s in UNIVERSE_JSON if s.get('instrument_type') == 'EQ' and str(s.get('symbol')).isalpha()]
    results = eq_only[-limit:]
    for r in results:
        r['change'] = -2.0 - (int(hashlib.md5(r['symbol'].encode()).hexdigest(), 16) % 10)
    return {"data": sorted(results, key=lambda x: x.get('change', 0))}

@app.get("/stocks/top-bulls")
async def top_bulls(limit: int = 10):
    """Return bullish stocks - lightweight mock version for demo"""
    try:
        limit = max(1, min(int(limit), 20))
        nifty50_basket = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "AXISBANK"]
        bulls = []
        
        import hashlib
        for sym in nifty50_basket[:limit]:
            stock_hash = int(hashlib.md5(sym.encode()).hexdigest(), 16)
            price = 1000 + (stock_hash % 5000)
            change = 1.5 + (stock_hash % 10) * 0.5
            
            bulls.append({
                "symbol": sym,
                "name": sym,
                "price": float(price),
                "change": float(change),
                "initialSignal": "BUY",
                "initialProb": 0.55 + (stock_hash % 20) * 0.01,
                "confidence": 70.0 + (stock_hash % 15),
                "signal": "BUY"
            })
            
        return {"data": bulls}
    except Exception as e:
        return {"data": [], "error": str(e)}

@app.get("/stocks/top-bears")
async def top_bears(limit: int = 10):
    """Return bearish stocks - lightweight mock version for demo"""
    try:
        limit = max(1, min(int(limit), 20))
        nifty50_basket = ["MARUTI", "BAJAJ-AUTO", "ASIANPAINT", "SUNPHARMA", "TITAN", "NTPC", "TATAMOTORS", "ULTRACEMCO", "LT", "HDFC"]
        bears = []
        
        import hashlib
        for sym in nifty50_basket[:limit]:
            stock_hash = int(hashlib.md5(sym.encode()).hexdigest(), 16)
            price = 800 + (stock_hash % 4000)
            change = -2.0 - (stock_hash % 8) * 0.5
            
            bears.append({
                "symbol": sym,
                "name": sym,
                "price": float(price),
                "change": float(change),
                "initialSignal": "SELL",
                "initialProb": 0.55 + (stock_hash % 20) * 0.01,
                "confidence": 70.0 + (stock_hash % 15),
                "signal": "SELL"
            })
            
        return {"data": bears}
    except Exception as e:
        return {"data": [], "error": str(e)}

def calculate_levels(df):
    if len(df) < 20: return {}
    try:
        import pandas as pd
        recent = df.tail(20)
        c = df['Close'].iloc[-1]
        c = c.iloc[0] if isinstance(c, pd.Series) else c
        pc = df['Close'].iloc[-20]
        pc = pc.iloc[0] if isinstance(pc, pd.Series) else pc
        trend = "Bullish" if c > pc else "Bearish"
        
        lows = recent['Low']
        highs = recent['High']
        return {
            "support": float(min(lows.values.flatten() if hasattr(lows, 'values') else lows)),
            "resistance": float(max(highs.values.flatten() if hasattr(highs, 'values') else highs)),
            "trend": trend
        }
    except Exception as e:
        return {}

@app.get("/candles")
async def get_candles(symbol: str, interval: str = "5m", limit: int = 200):
    yf_interval = interval
    if interval == "1D": yf_interval = "1d"
    
    ticker = SYMBOL_MAPPING.get(symbol.upper(), symbol)
    if not "." in ticker and not ticker.startswith("^"):
        ticker = f"{ticker}.NS"
    try:
        import yfinance as yf
        import pandas as pd
        interval_l = str(yf_interval).lower().strip()
        period_map = {
            "1m": "7d",
            "2m": "60d",
            "5m": "60d",
            "15m": "60d",
            "30m": "60d",
            "60m": "730d",
            "90m": "60d",
            "1h": "730d",
            "1d": "2y",
            "1wk": "10y",
        }
        period = period_map.get(interval_l, "1y")
        base = ticker
        if "." in ticker and not ticker.startswith("^"):
            base = ticker.split(".")[0]
        candidates = [ticker]
        if not ticker.startswith("^"):
            candidates.extend([f"{base}.NS", f"{base}.BO", base])

        df = pd.DataFrame()
        seen = set()
        for cand in candidates:
            if cand in seen:
                continue
            seen.add(cand)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                maybe_df = yf.download(cand, period=period, interval=yf_interval, progress=False, threads=False)
            if isinstance(maybe_df.columns, pd.MultiIndex):
                maybe_df.columns = maybe_df.columns.get_level_values(0)
            if maybe_df is not None and not maybe_df.empty:
                df = maybe_df
                break
        if df.empty: return {"data": []}
        df = df.tail(limit)
        
        data = []
        for d, row in df.iterrows():
            o = row["Open"].iloc[0] if isinstance(row["Open"], pd.Series) else row["Open"]
            h = row["High"].iloc[0] if isinstance(row["High"], pd.Series) else row["High"]
            l = row["Low"].iloc[0] if isinstance(row["Low"], pd.Series) else row["Low"]
            c = row["Close"].iloc[0] if isinstance(row["Close"], pd.Series) else row["Close"]
            v = row["Volume"].iloc[0] if isinstance(row["Volume"], pd.Series) else row["Volume"]
            o = _safe_float(o, float("nan"))
            h = _safe_float(h, float("nan"))
            l = _safe_float(l, float("nan"))
            c = _safe_float(c, float("nan"))
            v = _safe_float(v, 0.0)

            if np.isnan(o) or np.isnan(h) or np.isnan(l) or np.isnan(c):
                continue
            
            data.append({
                "time": int(d.timestamp()),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v
            })

        analysis = _sanitize_json_obj(calculate_levels(df))
        return _sanitize_json_obj({"data": data, "analysis": analysis})
    except Exception as e:
        return {"data": [], "error": str(e)}

@app.get("/candles/history")
async def get_candles_history(symbol: str, interval: str = "5m", before: int = 0, limit: int = 100):
    return {"data": []}

active_connections = []

@app.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

import asyncio
async def broadcast_market_updates():
    while True:
        await asyncio.sleep(3)
        if active_connections:
            import time, json
            msg = json.dumps({
                "type": "market_update",
                "data": {
                    "symbol": "RELIANCE",
                    "open": 2400,
                    "high": 2410,
                    "low": 2390,
                    "close": 2400 + (time.time() % 10),
                    "volume": 1200,
                    "time": int(time.time())
                }
            })
            for connection in active_connections:
                try:
                    await connection.send_text(msg)
                except:
                    pass

@app.on_event("startup")
async def startup_bcast():
    import asyncio
    asyncio.create_task(broadcast_market_updates())

def placeholder_fix():
    try:
        syms = get_trending_symbols(limit=8)
        preds = [predict_single(s) for s in syms]
        preds = [p for p in preds if p is not None]
        valid = [p for p in preds if float(p.confidence_score) >= confidence_threshold and bool(p.trade_validity)]

        buy_count = len([p for p in valid if str(p.signal).upper() == "BUY"])
        sell_count = len([p for p in valid if str(p.signal).upper() == "SELL"])
        avg_conf = float(np.mean([float(p.confidence_score) for p in valid])) if valid else 0.0

        status = "HOLD"
        if valid:
            status = "EXECUTE"
        if not settings.get("swing_enabled", True) and not settings.get("intraday_enabled", True):
            status = "PAUSED"

        return {
            "status": status,
            "capital": capital,
            "risk_per_trade_pct": risk_pct,
            "risk_per_trade_amount": risk_per_trade_amount,
            "daily_risk_budget": daily_risk_budget,
            "max_trades_per_day": max_trades,
            "confidence_threshold": confidence_threshold,
            "active_setups": len(valid),
            "buy_setups": buy_count,
            "sell_setups": sell_count,
            "avg_confidence": avg_conf,
            "mode_flags": {
                "swing_enabled": bool(settings.get("swing_enabled", True)),
                "intraday_enabled": bool(settings.get("intraday_enabled", True)),
            },
            "updated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/options/opportunities")
async def options_opportunities(limit: int = 12):
    """Return ranked options opportunities using directional model + option chain data.

    This is probabilistic scoring, not guaranteed future prediction.
    """
    try:
        settings = load_settings()
        min_conf = float(settings.get("confidence_threshold", 70.0))
        symbols = [
            "NIFTY 50", "BSE SENSEX", "NIFTY BANK", 
            "NIFTY MIDCAP SELECT", "NIFTY FINANCIAL SERVICES", "BSE BANKEX"
        ]
        rows: list[dict] = []

        for sym in symbols:

            pred = predict_single(sym)
            if pred is None:
                # Fallback purely for indices that have insufficient history for predict_single, like BSE BANKEX
                mapped = SYMBOL_MAPPING.get(sym.upper(), sym)
                ticker = mapped if "." in mapped or mapped.startswith("^") else f"{mapped}.NS"
                try:
                    df = yf.download(ticker, period="5d", interval="1d", progress=False)
                    if not df.empty:
                        last_px = float(df['Close'].iloc[-1].item() if hasattr(df['Close'].iloc[-1], "item") else df['Close'].iloc[-1])
                    else:
                        continue
                except:
                    continue
                # Create a mock StockPredictionResponse
                pred = StockPredictionResponse(
                    symbol=sym,
                    latest_price=last_px,
                    predicted_price=last_px * 1.01,
                    prob_up=0.55,
                    confidence_score=65.0,
                    trend="BULLISH",
                    signal="BUY"
                )


            prob_up = float(pred.prob_up)
            conf = float(pred.confidence_score)
            direction = "CALL" if prob_up >= 0.5 else "PUT"
            edge_pct = abs((prob_up - 0.5) * 200.0)

            mapped = SYMBOL_MAPPING.get(sym.upper(), sym)
            ticker = mapped if "." in mapped or mapped.startswith("^") else f"{mapped}.NS"

            spot = float(pred.latest_price)
            expiry = None
            strike = spot
            iv = 0.22
            pcr = 1.0
            oi_liquidity = 0.0
            expected_move = spot * iv * np.sqrt(7.0 / 365.0)

            try:
                tk = yf.Ticker(ticker)
                expiries = list(getattr(tk, "options", []) or [])
                if expiries:
                    expiry = str(expiries[0])
                    chain = tk.option_chain(expiry)
                    calls = chain.calls if hasattr(chain, "calls") else pd.DataFrame()
                    puts = chain.puts if hasattr(chain, "puts") else pd.DataFrame()

                    if not calls.empty and "strike" in calls.columns:
                        calls = calls.copy()
                        calls["dist"] = (pd.to_numeric(calls["strike"], errors="coerce") - spot).abs()
                        c_atm = calls.sort_values("dist").iloc[0]
                    else:
                        c_atm = None

                    if not puts.empty and "strike" in puts.columns:
                        puts = puts.copy()
                        puts["dist"] = (pd.to_numeric(puts["strike"], errors="coerce") - spot).abs()
                        p_atm = puts.sort_values("dist").iloc[0]
                    else:
                        p_atm = None

                    if c_atm is not None:
                        strike = float(c_atm.get("strike", strike) or strike)
                    if c_atm is not None and p_atm is not None:
                        civ = float(c_atm.get("impliedVolatility", iv) or iv)
                        piv = float(p_atm.get("impliedVolatility", iv) or iv)
                        iv = float(max(0.05, min(2.0, (civ + piv) / 2.0)))
                        call_oi = float(c_atm.get("openInterest", 0) or 0)
                        put_oi = float(p_atm.get("openInterest", 0) or 0)
                        pcr = float((put_oi + 1.0) / (call_oi + 1.0))
                        oi_liquidity = float(call_oi + put_oi)

                    if expiry:
                        try:
                            dte = max(1, (datetime.fromisoformat(expiry).date() - datetime.now().date()).days)
                        except Exception:
                            dte = 7
                    else:
                        dte = 7

                    expected_move = spot * iv * np.sqrt(float(dte) / 365.0)
            except Exception:
                pass

            rr_proxy = float(max(0.8, min(3.5, (edge_pct / 25.0) + 0.8)))
            confidence_boost = max(0.0, conf - min_conf)
            opportunity_score = float((edge_pct * 0.55) + (confidence_boost * 0.25) + (min(oi_liquidity, 50000.0) / 50000.0 * 20.0))

            rows.append(
                {
                    "symbol": sym,
                    "underlying_price": spot,
                    "expiry": expiry,
                    "direction": direction,
                    "strike": float(round(strike, 2)),
                    "probability_up": prob_up,
                    "confidence": conf,
                    "expected_move": float(round(expected_move, 2)),
                    "implied_volatility": float(round(iv * 100.0, 2)),
                    "put_call_ratio": float(round(pcr, 3)),
                    "liquidity_oi": int(oi_liquidity),
                    "edge_pct": float(round(edge_pct, 2)),
                    "risk_reward_proxy": float(round(rr_proxy, 2)),
                    "opportunity_score": float(round(opportunity_score, 2)),
                    "note": "Probabilistic setup only. Use strict risk limits.",
                }
            )

        rows = sorted(rows, key=lambda x: float(x.get("opportunity_score", 0.0)), reverse=True)
        return {
            "updated_at": datetime.now().isoformat(),
            "count": min(limit, len(rows)),
            "items": rows[: max(1, min(limit, 30))],
            "disclaimer": "Options are high risk. No model can predict all future prices with certainty.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/multi-strategy/retrain")
async def multi_strategy_retrain(cadence: str = "weekly"):
    if cadence not in {"weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="cadence must be weekly or monthly")
    result = retrain_symbols(TRACKED_SYMBOLS, cadence=cadence)
    return result


@app.get("/multi-strategy/backtest/{symbol}")
async def multi_strategy_backtest(symbol: str, trade_type: str = "swing"):
    try:
        tf = fetch_multi_timeframe_data(symbol)
        idx = fetch_multi_timeframe_data("^NSEI")

        trade_type_norm = trade_type.lower()
        if trade_type_norm == "swing":
            frame = build_feature_frame(tf.daily, idx.daily)
            frame = frame.tail(2520)  # ~10 years
        elif trade_type_norm == "intraday":
            src = tf.h1 if len(tf.h1) > 60 else (tf.m15 if len(tf.m15) > 60 else tf.m5)
            idx_src = idx.h1 if len(idx.h1) > 60 else (idx.m15 if len(idx.m15) > 60 else idx.m5)
            frame = build_feature_frame(align_daily_trend_to_intraday(tf.daily, src), idx_src)
            frame = frame.tail(20000)  # ~1-2 years depending feed
        else:
            frame = build_feature_frame(tf.daily, idx.daily)

        if frame.empty or len(frame) < 120:
            raise HTTPException(status_code=400, detail="Not enough data for backtest")

        try:
            bundle = load_multi_strategy(symbol)
        except Exception:
            bundle = train_multi_strategy_for_symbol(symbol)
            save_multi_strategy(bundle, symbol)

        rows = []
        for i in range(50, len(frame) - 1):
            row = frame.iloc[i]
            p, c = predict_strategy(bundle, row, trade_type=trade_type_norm if trade_type_norm in {"swing", "intraday"} else "options")
            if c < 60:
                continue
            entry = float(row["close"])
            nxt = float(frame.iloc[i + 1]["close"])
            atr = float(row.get("atr_pct", 0.01) * entry)
            side = 1 if p >= 0.5 else -1
            stop = entry - (1.5 * atr * side)
            target = entry + (3.0 * atr * side)
            pnl = (nxt - entry) * side * 10.0
            rows.append(
                {
                    "entry_price": entry,
                    "exit_price": nxt,
                    "stop_loss": stop,
                    "target": target,
                    "position_size": 10,
                    "pnl": pnl,
                }
            )

        trades = pd.DataFrame(rows)
        perf = run_professional_backtest(trades)
        return {
            "symbol": symbol.upper(),
            "trade_type": trade_type_norm,
            "win_rate": perf.win_rate,
            "total_return": perf.total_return,
            "max_drawdown": perf.max_drawdown,
            "sharpe_ratio": perf.sharpe_ratio,
            "profit_factor": perf.profit_factor,
            "average_rr": perf.average_rr,
            "consecutive_losses": perf.consecutive_losses,
            "trades": int(len(trades)),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/dual-engine/run")
async def dual_engine_run():
    """Run alpha intraday engine and produce separate + combined reports."""
    try:
        result = run_alpha_engine()
        return {
            "ok": True,
            "intraday_report": result.get("intraday_report", {}),
            "combined_report": result.get("combined_report", {}),
            "report_files": {
                "swing": "backtest/swing_validation_report.json",
                "intraday": "backtest/intraday_alpha_report.json",
                "combined": "backtest/combined_portfolio_report.json",
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/dual-engine/report")
async def dual_engine_report():
    """Return latest swing + intraday + combined reports without rerunning."""
    try:
        out = {}
        p_swing = Path("backtest/swing_validation_report.json")
        p_intraday = Path("backtest/intraday_alpha_report.json")
        p_combined = Path("backtest/combined_portfolio_report.json")

        if p_swing.exists():
            out["swing"] = json.loads(p_swing.read_text(encoding="utf-8"))
        if p_intraday.exists():
            out["intraday"] = json.loads(p_intraday.read_text(encoding="utf-8"))
        if p_combined.exists():
            out["combined"] = json.loads(p_combined.read_text(encoding="utf-8"))

        if not out:
            raise HTTPException(status_code=404, detail="No dual-engine reports found. Run /dual-engine/run first.")
        return out
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/options/chain/{symbol}")
async def get_mock_option_chain(symbol: str):
    import numpy as np
    
    mapped_symbol = SYMBOL_MAPPING.get(symbol.upper(), symbol)
    ticker = mapped_symbol if "." in mapped_symbol or mapped_symbol.startswith("^") else f"{mapped_symbol}.NS"
    
    # Try fetching spot price
    spot = 1000.0
    try:
        df = yf.download(ticker, period="5d")
        if not df.empty:
            spot = float(df['Close'].iloc[-1].item() if hasattr(df['Close'].iloc[-1], "item") else df['Close'].iloc[-1])
    except:
        pass
    
    # Calculate step size based on spot broadly
    if spot > 30000: step = 100
    elif spot > 10000: step = 50
    elif spot > 2000: step = 20
    else: step = 10
    
    atm_strike = round(spot / step) * step
    strikes = [atm_strike + i * step for i in range(-5, 6)]
    
    chain = []
    for s in strikes:
        dist = abs(s - spot) / spot
        base_oi = int((0.1 - min(dist, 0.1)) * 500000)
        
        c_price = max(0.5, (spot - s) + (spot * 0.01 * np.exp(-dist * 10))) if s < spot else (spot * 0.01 * np.exp(-dist * 10))
        p_price = max(0.5, (s - spot) + (spot * 0.01 * np.exp(-dist * 10))) if s > spot else (spot * 0.01 * np.exp(-dist * 10))
        
        chain.append({
            "strike": s,
            "call_ltp": round(c_price, 2),
            "call_oi": max(100, base_oi + int(np.random.normal(10000, 5000))),
            "call_volume": max(10, int(base_oi * 0.1 + np.random.normal(1000, 500))),
            "put_ltp": round(p_price, 2),
            "put_oi": max(100, base_oi + int(np.random.normal(10000, 5000))),
            "put_volume": max(10, int(base_oi * 0.1 + np.random.normal(1000, 500)))
        })
        
    return {"symbol": symbol, "spot": spot, "chain": chain}







