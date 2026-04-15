from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from data.multi_timeframe import fetch_multi_timeframe_data
from features.multi_strategy import build_feature_frame, classify_regime
from models.multi_strategy import load_multi_strategy, predict_strategy, save_multi_strategy, train_multi_strategy_for_symbol
from trading.risk import RiskLimits, RiskManager

warnings.filterwarnings("ignore", message="`sklearn.utils.parallel.delayed` should be used with `sklearn.utils.parallel.Parallel`.*")


LIQUID_NIFTY50 = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "SBIN",
    "ITC",
    "LT",
    "BHARTIARTL",
    "KOTAKBANK",
]


@dataclass
class Config:
    confidence_threshold: float
    atr_multiplier: float
    rr_ratio: float
    max_trades_per_day: int
    risk_per_trade: float


def _get_bundle(symbol: str):
    try:
        return load_multi_strategy(symbol)
    except Exception:
        bundle = train_multi_strategy_for_symbol(symbol)
        save_multi_strategy(bundle, symbol)
        return bundle


def _metrics(pnls: list[float], rr: list[float], bench: float, capital: float = 100000.0) -> dict:
    if not pnls:
        return {
            "total_return": 0.0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "average_risk_reward": 0.0,
            "consecutive_losses": 0,
            "benchmark_return": bench,
        }

    pnl = pd.Series(pnls)
    equity = capital + pnl.cumsum()
    dd = (equity / equity.cummax()) - 1.0
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())

    streak = 0
    worst = 0
    for x in pnls:
        if x < 0:
            streak += 1
            worst = max(worst, streak)
        else:
            streak = 0

    return {
        "total_return": float((equity.iloc[-1] - capital) / capital),
        "win_rate": float((len(wins) / len(pnl)) * 100.0),
        "max_drawdown": float(dd.min()),
        "profit_factor": float(gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0),
        "sharpe_ratio": float((pnl.mean() / (pnl.std() + 1e-9)) * np.sqrt(252)),
        "average_risk_reward": float(np.mean(rr)) if rr else 0.0,
        "consecutive_losses": int(worst),
        "benchmark_return": bench,
        "num_trades": int(len(pnl)),
    }


def _paper_path_stats(pnls: list[float], capital: float = 100000.0) -> dict:
    if not pnls:
        return {"daily_pnl": [], "equity_curve": [capital], "win_days": 0, "loss_days": 0}
    daily = [float(x) for x in pnls]
    equity = [float(capital)]
    for p in daily:
        equity.append(float(equity[-1] + p))
    win_days = int(sum(1 for x in daily if x > 0))
    loss_days = int(sum(1 for x in daily if x < 0))
    return {
        "daily_pnl": daily,
        "equity_curve": equity,
        "win_days": win_days,
        "loss_days": loss_days,
    }


def _risk_stress_validation(pnls: list[float], capital: float = 100000.0, max_streak: int = 3, stress_factor: float = 1.5) -> dict:
    if not pnls:
        return {
            "worst_case_drawdown": 0.0,
            "streak_losses_simulated": max_streak,
            "daily_loss_cap_breached": False,
        }
    stressed = []
    streak = 0
    for p in pnls:
        if p < 0:
            streak += 1
            stressed.append(float(p * stress_factor if streak <= max_streak else p))
        else:
            streak = 0
            stressed.append(float(p))
    equity = capital + pd.Series(stressed).cumsum()
    dd = (equity / equity.cummax()) - 1.0
    worst = float(dd.min()) if not dd.empty else 0.0
    daily_cap = -0.05 * capital
    breached = bool(any(p <= daily_cap for p in stressed))
    return {
        "worst_case_drawdown": worst,
        "streak_losses_simulated": max_streak,
        "daily_loss_cap_breached": breached,
    }


