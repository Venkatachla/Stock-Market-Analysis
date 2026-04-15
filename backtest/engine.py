from dataclasses import dataclass

import numpy as np
import pandas as pd


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    return float(dd.min())


@dataclass
class BacktestSummary:
    total_return: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    benchmark_return: float


def backtest_with_benchmark(prices: pd.Series, signal: pd.Series, transaction_cost_bps: float = 5.0) -> BacktestSummary:
    frame = pd.DataFrame({"price": prices, "signal": signal}).dropna()
    if len(frame) < 3:
        return BacktestSummary(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    daily_ret = frame["price"].pct_change().fillna(0.0)
    shifted_pos = frame["signal"].shift(1).fillna(0.0)

    costs = (shifted_pos.diff().abs().fillna(0.0) * (transaction_cost_bps / 10000.0)).clip(lower=0.0)
    strategy_ret = (shifted_pos * daily_ret) - costs

    equity = (1.0 + strategy_ret).cumprod()
    total_return = float(equity.iloc[-1] - 1.0)

    trades = strategy_ret[shifted_pos != 0]
    wins = trades[trades > 0]
    losses = trades[trades < 0]
    win_rate = float((len(wins) / len(trades)) * 100.0) if len(trades) else 0.0

    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

    sharpe = 0.0
    if strategy_ret.std() > 0:
        sharpe = float((strategy_ret.mean() / strategy_ret.std()) * np.sqrt(252))

    benchmark_equity = (1.0 + daily_ret).cumprod()
    benchmark_return = float(benchmark_equity.iloc[-1] - 1.0)

    return BacktestSummary(
        total_return=total_return,
        win_rate=win_rate,
        max_drawdown=_max_drawdown(equity),
        sharpe_ratio=sharpe,
        profit_factor=float(profit_factor),
        benchmark_return=benchmark_return,
    )
