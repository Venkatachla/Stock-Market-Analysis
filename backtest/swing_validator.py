from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from data.multi_timeframe import fetch_multi_timeframe_data
from features.multi_strategy import build_feature_frame, classify_regime
from models.multi_strategy import load_multi_strategy, predict_strategy, save_multi_strategy, train_multi_strategy_for_symbol
from trading.risk import RiskLimits, RiskManager


LIQUID_NIFTY50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "LT", "ITC", "AXISBANK", "KOTAKBANK",
]


@dataclass
class Config:
    confidence_threshold: float
    atr_multiplier: float
    rr_ratio: float
    max_trades_per_day: int
    risk_per_trade: float


@dataclass
class Metrics:
    total_return: float
    win_rate: float
    max_drawdown: float
    profit_factor: float
    sharpe_ratio: float
    average_risk_reward: float
    consecutive_losses: int
    benchmark_return: float


def _get_bundle(symbol: str):
    try:
        return load_multi_strategy(symbol)
    except Exception:
        bundle = train_multi_strategy_for_symbol(symbol)
        save_multi_strategy(bundle, symbol)
        return bundle


def _equity_metrics(pnls: list[float], risk_rewards: list[float], benchmark_return: float, capital_start: float = 100000.0) -> Metrics:
    if not pnls:
        return Metrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, benchmark_return)

    pnl_ser = pd.Series(pnls)
    equity = capital_start + pnl_ser.cumsum()
    total_return = float((equity.iloc[-1] - capital_start) / capital_start)

    dd = (equity / equity.cummax()) - 1.0
    max_dd = float(dd.min())

    wins = pnl_ser[pnl_ser > 0]
    losses = pnl_ser[pnl_ser < 0]
    win_rate = float((len(wins) / len(pnl_ser)) * 100.0)

    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

    rets = pnl_ser / capital_start
    sharpe = float((rets.mean() / (rets.std() + 1e-9)) * np.sqrt(252)) if len(rets) > 1 else 0.0

    avg_rr = float(np.mean(risk_rewards)) if risk_rewards else 0.0

    streak = 0
    worst = 0
    for p in pnls:
        if p < 0:
            streak += 1
            worst = max(worst, streak)
        else:
            streak = 0

    return Metrics(
        total_return=total_return,
        win_rate=win_rate,
        max_drawdown=max_dd,
        profit_factor=float(profit_factor),
        sharpe_ratio=sharpe,
        average_risk_reward=avg_rr,
        consecutive_losses=worst,
        benchmark_return=benchmark_return,
    )


def _build_signals_for_symbol(symbol: str, cfg: Config, lookback_days: int = 2520) -> tuple[pd.DataFrame, float]:
    tf = fetch_multi_timeframe_data(symbol)
    idx = fetch_multi_timeframe_data("^NSEI")
    frame = build_feature_frame(tf.daily, idx.daily)
    if frame.empty:
        return pd.DataFrame(), 0.0

    frame = frame.tail(lookback_days).copy()
    if len(frame) < 120:
        return pd.DataFrame(), 0.0

    bundle = _get_bundle(symbol)

    benchmark = 0.0
    if len(frame) > 1:
        benchmark = float((frame["close"].iloc[-1] - frame["close"].iloc[0]) / (frame["close"].iloc[0] + 1e-9))

    rows = []
    for i in range(50, len(frame) - 1):
        row = frame.iloc[i]
        nxt = frame.iloc[i + 1]

        prob, conf = predict_strategy(bundle, row, trade_type="swing")
        if conf < cfg.confidence_threshold:
            continue

        adx = float(row.get("adx", 0.0))
        atr_pct = float(row.get("atr_pct", 0.0))
        vol_reg = float(row.get("volatility_regime", 0.0))
        regime = classify_regime(adx=adx, atr_pct=atr_pct, vol_regime=vol_reg)

        if regime in {"SIDEWAYS", "LOW_VOLATILITY"}:
            continue

        idx_trend = float(row.get("index_trend", 0.0))
        side = 1 if prob >= 0.5 else -1
        if idx_trend > 0 and side < 0:
            continue
        if idx_trend < 0 and side > 0:
            continue

        entry = float(row["close"])
        exit_price = float(nxt["close"])

        atr_abs = max(float(atr_pct * entry), 1e-6)
        stop_dist = cfg.atr_multiplier * atr_abs
        stop = entry - stop_dist if side > 0 else entry + stop_dist
        target = entry + (stop_dist * cfg.rr_ratio) if side > 0 else entry - (stop_dist * cfg.rr_ratio)

        rm = RiskManager(RiskLimits(risk_per_trade=cfg.risk_per_trade, max_trades_per_day=cfg.max_trades_per_day))
        qty = rm.position_size(entry_price=entry, stop_loss=stop)
        if qty <= 0:
            continue

        pnl = (exit_price - entry) * side * qty
        rr = abs((target - entry) / (entry - stop + 1e-9))

        rows.append(
            {
                "date": frame.index[i],
                "symbol": symbol,
                "probability_up": float(prob),
                "confidence": float(conf),
                "entry_price": entry,
                "exit_price": exit_price,
                "stop_loss": stop,
                "target": target,
                "position_size": qty,
                "pnl": pnl,
                "risk_reward": rr,
                "regime": regime,
            }
        )

    return pd.DataFrame(rows), benchmark


