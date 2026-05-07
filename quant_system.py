"""
Quantitative trading utilities: regime detection, regime-aware signals, backtesting,
threshold optimization, paper trading, and reporting.

This module is self-contained and uses existing dependencies: pandas, numpy, yfinance.
It does NOT retrain your models; plug your model's probability outputs where indicated.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

# ------------------------------------------------------------
# Regime detection
# ------------------------------------------------------------

def download_index(ticker: str = "^NSEI", period: str = "3y") -> pd.DataFrame:
    """Download index data (e.g., NIFTY 50: ^NSEI)."""
    df = yf.download(ticker, period=period, interval="1d", progress=False)
    if df.empty:
        raise ValueError(f"No data for index {ticker}")
    # yfinance can return MultiIndex columns like ('Close','^NSEI'). Flatten to OHLCV names.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.capitalize)
    return df


def compute_regime(df: pd.DataFrame) -> pd.DataFrame:
    """Classify regime per day using MA200, volatility, slope, returns.

    Regime logic (simple):
      - Bull: Close > MA200
      - Bear: Close < MA200
      - Sideways: otherwise
    """
    out = df.copy()
    out["ret"] = out["Close"].pct_change()
    out["ma200"] = out["Close"].rolling(200).mean()
    out["vol20"] = out["ret"].rolling(20).std()
    # Trend slope via rolling 60-day linear fit on Close
    def _slope(x: pd.Series) -> float:
        idx = np.arange(len(x))
        if len(x) < 2:
            return np.nan
        a, b = np.polyfit(idx, x, 1)
        return a

    out["slope60"] = out["Close"].rolling(60).apply(_slope, raw=False)

    def _label(row):
        if pd.isna(row["ma200"]):
            return "UNKNOWN"
        if row["Close"] > row["ma200"]:
            return "BULL"
        if row["Close"] < row["ma200"]:
            return "BEAR"
        return "SIDEWAYS"

    out["regime"] = out.apply(_label, axis=1)
    return out


# ------------------------------------------------------------
# Regime-aware signal adjustment
# ------------------------------------------------------------

def regime_adjusted_decision(prob_up: float, regime: str, base_threshold: float = 0.55) -> Tuple[bool, float, float]:
    """Return (enter_long, position_size, threshold_used)."""
    regime = (regime or "").upper()
    threshold = base_threshold
    size = 1.0

    if regime == "BULL":
        threshold = base_threshold
        size = 1.0
    elif regime == "BEAR":
        threshold = min(0.9, base_threshold + 0.05)  # require stronger edge
        size = 0.5                                   # cut size
    else:  # SIDEWAYS or unknown
        threshold = max(0.65, base_threshold)        # more selective
        size = 0.75

    enter = prob_up >= threshold
    return enter, size, threshold


# ------------------------------------------------------------
# Backtesting utilities
# ------------------------------------------------------------

@dataclass
class BacktestResult:
    total_return: float
    win_rate: float
    max_drawdown: float
    sharpe: float
    sortino: float
    profit_factor: float
    avg_trade_return: float
    num_trades: int
    equity: pd.Series
    trades: pd.DataFrame


def compute_drawdown(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    return dd


def backtest(
    prices: pd.Series,
    prob_up: pd.Series,
    regime: pd.Series,
    base_threshold: float = 0.55,
    cost_bps: float = 5.0,
    slip_bps: float = 2.0,
    top_k: int = 5,
    sectors: pd.Series | None = None,
    sector_caps: Dict[str, int] | None = None,
) -> BacktestResult:
    """Long-only backtest with costs/slippage, top-K, and optional sector caps."""

    df = pd.concat([
        prices.rename("price"),
        prob_up.rename("prob"),
        regime.rename("regime"),
    ], axis=1).dropna()
    df["date"] = df.index.date

    # Entry decision based on current day's prob/regime, applied to next day's return
    df["enter"], df["size"], df["th_used"] = zip(*df.apply(lambda r: regime_adjusted_decision(r["prob"], r["regime"], base_threshold), axis=1))

    # Top-K filter per day
    df = df.groupby("date", group_keys=False).apply(lambda g: g.nlargest(top_k, "prob"))

    # Optional sector cap
    if sectors is not None:
        df["sector"] = sectors.reindex(df.index)
        if sector_caps:
            def _cap(group):
                capped = []
                for sec, grp in group.groupby("sector"):
                    m = sector_caps.get(sec, len(grp))
                    capped.append(grp.head(m))
                return pd.concat(capped)
            df = df.groupby("date", group_keys=False).apply(_cap)

    df["ret_fwd"] = df["price"].pct_change().shift(-1)  # next-day return
    trade_ret = df["enter"] * df["size"] * df["ret_fwd"]

    # Apply costs and slippage (per trade, entry+exit approximated as one hit)
    cost = (cost_bps + slip_bps) / 10000.0
    trade_ret = trade_ret - df["enter"] * cost
    df["trade_ret"] = trade_ret

    trades = df[df["enter"]].copy()
    num_trades = len(trades)
    wins = trades[trades["trade_ret"] > 0]
    losses = trades[trades["trade_ret"] < 0]

    equity = (1 + df["trade_ret"].fillna(0)).cumprod()
    total_return = equity.iloc[-1] - 1 if not equity.empty else 0.0
    win_rate = len(wins) / num_trades if num_trades else 0.0
    dd = compute_drawdown(equity)
    max_dd = dd.min() if not dd.empty else 0.0

    daily_ret = df["trade_ret"].fillna(0)
    sharpe = (daily_ret.mean() / (daily_ret.std() + 1e-9)) * math.sqrt(252) if not daily_ret.empty else 0.0
    downside = daily_ret[daily_ret < 0]
    sortino = (daily_ret.mean() / (downside.std() + 1e-9)) * math.sqrt(252) if not downside.empty else 0.0

    gross_profit = wins["trade_ret"].sum()
    gross_loss = -losses["trade_ret"].sum()
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0
    avg_trade = trades["trade_ret"].mean() if num_trades else 0.0

    return BacktestResult(
        total_return=total_return,
        win_rate=win_rate,
        max_drawdown=max_dd,
        sharpe=sharpe,
        sortino=sortino,
        profit_factor=profit_factor,
        avg_trade_return=avg_trade,
        num_trades=num_trades,
        equity=equity,
        trades=trades,
    )


def optimize_thresholds(
    prices: pd.Series,
    prob_up: pd.Series,
    regime: pd.Series,
    thresholds: Iterable[float],
    cost_bps: float = 5.0,
    slip_bps: float = 2.0,
    top_k: int = 5,
    sectors: pd.Series | None = None,
    sector_caps: Dict[str, int] | None = None,
) -> pd.DataFrame:
    rows = []
    for th in thresholds:
        res = backtest(
            prices,
            prob_up,
            regime,
            base_threshold=th,
            cost_bps=cost_bps,
            slip_bps=slip_bps,
            top_k=top_k,
            sectors=sectors,
            sector_caps=sector_caps,
        )
        rows.append({
            "threshold": th,
            "profit_factor": res.profit_factor,
            "total_return": res.total_return,
            "sharpe": res.sharpe,
            "max_drawdown": res.max_drawdown,
            "win_rate": res.win_rate,
            "num_trades": res.num_trades,
        })
    return pd.DataFrame(rows).sort_values("profit_factor", ascending=False)


# ------------------------------------------------------------
# Paper trading (simulation) and logging
# ------------------------------------------------------------

def paper_trade(
    prices: pd.Series,
    prob_up: pd.Series,
    regime: pd.Series,
    base_threshold: float = 0.55,
    cash_start: float = 100_000.0,
    log_path: Path = Path("logs/paper_trades.csv"),
    cost_bps: float = 5.0,
    slip_bps: float = 2.0,
    top_k: int = 5,
    sectors: pd.Series | None = None,
    sector_caps: Dict[str, int] | None = None,
) -> pd.DataFrame:
    res = backtest(
        prices,
        prob_up,
        regime,
        base_threshold=base_threshold,
        cost_bps=cost_bps,
        slip_bps=slip_bps,
        top_k=top_k,
        sectors=sectors,
        sector_caps=sector_caps,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    res.trades.to_csv(log_path, index=True)
    return res.trades


# ------------------------------------------------------------
# Performance reporting
# ------------------------------------------------------------

def performance_report(res: BacktestResult) -> Dict[str, float]:
    equity = res.equity
    dd = compute_drawdown(equity)
    monthly = res.trades["trade_ret"].resample("M").sum() if not res.trades.empty else pd.Series(dtype=float)
    best_trade = res.trades["trade_ret"].max() if not res.trades.empty else 0.0
    worst_trade = res.trades["trade_ret"].min() if not res.trades.empty else 0.0

    return {
        "total_return": res.total_return,
        "max_drawdown": res.max_drawdown,
        "sharpe": res.sharpe,
        "sortino": res.sortino,
        "profit_factor": res.profit_factor,
        "win_rate": res.win_rate,
        "num_trades": res.num_trades,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "monthly_returns": monthly.to_dict(),
        "equity_curve_last": float(equity.iloc[-1]) if not equity.empty else 1.0,
        "drawdown_curve_min": float(dd.min()) if not dd.empty else 0.0,
    }


# ------------------------------------------------------------
# Daily auto-update (skeleton)
# ------------------------------------------------------------

def daily_auto_update(symbols: List[str]):
    """
    Skeleton for daily run after market close:
      1) Download latest data for symbols and index
      2) Compute features / run your model to get prob_up
      3) Detect regime from index
      4) Backtest / paper-trade and log
    This is left as a template; plug your model inference where noted.
    """
    index_df = compute_regime(download_index())
    regime_series = index_df["regime"]
    # TODO: integrate your model inference here for each symbol to get prob_up series.
    # Example placeholder (random):
    # prob_up = pd.Series(np.random.rand(len(regime_series)), index=regime_series.index)
    # prices = download_symbol_prices(symbol)
    # res = backtest(prices["Close"], prob_up, regime_series)
    # paper_trade(prices["Close"], prob_up, regime_series)
    return regime_series


# ------------------------------------------------------------
# Example main (demo with random probs) — replace with real model outputs
# ------------------------------------------------------------
if __name__ == "__main__":
    # Demo: run regime detection on NIFTY, generate random probs, and backtest a dummy strategy
    idx = compute_regime(download_index(period="2y"))
    regime = idx["regime"].dropna()
    prices = idx["Close"].loc[regime.index]
    rng = np.random.default_rng(42)
    prob_series = pd.Series(rng.random(len(prices)), index=prices.index)

    thresholds = [0.55, 0.60, 0.65, 0.70]
    opt = optimize_thresholds(prices, prob_series, regime, thresholds)
    best_th = opt.iloc[0]["threshold"] if not opt.empty else 0.6
    res = backtest(prices, prob_series, regime, base_threshold=best_th)

    report = performance_report(res)
    print("Best threshold:", best_th)
    print("Report:", report)
    # Log trades for inspection
    paper_trade(prices, prob_series, regime, base_threshold=best_th, log_path=Path("logs/demo_paper_trades.csv"))
