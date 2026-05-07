from __future__ import annotations

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator, MACD
from ta.volatility import AverageTrueRange


FEATURE_SET_SWING = [
    "ret_1", "ret_3", "ret_5", "rsi", "macd", "macd_signal", "adx", "atr_pct",
    "support_zone", "resistance_zone", "breakout_flag", "liquidity_sweep", "candle_bias",
    "volume_spike", "delivery_percentage", "acc_dist", "index_trend", "sector_strength_rank",
    "open_interest_change", "put_call_ratio", "max_pain_distance", "iv_percentile",
    "volatility_regime", "sample_weight",
]

FEATURE_SET_INTRADAY = [
    "ret_1", "ret_3", "ret_5", "rsi", "macd", "adx", "atr_pct", "volume_spike",
    "breakout_flag", "liquidity_sweep", "candle_bias", "daily_trend", "volatility_regime",
    "sample_weight",
]

FEATURE_SET_OPTIONS = [
    "ret_1", "ret_3", "rsi", "adx", "put_call_ratio", "open_interest_change",
    "max_pain_distance", "iv_percentile", "volatility_regime", "sample_weight",
]


def classify_regime(adx: float, atr_pct: float, vol_regime: float) -> str:
    if atr_pct >= 0.03 or vol_regime >= 0.7:
        return "HIGH_VOLATILITY"
    if adx >= 25:
        return "TRENDING"
    if atr_pct <= 0.012 and adx < 18:
        return "LOW_VOLATILITY"
    return "SIDEWAYS"


def build_feature_frame(df: pd.DataFrame, index_df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df.empty or len(df) < 80:
        return pd.DataFrame()

    close = pd.to_numeric(df["Close"], errors="coerce")
    high = pd.to_numeric(df["High"], errors="coerce")
    low = pd.to_numeric(df["Low"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")

    ret_1 = close.pct_change()
    ret_3 = close.pct_change(3)
    ret_5 = close.pct_change(5)

    rsi = RSIIndicator(close, 14).rsi()
    macd_obj = MACD(close)
    macd = macd_obj.macd()
    macd_signal = macd_obj.macd_signal()
    adx = ADXIndicator(high, low, close, 14).adx()
    atr = AverageTrueRange(high, low, close, 14).average_true_range()
    atr_pct = atr / (close + 1e-9)

    support_zone = close.rolling(20).min()
    resistance_zone = close.rolling(20).max()
    breakout_flag = np.where(close > resistance_zone.shift(1), 1, np.where(close < support_zone.shift(1), -1, 0))
    liquidity_sweep = np.where((high > resistance_zone.shift(1)) & (close < resistance_zone.shift(1)), 1, 0)

    _candle_body = (close - pd.to_numeric(df["Open"], errors="coerce")).abs()
    candle_range = (high - low).replace(0, np.nan)
    candle_bias = ((close - pd.to_numeric(df["Open"], errors="coerce")) / (candle_range + 1e-9)).clip(-1, 1)

    volume_spike = volume / (volume.rolling(20).mean() + 1e-9)
    delivery_percentage = (volume / (volume.rolling(10).mean() + 1e-9)).clip(0, 5)

    clv = ((close - low) - (high - close)) / ((high - low) + 1e-9)
    acc_dist = (clv * volume).cumsum()

    index_trend = pd.Series(0.0, index=df.index)
    sector_strength_rank = ret_5.rank(pct=True)
    if index_df is not None and not index_df.empty and "Close" in index_df.columns:
        idx_close = pd.to_numeric(index_df["Close"], errors="coerce").reindex(df.index, method="ffill")
        idx_ma20 = idx_close.rolling(20).mean()
        index_trend = (idx_close - idx_ma20) / (idx_ma20 + 1e-9)
        sector_strength_rank = (ret_5 - idx_close.pct_change(5)).rank(pct=True)

    open_interest_change = volume.pct_change().rolling(3).mean().fillna(0.0)
    put_call_ratio = ((volume.where(candle_bias < 0, 0).rolling(10).mean() + 1) / (volume.where(candle_bias > 0, 0).rolling(10).mean() + 1)).fillna(1.0)
    max_pain_distance = ((close - close.rolling(30).median()) / (close.rolling(30).median() + 1e-9)).fillna(0.0)
    iv_proxy = atr_pct.rolling(20).mean().fillna(0.0)
    iv_percentile = iv_proxy.rank(pct=True)

    vol_med = atr_pct.rolling(120).median()
    volatility_regime = np.where(atr_pct > vol_med, 1.0, 0.0)

    out = pd.DataFrame({
        "ret_1": ret_1,
        "ret_3": ret_3,
        "ret_5": ret_5,
        "rsi": rsi,
        "macd": macd,
        "macd_signal": macd_signal,
        "adx": adx,
        "atr_pct": atr_pct,
        "support_zone": support_zone,
        "resistance_zone": resistance_zone,
        "breakout_flag": breakout_flag,
        "liquidity_sweep": liquidity_sweep,
        "candle_bias": candle_bias,
        "volume_spike": volume_spike,
        "delivery_percentage": delivery_percentage,
        "acc_dist": acc_dist,
        "index_trend": index_trend,
        "sector_strength_rank": sector_strength_rank,
        "open_interest_change": open_interest_change,
        "put_call_ratio": put_call_ratio,
        "max_pain_distance": max_pain_distance,
        "iv_percentile": iv_percentile,
        "volatility_regime": volatility_regime,
        "sample_weight": pd.to_numeric(df.get("sample_weight", 1.0), errors="coerce").fillna(1.0),
        "close": close,
    }, index=df.index)

    out["target_up"] = (out["close"].shift(-1) > out["close"]).astype(int)
    out.replace([np.inf, -np.inf], np.nan, inplace=True)
    out.dropna(inplace=True)
    return out