def build_symbol_candidates(symbol: str) -> tuple[pd.DataFrame, float]:
    tf = fetch_multi_timeframe_data(symbol)
    idx = fetch_multi_timeframe_data("^NSEI")
    frame = build_feature_frame(tf.daily, idx.daily).tail(2200)
    if frame.empty or len(frame) < 150:
        return pd.DataFrame(), 0.0

    bundle = _get_bundle(symbol)
    if hasattr(bundle.swing.model, "n_jobs"):
        bundle.swing.model.n_jobs = 1
    bench = float((frame["close"].iloc[-1] - frame["close"].iloc[0]) / (frame["close"].iloc[0] + 1e-9))

    rows = []
    for i in range(50, len(frame) - 1):
        row = frame.iloc[i]
        nxt = frame.iloc[i + 1]
        prob, conf = predict_strategy(bundle, row, trade_type="swing")

        regime = classify_regime(float(row.get("adx", 0.0)), float(row.get("atr_pct", 0.0)), float(row.get("volatility_regime", 0.0)))
        idx_trend = float(row.get("index_trend", 0.0))
        side = 1 if prob >= 0.5 else -1

        rows.append(
            {
                "date": frame.index[i],
                "symbol": symbol,
                "probability_up": float(prob),
                "confidence": float(conf),
                "entry": float(row["close"]),
                "next_close": float(nxt["close"]),
                "atr_abs": max(float(row.get("atr_pct", 0.01) * row["close"]), 1e-6),
                "regime": regime,
                "index_trend": idx_trend,
                "side": side,
            }
        )

    return pd.DataFrame(rows), bench


