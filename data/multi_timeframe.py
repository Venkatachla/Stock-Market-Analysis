from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class TimeframeData:
    daily: pd.DataFrame
    h1: pd.DataFrame
    m15: pd.DataFrame
    m5: pd.DataFrame


def _download(symbol: str, interval: str, period: str) -> pd.DataFrame:
    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.index = pd.to_datetime(out.index)
    out = out.rename(columns=str.capitalize)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in out.columns:
            out[col] = np.nan
    out = out[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return out


def remove_illiquid_rows(df: pd.DataFrame, vol_col: str = "Volume", min_quantile: float = 0.15) -> pd.DataFrame:
    if df.empty or vol_col not in df.columns:
        return df
    threshold = float(df[vol_col].quantile(min_quantile)) if len(df) > 10 else 0.0
    return df[df[vol_col] >= threshold].copy()


def clean_time_series(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out.replace([np.inf, -np.inf], np.nan, inplace=True)
    out = out.ffill().dropna()
    return out


def add_recent_weights(df: pd.DataFrame, half_life_days: int = 180) -> pd.DataFrame:
    if df.empty:
        df = df.copy()
        df["sample_weight"] = 1.0
        return df
    out = df.copy()
    last_ts = out.index.max()
    delta_days = (last_ts - out.index).days.astype(float)
    out["sample_weight"] = np.exp(-np.log(2) * (delta_days / max(half_life_days, 1)))
    return out


def fetch_multi_timeframe_data(symbol: str) -> TimeframeData:
    ticker = symbol if ("." in symbol or symbol.startswith("^")) else f"{symbol}.NS"

    daily = _download(ticker, interval="1d", period="10y")
    h1 = _download(ticker, interval="60m", period="730d")
    m15 = _download(ticker, interval="15m", period="60d")
    m5 = _download(ticker, interval="5m", period="60d")

    h1 = add_recent_weights(clean_time_series(remove_illiquid_rows(h1)), half_life_days=120)
    daily = add_recent_weights(clean_time_series(remove_illiquid_rows(daily)), half_life_days=260)
    m15 = add_recent_weights(clean_time_series(remove_illiquid_rows(m15)), half_life_days=60)
    m5 = add_recent_weights(clean_time_series(remove_illiquid_rows(m5)), half_life_days=45)

    return TimeframeData(daily=daily, h1=h1, m15=m15, m5=m5)


def align_daily_trend_to_intraday(daily_df: pd.DataFrame, intraday_df: pd.DataFrame) -> pd.DataFrame:
    if daily_df.empty or intraday_df.empty:
        out = intraday_df.copy()
        out["daily_trend"] = 0.0
        return out

    daily = daily_df.copy()
    daily["daily_ma20"] = daily["Close"].rolling(20).mean()
    daily["daily_trend"] = (daily["Close"] - daily["daily_ma20"]) / (daily["daily_ma20"] + 1e-9)

    out = intraday_df.copy()
    out["d"] = out.index.date
    dtrend = pd.DataFrame({"d": daily.index.date, "daily_trend": daily["daily_trend"].values})
    merged = out.merge(dtrend, on="d", how="left")
    merged.set_index(intraday_df.index, inplace=True)
    merged.drop(columns=["d"], inplace=True)
    merged["daily_trend"] = merged["daily_trend"].fillna(0.0)
    return merged
