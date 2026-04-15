from pathlib import Path
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange

from utils.logger import get_logger

logger = get_logger(__name__)


FEATURE_COLUMNS = [
    "rsi",
    "macd",
    "macd_signal",
    "macd_hist",
    "sma_20",
    "sma_50",
    "sma_200",
    "ema_20",
    "ema_50",
    "bb_high",
    "bb_low",
    "bb_mid",
    "atr",
    "momentum",
    "daily_return",
    "rolling_vol",
    "volume_change",
    "rolling_mean",
    "rolling_std",
]


def compute_features_for_file(raw_path: Path, processed_dir: Path, nifty_df: pd.DataFrame | None = None, sector_ret: pd.Series | None = None) -> None:
    df = pd.read_csv(raw_path, parse_dates=["date"])
    # Drop header/artifact rows with missing dates
    df.dropna(subset=["date"], inplace=True)
    if df.empty:
        logger.warning("Empty data in %s", raw_path)
        return

    df.sort_values("date", inplace=True)
    if len(df) < 50:  # skip very short histories to avoid indicator window issues
        logger.warning("Not enough rows (%d) in %s; skipping", len(df), raw_path)
        return
    # Use Adj Close when available, otherwise fall back to Close
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    required_cols = [price_col, "High", "Low", "Volume"]
    for col in required_cols:
        if col not in df.columns:
            logger.warning("Missing %s in %s; skipping file", col, raw_path)
            return

    close = pd.to_numeric(df[price_col], errors="coerce")
    high = pd.to_numeric(df["High"], errors="coerce")
    low = pd.to_numeric(df["Low"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")

    df = df.assign(close=close, high=high, low=low, volume=volume)
    df.dropna(subset=["close", "high", "low", "volume"], inplace=True)
    if df.empty:
        logger.warning("All numeric rows dropped for %s", raw_path)
        return
    if len(df) < 20:
        logger.warning("Not enough usable rows (%d) in %s after cleaning; skipping", len(df), raw_path)
        return

    rsi = RSIIndicator(close, window=14)
    macd = MACD(close)
    sma20 = SMAIndicator(close, window=20)
    sma50 = SMAIndicator(close, window=50)
    sma200 = SMAIndicator(close, window=200)
    ema20 = EMAIndicator(close, window=20)
    ema50 = EMAIndicator(close, window=50)
    bb = BollingerBands(close, window=20, window_dev=2)
    atr = AverageTrueRange(high=high, low=low, close=close, window=14)

    # Optional index/sector alignments (reindex to stock dates)
    nifty_close = None
    if nifty_df is not None and not nifty_df.empty:
        nifty_close = pd.to_numeric(nifty_df.get("Close"), errors="coerce").reindex(df["date"])
    sector_ret_aligned = None
    if sector_ret is not None and not sector_ret.empty:
        sector_ret_aligned = sector_ret.reindex(df["date"])

    df_features = pd.DataFrame({
        "date": df["date"],
        "stock_symbol": raw_path.stem + ".NS",
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
        "close": close,
    })

    # Advanced features with safe fallbacks
    df_features["vol_spike"] = volume / volume.rolling(20).mean()
    adx = ADXIndicator(high=high, low=low, close=close, window=14)
    df_features["adx_14"] = adx.adx()

    if nifty_close is not None:
        stock_ret = close.pct_change()
        nifty_ret = nifty_close.pct_change()
        df_features["relative_strength_20"] = stock_ret.rolling(20).mean() / (nifty_ret.rolling(20).mean() + 1e-9)
        cov = stock_ret.rolling(60).cov(nifty_ret)
        var = nifty_ret.rolling(60).var()
        df_features["beta_60"] = cov / (var + 1e-9)
        df_features["vol_pct_20"] = stock_ret.rolling(20).std().rank(pct=True)
    else:
        df_features["relative_strength_20"] = 0.0
        df_features["beta_60"] = 0.0
        df_features["vol_pct_20"] = 0.5

    if sector_ret_aligned is not None:
        df_features["sector_mom_20"] = sector_ret_aligned.rolling(20).mean()
    else:
        df_features["sector_mom_20"] = 0.0

    # Price structure
    df_features["support_zone"] = close.rolling(20).min()
    df_features["resistance_zone"] = close.rolling(20).max()
    df_features["trend_strength"] = (ema20.ema_indicator() - ema50.ema_indicator()).abs() / (close.abs() + 1e-9)
    prev_support = close.shift(1).rolling(20).min()
    prev_resistance = close.shift(1).rolling(20).max()
    df_features["breakout_flag"] = np.where(close > prev_resistance, 1, np.where(close < prev_support, -1, 0))

    # Market context
    if nifty_close is not None:
        nifty_ma50 = nifty_close.rolling(50).mean()
        df_features["nifty_trend"] = (nifty_close - nifty_ma50) / (nifty_ma50 + 1e-9)
    else:
        df_features["nifty_trend"] = 0.0

    if sector_ret_aligned is not None:
        df_features["sector_strength_rank"] = sector_ret_aligned.rolling(20).mean().rank(pct=True)
    else:
        df_features["sector_strength_rank"] = df_features["relative_strength_20"].rank(pct=True)

    # Smart money (proxy features; true OI/FII/DII require exchange derivatives/cashflow data feeds)
    df_features["oi_change"] = volume.pct_change().rolling(5).mean()
    up_vol = pd.Series(np.where(close.diff() > 0, volume, 0.0), index=df_features.index)
    down_vol = pd.Series(np.where(close.diff() < 0, volume, 0.0), index=df_features.index)
    df_features["pcr_ratio"] = (down_vol.rolling(10).mean() + 1.0) / (up_vol.rolling(10).mean() + 1.0)
    df_features["open_interest_change"] = df_features["oi_change"]
    df_features["put_call_ratio"] = df_features["pcr_ratio"]
    df_features["delivery_percent"] = ((volume / (volume.rolling(20).mean() + 1e-9)) * 100.0).clip(lower=0.0)
    turnover = close * volume
    vol_profile_raw = turnover / (turnover.rolling(20).mean() + 1e-9)
    df_features["volume_profile"] = vol_profile_raw.rank(pct=True)
    rolling_vol = close.pct_change().rolling(20).std()
    vol_med = rolling_vol.rolling(120).median()
    df_features["volatility_regime"] = np.where(rolling_vol > vol_med, 1.0, 0.0)
    turnover = close * volume
    df_features["fii_dii_flow"] = turnover.pct_change().rolling(10).mean()

    # Placeholder sentiment in offline feature build (live sentiment is injected at inference).
    df_features["news_sentiment_score"] = 0.0

    df_features.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_features["target"] = (df_features["close"].shift(-1) > df_features["close"]).astype(int)
    essential = [
        "rsi","macd","macd_signal","macd_hist","sma_20","sma_50","sma_200",
        "ema_20","ema_50","bb_high","bb_low","bb_mid","atr","momentum","daily_return",
        "rolling_vol","volume_change","rolling_mean","rolling_std","target","close"
    ]
    df_features.dropna(subset=essential, inplace=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(processed_dir / raw_path.name, index=False)
    logger.info("Features computed for %s", raw_path.stem)


def _load_nifty(period: str = "3y") -> pd.DataFrame | None:
    try:
        import yfinance as yf

        df = yf.download("^NSEI", period=period, interval="1d", progress=False)
        if df.empty:
            return None
        df = df.rename_axis("date").reset_index()
        return df
    except Exception as exc:
        logger.warning("Could not load NIFTY data: %s", exc)
        return None


def run_feature_engineering(raw_dir: str = "data/raw", processed_dir: str = "data/processed", nifty_df: pd.DataFrame | None = None) -> None:
    raw_path = Path(raw_dir)
    processed_path = Path(processed_dir)
    files = list(raw_path.glob("*.csv"))
    if not files:
        logger.warning("No raw data files found in %s", raw_dir)
        return

    if nifty_df is None:
        nifty_df = _load_nifty()

    for file in files:
        compute_features_for_file(file, processed_path, nifty_df=nifty_df)


def load_combined_dataset(processed_dir: str = "data/processed") -> pd.DataFrame:
    processed_path = Path(processed_dir)
    frames = []
    for file in processed_path.glob("*.csv"):
        frames.append(pd.read_csv(file, parse_dates=["date"]))
    if not frames:
        logger.warning("No processed feature files found")
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    if "target" not in df.columns:
        logger.error("No target column in processed data")
        return pd.DataFrame()
    df["target"] = df["target"].astype(int)
    df.sort_values(["stock_symbol", "date"], inplace=True)
    return df