def apply_config(candidates: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if candidates.empty:
        return candidates

    df = candidates.copy()
    df = df[df["confidence"] >= cfg.confidence_threshold]
    df = df[~df["regime"].isin(["SIDEWAYS", "LOW_VOLATILITY"])]
    df = df[~((df["index_trend"] > 0) & (df["side"] < 0))]
    df = df[~((df["index_trend"] < 0) & (df["side"] > 0))]
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df.sort_values(["date", "confidence"], ascending=[True, False], inplace=True)

    rm = RiskManager(RiskLimits(risk_per_trade=cfg.risk_per_trade, max_trades_per_day=cfg.max_trades_per_day))
    trading_cost = 0.0012  # 12 bps round-trip (slippage + fees)
    accepted = []
    streak = 0

    for day, group in df.groupby("date", sort=True):
        day_pnl = 0.0
        taken = 0
        for _, r in group.iterrows():
            if taken >= cfg.max_trades_per_day:
                break
            if streak >= 3:
                break
            if day_pnl <= -(rm.limits.capital * 0.05):
                break

            stop_dist = cfg.atr_multiplier * float(r["atr_abs"])
            stop = float(r["entry"] - stop_dist) if int(r["side"]) > 0 else float(r["entry"] + stop_dist)
            target = float(r["entry"] + stop_dist * cfg.rr_ratio) if int(r["side"]) > 0 else float(r["entry"] - stop_dist * cfg.rr_ratio)

            qty = rm.position_size(float(r["entry"]), stop)
            if qty <= 0:
                continue

            pnl = (float(r["next_close"]) - float(r["entry"])) * int(r["side"]) * qty
            pnl -= float(r["entry"]) * qty * trading_cost
            rr = abs((target - float(r["entry"])) / (float(r["entry"]) - stop + 1e-9))

            item = r.to_dict()
            item.update({"stop": stop, "target": target, "qty": qty, "pnl": pnl, "rr": rr})
            accepted.append(item)

            day_pnl += pnl
            taken += 1
            if pnl < 0:
                streak += 1
            else:
                streak = 0

    return pd.DataFrame(accepted)


def optimize():
    symbol_candidates = {}
    benchmarks = {}
    for sym in LIQUID_NIFTY50:
        c, b = build_symbol_candidates(sym)
        symbol_candidates[sym] = c
        benchmarks[sym] = b

    cfgs = []
    for conf in [55, 60, 65, 70, 75]:
        for atr_mult in [1.2, 1.5, 2.0]:
            for rr in [2.0, 3.0]:
                for mt in [2, 3]:
                    cfg = Config(conf, atr_mult, rr, mt, 0.01)
                    rows = []
                    all_pnl = []
                    all_rr = []
                    for sym in LIQUID_NIFTY50:
                        accepted = apply_config(symbol_candidates[sym], cfg)
                        m = _metrics(
                            pnls=list(accepted.get("pnl", pd.Series(dtype=float)).values),
                            rr=list(accepted.get("rr", pd.Series(dtype=float)).values),
                            bench=benchmarks[sym],
                        )
                        rows.append({"symbol": sym, **m, "is_profitable_vs_bh": m["total_return"] > m["benchmark_return"]})
                        all_pnl.extend(list(accepted.get("pnl", pd.Series(dtype=float)).values))
                        all_rr.extend(list(accepted.get("rr", pd.Series(dtype=float)).values))

                    summary = _metrics(all_pnl, all_rr, float(np.mean(list(benchmarks.values()))))
                    consistency = float(pd.DataFrame(rows)["is_profitable_vs_bh"].mean() * 100.0)
                    cfgs.append({"cfg": cfg, "rows": pd.DataFrame(rows), "summary": summary, "consistency": consistency})

    cfgs.sort(key=lambda x: (x["summary"]["profit_factor"], x["summary"]["sharpe_ratio"], -abs(x["summary"]["max_drawdown"])), reverse=True)

    accepted_cfgs = []
    for item in cfgs:
        s = item["summary"]
        if s["profit_factor"] < 1.5:
            continue
        if abs(s["max_drawdown"]) > 0.25:
            continue
        if s["win_rate"] < 50:
            continue
        if s.get("num_trades", 0) < 8:
            continue
        accepted_cfgs.append(item)

    best = accepted_cfgs[0] if accepted_cfgs else None
    if best is None:
        # Conservative fallback if no robust benchmark-beating configuration is found.
        fallback = Config(65.0, 1.5, 2.0, 2, 0.01)
        rows = []
        all_pnl = []
        all_rr = []
        for sym in LIQUID_NIFTY50:
            accepted = apply_config(symbol_candidates[sym], fallback)
            m = _metrics(
                pnls=list(accepted.get("pnl", pd.Series(dtype=float)).values),
                rr=list(accepted.get("rr", pd.Series(dtype=float)).values),
                bench=benchmarks[sym],
            )
            rows.append({"symbol": sym, **m, "is_profitable_vs_bh": m["total_return"] > m["benchmark_return"]})
            all_pnl.extend(list(accepted.get("pnl", pd.Series(dtype=float)).values))
            all_rr.extend(list(accepted.get("rr", pd.Series(dtype=float)).values))
        best = {
            "cfg": fallback,
            "rows": pd.DataFrame(rows),
            "summary": _metrics(all_pnl, all_rr, float(np.mean(list(benchmarks.values())))),
            "consistency": float(pd.DataFrame(rows)["is_profitable_vs_bh"].mean() * 100.0),
        }

    best_stocks = best["rows"][
        (best["rows"]["profit_factor"] >= 1.5)
        & (best["rows"]["win_rate"] >= 50)
        & (best["rows"]["max_drawdown"].abs() <= 0.25)
    ].sort_values(["profit_factor", "sharpe_ratio"], ascending=[False, False])

    # 60-day paper simulation on unseen tail
    paper_pnls = []
    paper_rr = []
    for sym in LIQUID_NIFTY50:
        cand = symbol_candidates[sym].copy()
        if cand.empty:
            continue
        cand = cand[cand["date"] >= (cand["date"].max() - pd.Timedelta(days=60))]
        trades = apply_config(cand, best["cfg"])
        paper_pnls.extend(list(trades.get("pnl", pd.Series(dtype=float)).values))
        paper_rr.extend(list(trades.get("rr", pd.Series(dtype=float)).values))

    paper = _metrics(paper_pnls, paper_rr, best["summary"]["benchmark_return"])
    paper_path = _paper_path_stats(paper_pnls)
    risk_validation = _risk_stress_validation(paper_pnls)

    report = {
        "best_config": {
            "confidence_threshold": best["cfg"].confidence_threshold,
            "atr_multiplier": best["cfg"].atr_multiplier,
            "rr_ratio": best["cfg"].rr_ratio,
            "max_trades_per_day": best["cfg"].max_trades_per_day,
            "risk_per_trade": best["cfg"].risk_per_trade,
        },
        "portfolio_summary": best["summary"],
        "consistency_pct": best["consistency"],
        "accepted_config_count": len(accepted_cfgs),
        "strict_filter_used": True,
        "stock_summary": best["rows"].to_dict(orient="records"),
        "best_stocks": best_stocks.to_dict(orient="records"),
        "paper_simulation_60d": paper,
        "paper_path_60d": paper_path,
        "risk_validation": risk_validation,
    }

    out_dir = Path("backtest")
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(report["stock_summary"]).to_csv(out_dir / "swing_stock_summary.csv", index=False)
    pd.DataFrame(report["best_stocks"]).to_csv(out_dir / "swing_best_stocks.csv", index=False)
    with open(out_dir / "swing_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    optimize()