def _apply_portfolio_risk_rules(trades: pd.DataFrame, cfg: Config, capital: float = 100000.0) -> pd.DataFrame:
    if trades.empty:
        return trades

    data = trades.copy()
    data["date"] = pd.to_datetime(data["date"]).dt.date
    data.sort_values(["date", "confidence"], ascending=[True, False], inplace=True)

    accepted = []
    day_pnl = 0.0
    streak = 0
    _current_day = None

    for day, day_df in data.groupby("date", sort=True):
        _current_day = day
        day_pnl = 0.0
        taken = 0

        for _, row in day_df.iterrows():
            if taken >= cfg.max_trades_per_day:
                break
            if streak >= 3:
                break
            if day_pnl <= -(capital * 0.05):
                break

            accepted.append(row.to_dict())
            taken += 1
            p = float(row["pnl"])
            day_pnl += p
            if p < 0:
                streak += 1
            else:
                streak = 0

    return pd.DataFrame(accepted)


def evaluate_configuration(symbols: Iterable[str], cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    per_stock_rows = []
    all_trades = []
    bench_returns = []

    for sym in symbols:
        raw_trades, bench = _build_signals_for_symbol(sym, cfg)
        filtered = _apply_portfolio_risk_rules(raw_trades, cfg)
        bench_returns.append(bench)

        metrics = _equity_metrics(
            pnls=list(filtered.get("pnl", pd.Series(dtype=float)).astype(float).values),
            risk_rewards=list(filtered.get("risk_reward", pd.Series(dtype=float)).astype(float).values),
            benchmark_return=bench,
        )

        per_stock_rows.append(
            {
                "symbol": sym,
                "total_return": metrics.total_return,
                "win_rate": metrics.win_rate,
                "max_drawdown": metrics.max_drawdown,
                "profit_factor": metrics.profit_factor,
                "sharpe_ratio": metrics.sharpe_ratio,
                "average_risk_reward": metrics.average_risk_reward,
                "consecutive_losses": metrics.consecutive_losses,
                "benchmark_return": metrics.benchmark_return,
                "is_profitable_vs_bh": metrics.total_return > metrics.benchmark_return,
            }
        )

        if not filtered.empty:
            all_trades.append(filtered)

    stock_df = pd.DataFrame(per_stock_rows)
    trades_df = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()

    portfolio_metrics = _equity_metrics(
        pnls=list(trades_df.get("pnl", pd.Series(dtype=float)).astype(float).values),
        risk_rewards=list(trades_df.get("risk_reward", pd.Series(dtype=float)).astype(float).values),
        benchmark_return=float(np.mean(bench_returns) if bench_returns else 0.0),
    )

    summary = {
        "total_return": portfolio_metrics.total_return,
        "win_rate": portfolio_metrics.win_rate,
        "max_drawdown": portfolio_metrics.max_drawdown,
        "profit_factor": portfolio_metrics.profit_factor,
        "sharpe_ratio": portfolio_metrics.sharpe_ratio,
        "average_risk_reward": portfolio_metrics.average_risk_reward,
        "consecutive_losses": portfolio_metrics.consecutive_losses,
        "benchmark_return": portfolio_metrics.benchmark_return,
    }

    return stock_df, trades_df, summary


def optimize_and_validate(symbols: Iterable[str] = LIQUID_NIFTY50) -> dict:
    configs = []

    for conf in [55, 60, 65, 70, 75]:
        for atr_mult in [1.2, 1.5, 1.8, 2.0]:
            for rr in [2.0, 3.0]:
                for max_trades in [2, 3]:
                    cfg = Config(
                        confidence_threshold=float(conf),
                        atr_multiplier=float(atr_mult),
                        rr_ratio=float(rr),
                        max_trades_per_day=int(max_trades),
                        risk_per_trade=0.01,
                    )
                    stock_df, trades_df, summary = evaluate_configuration(symbols, cfg)
                    consistency = float((stock_df["is_profitable_vs_bh"].mean() * 100.0) if not stock_df.empty else 0.0)
                    configs.append(
                        {
                            "config": cfg,
                            "stock_df": stock_df,
                            "trades_df": trades_df,
                            "summary": summary,
                            "consistency": consistency,
                        }
                    )

    def _score(item: dict) -> tuple[float, float, float]:
        s = item["summary"]
        return (
            float(s["profit_factor"]),
            float(item["consistency"]),
            float(-abs(s["max_drawdown"])),
        )

    configs_sorted = sorted(configs, key=_score, reverse=True)

    accepted = []
    for item in configs_sorted:
        s = item["summary"]
        if s["profit_factor"] < 1.5:
            continue
        if abs(float(s["max_drawdown"])) > 0.25:
            continue
        if float(s["win_rate"]) < 50.0:
            continue
        accepted.append(item)

    best = accepted[0] if accepted else configs_sorted[0]

    best_cfg = best["config"]
    best_stock_df = best["stock_df"].copy()

    passed_stocks = best_stock_df[
        (best_stock_df["profit_factor"] >= 1.5)
        & (best_stock_df["win_rate"] >= 50.0)
        & (best_stock_df["max_drawdown"].abs() <= 0.25)
    ].sort_values(["profit_factor", "sharpe_ratio"], ascending=[False, False])

    recent_trades = best["trades_df"].copy()
    if not recent_trades.empty:
        recent_trades["date"] = pd.to_datetime(recent_trades["date"])
        cutoff = recent_trades["date"].max() - pd.Timedelta(days=60)
        recent_trades = recent_trades[recent_trades["date"] >= cutoff].copy()

    paper_metrics = _equity_metrics(
        pnls=list(recent_trades.get("pnl", pd.Series(dtype=float)).astype(float).values),
        risk_rewards=list(recent_trades.get("risk_reward", pd.Series(dtype=float)).astype(float).values),
        benchmark_return=float(best["summary"]["benchmark_return"]),
    )

    out = {
        "best_config": {
            "confidence_threshold": best_cfg.confidence_threshold,
            "atr_multiplier": best_cfg.atr_multiplier,
            "rr_ratio": best_cfg.rr_ratio,
            "max_trades_per_day": best_cfg.max_trades_per_day,
            "risk_per_trade": best_cfg.risk_per_trade,
        },
        "portfolio_summary": best["summary"],
        "consistency_pct": best["consistency"],
        "accepted_config_count": len(accepted),
        "best_stocks": passed_stocks.to_dict(orient="records"),
        "stock_summary": best_stock_df.to_dict(orient="records"),
        "paper_simulation_60d": {
            "total_return": paper_metrics.total_return,
            "win_rate": paper_metrics.win_rate,
            "max_drawdown": paper_metrics.max_drawdown,
            "profit_factor": paper_metrics.profit_factor,
            "sharpe_ratio": paper_metrics.sharpe_ratio,
            "average_risk_reward": paper_metrics.average_risk_reward,
            "consecutive_losses": paper_metrics.consecutive_losses,
        },
    }

    out_dir = Path("backtest")
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(out["stock_summary"]).to_csv(out_dir / "swing_stock_summary.csv", index=False)
    pd.DataFrame(out["best_stocks"]).to_csv(out_dir / "swing_best_stocks.csv", index=False)
    with open(out_dir / "swing_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    return out


if __name__ == "__main__":
    report = optimize_and_validate()
    print(json.dumps(report, indent=2))
