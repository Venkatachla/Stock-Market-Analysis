#!/usr/bin/env python3
"""
Terminal CLI for live stock prediction using trained ensemble model.
Usage:
  python cli.py RELIANCE
  python cli.py TCS
  python cli.py INFY
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange

from features.engineer import FEATURE_COLUMNS
from training.dataset import make_sequences
from training.lstm_model import LSTMClassifier


LOOKBACK = 30
ENSEMBLE_WEIGHTS = {
    "xgb": 0.4,
    "lgbm": 0.3,
    "rf": 0.2,
    "lstm": 0.1,
}

DEFAULT_CACHE_DIR = Path(os.getenv("CACHE_DIR", ".cache_yf"))
DEFAULT_CACHE_MAX_AGE_HOURS = float(os.getenv("CACHE_MAX_AGE_HOURS", "12"))
DEFAULT_PERIOD = os.getenv("YF_PERIOD", "2y")
DEFAULT_NIFTY_PERIOD = os.getenv("NIFTY_PERIOD", "3y")
SYMBOL_CSV_PATH = Path(os.getenv("SYMBOL_CSV_PATH", "data/nse_symbols.csv"))

# Symbol mapping for NSE stocks (some have different Yahoo Finance symbols)
SYMBOL_MAPPING = {
    "SBI": "SBIN",      # State Bank of India
    "ADANIGREEN": "ADANIGREEN",
    "ADANIPORTS": "ADANIPORTS",
    "ADANIENT": "ADANIENT",
    "ADANIPOWER": "ADANIPOWER",
    "ADANIGAS": "ADANIGAS",
    "ONDCP": "ONDCP",
    "ONCG": "ONCG",
    "ANANT": "ANANTRAJ",
    "ANANT RAJ": "ANANTRAJ",
    "ANANTRAJ": "ANANTRAJ",
}


def load_symbol_catalog(path: Path = SYMBOL_CSV_PATH):
    """Load symbol catalog from CSV if present. Expected columns: symbol,name."""
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if "symbol" not in df.columns or "name" not in df.columns:
            print(f"{Colors.YELLOW}⚠ nse_symbols.csv missing columns 'symbol' and 'name'{Colors.RESET}")
            return None
        df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
        df["name"] = df["name"].astype(str).str.upper().str.strip()
        return df
    except Exception as exc:
        print(f"{Colors.YELLOW}⚠ Could not read symbol catalog: {exc}{Colors.RESET}")
        return None


def resolve_symbol(user_query: str, catalog_path: Path = SYMBOL_CSV_PATH):
    """Resolve user input to a ticker symbol using mappings and optional catalog."""
    q = user_query.upper().strip()

    if q in SYMBOL_MAPPING:
        return SYMBOL_MAPPING[q], None

    if len(q) <= 7 and q.replace("-", "").replace(".", "").isalnum():
        q_nospace = q.replace(" ", "")
        if q_nospace in SYMBOL_MAPPING:
            return SYMBOL_MAPPING[q_nospace], None
        return q, None

    catalog = load_symbol_catalog(catalog_path)
    if catalog is None:
        token = q.split()[0]
        if token in SYMBOL_MAPPING:
            return SYMBOL_MAPPING[token], None
        return token, None

    matches = catalog[catalog["name"].str.contains(q, case=False, na=False)]
    if matches.empty:
        token = q.split()[0]
        matches = catalog[catalog["name"].str.contains(token, case=False, na=False)]

    if matches.empty:
        return q.split()[0], None

    if len(matches) == 1:
        sym = matches.iloc[0]["symbol"]
        name = matches.iloc[0]["name"]
        return sym, name

    suggestions = matches.head(5)[["symbol", "name"]].values.tolist()
    return None, suggestions


def load_cached_data(ticker: str, cache_dir: Path, max_age_hours: float):
    """Load cached CSV if fresh enough."""
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"{ticker}.csv"
    if not cache_file.exists():
        return None
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    if datetime.now() - mtime > timedelta(hours=max_age_hours):
        return None
    try:
        df = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
        return df
    except Exception:
        return None


def cache_data(ticker: str, df: pd.DataFrame, cache_dir: Path):
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"{ticker}.csv"
    try:
        df.to_csv(cache_file)
    except Exception:
        pass


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def load_models():
    """Load trained models and scaler."""
    model_path = Path("models/tree_models.pkl")
    lstm_path = Path("models/lstm.pt")

    if not model_path.exists():
        print(f"{Colors.RED}❌ Models not found at {model_path}{Colors.RESET}")
        sys.exit(1)

    models = joblib.load(model_path)
    print(f"{Colors.GREEN}✓ Loaded tree models (XGB, LGBM, RF, Scaler){Colors.RESET}")

    lstm = None
    if lstm_path.exists():
        try:
            lstm = LSTMClassifier(input_size=len(FEATURE_COLUMNS), hidden_size=64, num_layers=2)
            lstm.load_state_dict(torch.load(lstm_path))
            lstm.eval()
            print(f"{Colors.GREEN}✓ Loaded LSTM model{Colors.RESET}")
        except Exception:
            print(f"{Colors.YELLOW}⚠ Could not load LSTM (will skip){Colors.RESET}")

    return {
        "xgb": models["xgb"],
        "lgbm": models["lgbm"],
        "rf": models["rf"],
        "scaler": models["scaler"],
        "lstm": lstm,
    }


def fetch_data(
    symbol,
    period: str = DEFAULT_PERIOD,
    use_cache: bool = True,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    cache_max_age_hours: float = DEFAULT_CACHE_MAX_AGE_HOURS,
):
    """Fetch stock data from Yahoo Finance with fallback options + caching."""
    base_symbol = SYMBOL_MAPPING.get(symbol, symbol)
    base_symbol_clean = base_symbol.replace(" ", "")

    symbols_to_try = [
        f"{base_symbol_clean}.NS",
        f"{base_symbol}.NS",
        f"{base_symbol_clean}",
        f"{base_symbol}",
        f"{base_symbol_clean}.BO",
    ]

    print(f"\n{Colors.CYAN}📊 Fetching {symbol} data...{Colors.RESET}")

    for ticker in symbols_to_try:
        cached = load_cached_data(ticker, cache_dir, cache_max_age_hours) if use_cache else None
        if cached is not None:
            print(f"{Colors.GREEN}✓ Using cached data for {ticker}{Colors.RESET}")
            return cached

        try:
            data = yf.download(ticker, period=period, interval="1d", progress=False)

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            if not data.empty and len(data) > 50:
                print(f"{Colors.GREEN}✓ Downloaded {len(data)} days of data (symbol: {ticker}){Colors.RESET}")
                if use_cache:
                    cache_data(ticker, data, cache_dir)
                return data
        except Exception:
            continue

    print(f"{Colors.RED}❌ No data found for {symbol}{Colors.RESET}")
    print(f"{Colors.YELLOW}💡 Tried: {', '.join(symbols_to_try)}{Colors.RESET}")
    print(f"{Colors.YELLOW}Suggestions:{Colors.RESET}")
    print(f"  - Check if symbol is correct (e.g., SBIN instead of SBI)")
    print(f"  - Some stocks might be delisted or not available in Yahoo Finance")
    print(f"  - Try: RELIANCE, TCS, INFY, HDFCBANK, WIPRO, MARUTI, ANANTRAJ")
    return None


def fetch_news_sentiment(symbol: str) -> float:
    """Fetch recent headline sentiment score for a symbol."""
    try:
        analyzer = SentimentIntensityAnalyzer()
        ticker = symbol if "." in symbol else f"{symbol}.NS"
        candidates = [ticker, ticker.replace(".NS", ""), symbol]
        news_items = []
        for cand in candidates:
            try:
                news_items = yf.Ticker(cand).news or []
                if news_items:
                    break
            except Exception:
                continue

        scores = []
        for item in news_items[:8]:
            title = (item.get("title") or "").strip()
            if title:
                scores.append(float(analyzer.polarity_scores(title)["compound"]))
        return float(np.mean(scores)) if scores else 0.0
    except Exception:
        return 0.0


def compute_features(df: pd.DataFrame, nifty_period: str = DEFAULT_NIFTY_PERIOD, symbol: str | None = None) -> pd.DataFrame | None:
    """Compute technical + advanced features aligned with FEATURE_COLUMNS."""
    if df.empty or len(df) < 50:
        print(f"{Colors.RED}❌ Not enough data to compute features (need at least 50 rows){Colors.RESET}")
        return None

    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    required = ["close", "high", "low", "volume"]
    for col in required:
        if col not in df.columns:
            print(f"{Colors.RED}❌ Missing column '{col}' in downloaded data{Colors.RESET}")
            return None

    try:
        close = pd.to_numeric(df["close"], errors="coerce")
        high = pd.to_numeric(df["high"], errors="coerce")
        low = pd.to_numeric(df["low"], errors="coerce")
        volume = pd.to_numeric(df["volume"], errors="coerce")

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

        # Smart money proxy features
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
        features_df["news_sentiment_score"] = 0.0

        if nifty_period:
            try:
                idx = yf.download("^NSEI", period=nifty_period, interval="1d", progress=False)
                if not idx.empty and "Close" in idx.columns:
                    idx_close = pd.to_numeric(idx["Close"], errors="coerce")
                    idx_close = idx_close.reindex(df.index, method=None)
                    stock_ret = close.pct_change()
                    nifty_ret = idx_close.pct_change()
                    features_df["relative_strength_20"] = stock_ret.rolling(20).mean() / (nifty_ret.rolling(20).mean() + 1e-9)
                    cov = stock_ret.rolling(60).cov(nifty_ret)
                    var = nifty_ret.rolling(60).var()
                    features_df["beta_60"] = cov / (var + 1e-9)
                    features_df["vol_pct_20"] = stock_ret.rolling(20).std().rank(pct=True)
                    idx_ma50 = idx_close.rolling(50).mean()
                    features_df["nifty_trend"] = (idx_close - idx_ma50) / (idx_ma50 + 1e-9)
                    features_df["sector_strength_rank"] = features_df["relative_strength_20"].rank(pct=True)
            except Exception as exc:
                print(f"{Colors.YELLOW}⚠ Could not load NIFTY for advanced features: {exc}{Colors.RESET}")

        if symbol:
            features_df.loc[features_df.index[-1], "news_sentiment_score"] = fetch_news_sentiment(symbol)

        features_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        essential = [
            "rsi", "macd", "macd_signal", "macd_hist", "sma_20", "sma_50", "sma_200",
            "ema_20", "ema_50", "bb_high", "bb_low", "bb_mid", "atr", "momentum", "daily_return",
            "rolling_vol", "volume_change", "rolling_mean", "rolling_std", "close",
        ]
        features_df.dropna(subset=essential, inplace=True)
        if features_df.empty:
            print(f"{Colors.RED}❌ Features computation resulted in empty dataframe{Colors.RESET}")
            return None

        print(f"{Colors.GREEN}✓ Computed features for {len(features_df)} time steps{Colors.RESET}")
        return features_df
    except Exception as exc:
        print(f"{Colors.RED}❌ Error computing features: {exc}{Colors.RESET}")
        return None


def predict(symbol, models, features_df):
    """Get prediction from ensemble model."""
    if len(features_df) < LOOKBACK + 1:
        print(f"{Colors.RED}❌ Not enough data for prediction (need {LOOKBACK + 1}, have {len(features_df)}){Colors.RESET}")
        return None

    print(f"\n{Colors.CYAN}🤖 Running ensemble prediction...{Colors.RESET}")

    scaler = models["scaler"]
    trained_cols = list(getattr(scaler, "feature_names_in_", FEATURE_COLUMNS))
    # Ensure we only use columns the scaler was fit on; fill missing with 0.0
    latest_row = features_df.iloc[-1]
    latest_aligned = latest_row.reindex(trained_cols).fillna(0.0)
    X_input = pd.DataFrame([latest_aligned], columns=trained_cols)
    X_scaled = scaler.transform(X_input)

    xgb_prob = models["xgb"].predict_proba(X_scaled)[:, 1][0]
    lgbm_prob = models["lgbm"].predict_proba(X_scaled)[:, 1][0]
    rf_prob = models["rf"].predict_proba(X_scaled)[:, 1][0]

    lstm_prob = None
    if models.get("lstm") is not None:
        try:
            seq_raw = features_df[trained_cols].reindex(columns=trained_cols).fillna(0.0)
            seq_scaled = scaler.transform(seq_raw)
            X_seq, _ = make_sequences(seq_scaled, np.zeros(len(seq_scaled)), lookback=LOOKBACK)
            if len(X_seq) > 0:
                with torch.no_grad():
                    preds = models["lstm"](torch.tensor(X_seq[-1:], dtype=torch.float32)).squeeze().item()
                    lstm_prob = float(preds)
        except Exception:
            pass

    prob_up = (
        ENSEMBLE_WEIGHTS["xgb"] * xgb_prob
        + ENSEMBLE_WEIGHTS["lgbm"] * lgbm_prob
        + ENSEMBLE_WEIGHTS["rf"] * rf_prob
        + (ENSEMBLE_WEIGHTS["lstm"] * lstm_prob if lstm_prob is not None else 0.0)
    )
    prob_up = float(max(0.0, min(1.0, prob_up)))
    prob_down = 1.0 - prob_up

    return {
        "prob_up": prob_up,
        "prob_down": prob_down,
        "xgb": xgb_prob,
        "lgbm": lgbm_prob,
        "rf": rf_prob,
        "lstm": lstm_prob,
    }


def print_signal(symbol, prediction, features_df):
    """Print prediction results neatly."""
    prob_up = prediction["prob_up"]
    prob_down = prediction["prob_down"]

    if prob_up > 0.55:
        signal = f"{Colors.GREEN}🔼 BULLISH{Colors.RESET}"
        confidence = prob_up
    elif prob_down > 0.55:
        signal = f"{Colors.RED}🔽 BEARISH{Colors.RESET}"
        confidence = prob_down
    else:
        signal = f"{Colors.YELLOW}➡️  NEUTRAL{Colors.RESET}"
        confidence = 0.5

    latest_price = features_df["close"].iloc[-1]
    date_str = features_df["date"].iloc[-1].strftime("%Y-%m-%d")

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{symbol}{Colors.RESET} | Signal: {signal} | Confidence: {confidence*100:.1f}%")
    print(f"Price: {Colors.CYAN}₹{latest_price:.2f}{Colors.RESET} | Date: {date_str}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

    bar_length = 30
    up_bar = int(bar_length * prob_up)
    down_bar = int(bar_length * prob_down)

    print(f"  {Colors.GREEN}UP  {Colors.RESET} [{Colors.GREEN}{'█' * up_bar}{Colors.RESET}{'░' * (bar_length - up_bar)}] {prob_up*100:5.1f}%")
    print(f"  {Colors.RED}DOWN{Colors.RESET} [{Colors.RED}{'█' * down_bar}{Colors.RESET}{'░' * (bar_length - down_bar)}] {prob_down*100:5.1f}%")

    print(f"\n{Colors.BOLD}Model Breakdown:{Colors.RESET}")
    print(f"  🌳 XGBoost   (40%): {prediction['xgb']*100:5.1f}%")
    print(f"  🌲 LightGBM  (30%): {prediction['lgbm']*100:5.1f}%")
    print(f"  🌳 Random Forest (20%): {prediction['rf']*100:5.1f}%")
    if prediction['lstm'] is not None:
        print(f"  🧠 LSTM      (10%): {prediction['lstm']*100:5.1f}%")
    else:
        print(f"  🧠 LSTM      (10%): {Colors.YELLOW}Not loaded{Colors.RESET}")

    print(f"\n{Colors.BOLD}Recent Data (last 5 days):{Colors.RESET}")
    recent = features_df[["date", "close", "rsi", "macd"]].tail(5)
    for _, row in recent.iterrows():
        date = row["date"].strftime("%Y-%m-%d")
        price = row["close"]
        rsi = row["rsi"]
        macd_val = row["macd"]
        print(f"  {date}: ₹{price:.2f} | RSI: {rsi:5.1f} | MACD: {macd_val:7.4f}")

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def plot_ascii_chart(features_df, symbol):
    """Print simple ASCII chart of price movement."""
    prices = features_df["close"].tail(30).values

    if len(prices) < 2:
        return

    min_price = prices.min()
    max_price = prices.max()
    price_range = max_price - min_price if max_price != min_price else 1

    normalized = [(p - min_price) / price_range * 20 for p in prices]

    print(f"{Colors.BOLD}Price Chart (last 30 days):{Colors.RESET}\n")

    for level in range(20, -1, -2):
        price_at_level = min_price + (level / 20) * price_range
        line = f"  ₹{price_at_level:.0f} │"

        for i, norm_price in enumerate(normalized):
            if abs(norm_price - level) < 0.5:
                if i == len(normalized) - 1:
                    line += f" {Colors.CYAN}●{Colors.RESET}"
                else:
                    line += " ●"
            else:
                line += " │"
        print(line)

    print("       └" + "─" * (len(normalized) * 2))

    dates = features_df["date"].tail(30)
    print(f"\n  From: {dates.iloc[0].strftime('%Y-%m-%d')} → To: {dates.iloc[-1].strftime('%Y-%m-%d')}\n")


def parse_args():
    parser = argparse.ArgumentParser(description="STCOK ML Predictor CLI")
    parser.add_argument("symbol", nargs="+", help="Ticker symbol or company name")
    parser.add_argument("--period", default=DEFAULT_PERIOD, help="Yahoo Finance lookback period (e.g., 6mo, 1y, 2y)")
    parser.add_argument("--nifty-period", default=DEFAULT_NIFTY_PERIOD, help="Period for NIFTY download for advanced features")
    parser.add_argument("--cache-hours", type=float, default=DEFAULT_CACHE_MAX_AGE_HOURS, help="Cache freshness window in hours")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="Directory for price cache")
    parser.add_argument("--no-cache", action="store_true", help="Skip reading/writing the local price cache")
    parser.add_argument("--symbol-csv", type=Path, default=SYMBOL_CSV_PATH, help="Path to NSE symbol catalog CSV")
    return parser.parse_args()


def main():
    args = parse_args()

    user_query = " ".join(args.symbol).strip()

    symbol, suggestions = resolve_symbol(user_query, catalog_path=args.symbol_csv)
    if suggestions is not None:
        print(f"{Colors.YELLOW}Found multiple matches for '{user_query}':{Colors.RESET}")
        for sym, name in suggestions:
            print(f"  {sym} - {name.title()}")
        print(f"{Colors.YELLOW}Please rerun with the exact symbol above.{Colors.RESET}")
        sys.exit(1)

    if symbol is None:
        print(f"{Colors.RED}Could not resolve symbol for '{user_query}'{Colors.RESET}")
        sys.exit(1)

    print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 STCOK ML Predictor CLI{Colors.RESET}\n")

    models = load_models()

    data = fetch_data(
        symbol,
        period=args.period,
        use_cache=not args.no_cache,
        cache_dir=args.cache_dir,
        cache_max_age_hours=args.cache_hours,
    )
    if data is None:
        sys.exit(1)

    features_df = compute_features(data, nifty_period=args.nifty_period, symbol=symbol)
    if features_df is None:
        sys.exit(1)

    prediction = predict(symbol, models, features_df)
    if prediction is None:
        sys.exit(1)

    print_signal(symbol, prediction, features_df)
    plot_ascii_chart(features_df, symbol)

    print(f"{Colors.GREEN}✓ Prediction complete!{Colors.RESET}\n")


if __name__ == "__main__":
    main()
