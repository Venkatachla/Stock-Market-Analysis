from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ProfessionalBacktestResult:
    win_rate: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    average_rr: float
    consecutive_losses: int


def run_professional_backtest(trades: pd.DataFrame, capital_start: float = 100000.0) -> ProfessionalBacktestResult:
    if trades.empty:
        return ProfessionalBacktestResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    df = trades.copy()
    for col in ["entry_price", "exit_price", "stop_loss", "target", "position_size"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["pnl"] = (df["exit_price"] - df["entry_price"]) * df["position_size"]
    df["risk_amount"] = (df["entry_price"] - df["stop_loss"]).abs() * df["position_size"]
    df["reward_amount"] = (df["target"] - df["entry_price"]).abs() * df["position_size"]
    df["rr"] = df["reward_amount"] / (df["risk_amount"] + 1e-9)

    equity = capital_start + df["pnl"].cumsum()
    total_return = float((equity.iloc[-1] - capital_start) / capital_start)

    peak = equity.cummax()
    max_dd = float(((equity / peak) - 1.0).min())

    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] < 0]
    win_rate = float((len(wins) / len(df)) * 100.0) if len(df) else 0.0

    gross_profit = float(wins["pnl"].sum())
    gross_loss = float(-losses["pnl"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

    pnl_series = df["pnl"] / capital_start
    sharpe = float((pnl_series.mean() / (pnl_series.std() + 1e-9)) * np.sqrt(252)) if len(df) > 1 else 0.0

    avg_rr = float(df["rr"].replace([np.inf, -np.inf], np.nan).dropna().mean()) if len(df) else 0.0

    worst_streak = 0
    streak = 0
    for x in df["pnl"]:
        if x < 0:
            streak += 1
            worst_streak = max(worst_streak, streak)
        else:
            streak = 0

    return ProfessionalBacktestResult(
        win_rate=win_rate,
        total_return=total_return,
        max_drawdown=max_dd,
        sharpe_ratio=sharpe,
        profit_factor=float(profit_factor),
        average_rr=avg_rr,
        consecutive_losses=int(worst_streak),
    )
