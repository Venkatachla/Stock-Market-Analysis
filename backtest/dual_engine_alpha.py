from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from data.multi_timeframe import align_daily_trend_to_intraday, fetch_multi_timeframe_data
from features.multi_strategy import build_feature_frame, classify_regime
from models.multi_strategy import load_multi_strategy, predict_strategy


warnings.filterwarnings(
    "ignore",
    message="`sklearn.utils.parallel.delayed` should be used with `sklearn.utils.parallel.Parallel`.*",
)


LIQUID_NIFTY_ALPHA = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "ITC", "LT", "BHARTIARTL", "KOTAKBANK",
    "AXISBANK", "MARUTI", "SUNPHARMA", "NTPC", "HINDUNILVR", "ULTRACEMCO", "BAJFINANCE", "BAJAJFINSV",
    "TITAN", "WIPRO",
]


BUNDLE_CACHE: dict[str, object | None] = {}
ALPHA_USE_ML_MODEL = False


@dataclass
class AlphaConfig:
    confidence_threshold: float
    atr_multiplier: float
    rr_ratio: float
    max_trades_per_day: int


def _get_bundle(symbol: str):
    if symbol in BUNDLE_CACHE:
        return BUNDLE_CACHE[symbol]
    try:
        bundle = load_multi_strategy(symbol)
        for art_name in ["swing", "intraday", "options_directional", "volatility"]:
            art = getattr(bundle, art_name, None)
            if art is not None and hasattr(art.model, "n_jobs"):
                art.model.n_jobs = 1
        BUNDLE_CACHE[symbol] = bundle
        return bundle
    except Exception:
        BUNDLE_CACHE[symbol] = None
        return None


def _calc_metrics(trades: pd.DataFrame, benchmark_return: float, capital: float = 30000.0) -> dict:
    if trades.empty:
        return {
            "total_return": 0.0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "average_risk_reward": 0.0,
            "consecutive_losses": 0,
            "benchmark_return": benchmark_return,
            "num_trades": 0,
        }

    pnl = pd.to_numeric(trades["pnl"], errors="coerce").fillna(0.0)
    rr = pd.to_numeric(trades["rr"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()

    equity = capital + pnl.cumsum()
    dd = (equity / equity.cummax()) - 1.0

    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())

    streak = 0
    worst = 0
    for x in pnl.values:
        if x < 0:
            streak += 1
            worst = max(worst, streak)
        else:
            streak = 0

    return {
        "total_return": float((equity.iloc[-1] - capital) / capital),
        "win_rate": float((len(wins) / len(pnl)) * 100.0),
        "max_drawdown": float(dd.min()) if len(dd) else 0.0,
        "profit_factor": float(gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0),
        "sharpe_ratio": float((pnl.mean() / (pnl.std() + 1e-9)) * np.sqrt(252)),
        "average_risk_reward": float(rr.mean()) if not rr.empty else 0.0,
        "consecutive_losses": int(worst),
        "benchmark_return": float(benchmark_return),
        "num_trades": int(len(pnl)),
    }


def _simulate_trend_ride(
    future_close: pd.Series,
    future_high: pd.Series,
    future_low: pd.Series,
    entry: float,
    side: int,
    stop: float,
    target: float,
    atr_abs: float,
) -> tuple[float, float]:
    """Partial at 1R, trail remainder, let winners run toward 3R+ equivalent."""
    if future_close.empty:
        return 0.0, 0.0

    risk = abs(entry - stop)
    if risk <= 1e-9:
        return 0.0, 0.0

    one_r = entry + (risk * side)
    three_r = entry + (3.0 * risk * side)

    half_booked = False
    pnl_r = 0.0
    trail_stop = stop

    for i in range(len(future_close)):
        hi = float(future_high.iloc[i])
        lo = float(future_low.iloc[i])
        px = float(future_close.iloc[i])

        if side > 0:
            if lo <= trail_stop:
                if half_booked:
                    pnl_r += ((trail_stop - entry) / risk) * 0.5
                else:
                    pnl_r += -1.0
                return pnl_r, 2.0
            if (not half_booked) and hi >= one_r:
                pnl_r += 0.5
                half_booked = True
                trail_stop = max(trail_stop, px - atr_abs)
            if half_booked:
                trail_stop = max(trail_stop, px - atr_abs)
            if hi >= three_r:
                pnl_r += 1.5
                return pnl_r, 3.0
        else:
            if hi >= trail_stop:
                if half_booked:
                    pnl_r += ((entry - trail_stop) / risk) * 0.5
                else:
                    pnl_r += -1.0
                return pnl_r, 2.0
            if (not half_booked) and lo <= one_r:
                pnl_r += 0.5
                half_booked = True
                trail_stop = min(trail_stop, px + atr_abs)
            if half_booked:
                trail_stop = min(trail_stop, px + atr_abs)
            if lo <= three_r:
                pnl_r += 1.5
                return pnl_r, 3.0

    final_px = float(future_close.iloc[-1])
    if not half_booked:
        pnl_r += ((final_px - entry) * side) / risk
        return pnl_r, abs(pnl_r)

    pnl_r += (((final_px - entry) * side) / risk) * 0.5
    return pnl_r, max(1.0, abs(pnl_r))


def _breakout_candidates(symbol: str, interval: str, tf, idx) -> tuple[pd.DataFrame, float]:

    if interval == "5m":
        raw = align_daily_trend_to_intraday(tf.daily, tf.m5)
        idx_raw = idx.m5 if not idx.m5.empty else idx.daily
    else:
        raw = align_daily_trend_to_intraday(tf.daily, tf.m15)
        idx_raw = idx.m15 if not idx.m15.empty else idx.daily

    frame = build_feature_frame(raw, idx_raw)
    if frame.empty or len(frame) < 120:
        return pd.DataFrame(), 0.0

    bundle = _get_bundle(symbol) if ALPHA_USE_ML_MODEL else None

    benchmark = float((frame["close"].iloc[-1] - frame["close"].iloc[0]) / (frame["close"].iloc[0] + 1e-9))
    rows = []

    for i in range(80, len(frame) - 12):
        row = frame.iloc[i]
        if ALPHA_USE_ML_MODEL and bundle is not None:
            prob, model_conf = predict_strategy(bundle, row, trade_type="intraday")
        else:
            # Fast fallback if symbol-specific model is unavailable.
            raw_mom = float(row.get("ret_1", 0.0))
            prob = float(np.clip(0.5 + np.tanh(raw_mom * 30.0) * 0.2, 0.0, 1.0))
            model_conf = float(min(100.0, max(0.0, abs(prob - 0.5) * 200.0)))

        close = float(row["close"])
        prev_window = frame.iloc[max(0, i - 20):i]
        range_hi = float(prev_window["close"].max()) if not prev_window.empty else close
        range_lo = float(prev_window["close"].min()) if not prev_window.empty else close

        breakout_up = 1.0 if close > range_hi else 0.0
        breakout_dn = 1.0 if close < range_lo else 0.0
        volume_spike = float(row.get("volume_spike", 0.0))
        atr_pct = float(row.get("atr_pct", 0.0))
        atr_expand = 1.0 if atr_pct > float(frame["atr_pct"].rolling(50).median().iloc[i]) else 0.0
        mom = float(row.get("ret_1", 0.0))

        conf_rule = (
            35.0 * max(breakout_up, breakout_dn)
            + 25.0 * min(2.0, max(volume_spike, 0.0)) / 2.0
            + 20.0 * atr_expand
            + 20.0 * min(1.0, abs(mom) * 200.0)
        )
        confidence = float(min(100.0, max(0.0, 0.45 * model_conf + 0.55 * conf_rule)))

        side = 1 if (prob >= 0.5 and breakout_up > 0) else -1 if (prob < 0.5 and breakout_dn > 0) else 0
        if side == 0:
            continue

        regime = classify_regime(float(row.get("adx", 0.0)), atr_pct, float(row.get("volatility_regime", 0.0)))
        idx_trend = float(row.get("daily_trend", 0.0))

        rows.append(
            {
                "timestamp": frame.index[i],
                "symbol": symbol,
                "interval": interval,
                "entry": close,
                "atr_abs": max(1e-6, atr_pct * close),
                "probability_up": float(prob),
                "confidence": confidence,
                "side": int(side),
                "regime": regime,
                "idx_trend": idx_trend,
                "breakout_strength": float(max(breakout_up, breakout_dn)),
                "volume_spike": float(volume_spike),
                "atr_expand": float(atr_expand),
                "momentum_abs": float(abs(mom)),
                "future_close": frame["close"].iloc[i + 1:i + 13].values.tolist(),
                "future_high": raw["High"].reindex(frame.index).iloc[i + 1:i + 13].ffill().values.tolist(),
                "future_low": raw["Low"].reindex(frame.index).iloc[i + 1:i + 13].ffill().values.tolist(),
                "put_call_ratio": float(row.get("put_call_ratio", 1.0)),
                "open_interest_change": float(row.get("open_interest_change", 0.0)),
                "iv_percentile": float(row.get("iv_percentile", 0.5)),
            }
        )

    return pd.DataFrame(rows), benchmark


def _apply_alpha_config(cands: pd.DataFrame, cfg: AlphaConfig) -> pd.DataFrame:
    if cands.empty:
        return cands

    df = cands.copy()
    df = df[df["confidence"] >= cfg.confidence_threshold]
    df = df[df["breakout_strength"] > 0]
    df = df[df["volume_spike"] >= 1.15]
    df = df[df["atr_expand"] >= 1.0]
    df = df[~df["regime"].isin(["SIDEWAYS", "LOW_VOLATILITY"])]
    df = df[~((df["idx_trend"] > 0) & (df["side"] < 0))]
    df = df[~((df["idx_trend"] < 0) & (df["side"] > 0))]
    if df.empty:
        return df

    df["day"] = pd.to_datetime(df["timestamp"]).dt.date
    df.sort_values(["day", "confidence"], ascending=[True, False], inplace=True)

    out = []
    tc = 0.0015

    for day, g in df.groupby("day", sort=True):
        top = g.head(cfg.max_trades_per_day)
        for _, r in top.iterrows():
            entry = float(r["entry"])
            atr_abs = cfg.atr_multiplier * float(r["atr_abs"])
            side = int(r["side"])

            stop = entry - atr_abs if side > 0 else entry + atr_abs
            target = entry + (cfg.rr_ratio * atr_abs) if side > 0 else entry - (cfg.rr_ratio * atr_abs)

            f_close = pd.Series(r["future_close"], dtype=float)
            f_high = pd.Series(r["future_high"], dtype=float)
            f_low = pd.Series(r["future_low"], dtype=float)

            pnl_r, rr = _simulate_trend_ride(
                future_close=f_close,
                future_high=f_high,
                future_low=f_low,
                entry=entry,
                side=side,
                stop=stop,
                target=target,
                atr_abs=float(r["atr_abs"]),
            )

            risk_amt = 30000.0 * 0.01
            pnl = (pnl_r * risk_amt) - (entry * tc)

            # Basic ATM option simulation on strongest signals via delta approximation.
            options_pnl = 0.0
            if float(r["confidence"]) >= 70.0:
                next_px = float(f_close.iloc[-1]) if not f_close.empty else entry
                under_ret = ((next_px - entry) / (entry + 1e-9)) * side
                delta = 0.5
                option_notional = 20000.0 * 0.2
                options_pnl = option_notional * delta * under_ret * 3.0

            row = r.to_dict()
            row.update(
                {
                    "stop": stop,
                    "target": target,
                    "rr": rr,
                    "pnl": pnl,
                    "options_pnl": options_pnl,
                }
            )
            out.append(row)

    return pd.DataFrame(out)


def _latest_scan_rank(cands_5: pd.DataFrame, cands_15: pd.DataFrame, top_n: int = 30) -> list[dict]:
    merged = pd.concat([cands_5, cands_15], ignore_index=True)
    if merged.empty:
        return []
    latest_ts = pd.to_datetime(merged["timestamp"]).max()
    snap_base = merged[pd.to_datetime(merged["timestamp"]) >= (latest_ts - pd.Timedelta(hours=1))]
    snap = snap_base[~snap_base["regime"].isin(["SIDEWAYS", "LOW_VOLATILITY"])]
    snap = snap[snap["confidence"] >= 45.0]
    if snap.empty:
        snap = snap_base.sort_values("confidence", ascending=False).head(top_n)
    else:
        snap = snap.sort_values("confidence", ascending=False).head(top_n)
    snap = snap.copy()
    snap["timestamp"] = pd.to_datetime(snap["timestamp"]).astype(str)
    cols = ["timestamp", "symbol", "interval", "confidence", "probability_up", "side", "regime"]
    return snap[cols].to_dict(orient="records")


def run_alpha_engine() -> dict:
    candidates_5 = {}
    candidates_15 = {}
    benchmarks = {}

    idx = fetch_multi_timeframe_data("^NSEI")

    for sym in LIQUID_NIFTY_ALPHA:
        tf = fetch_multi_timeframe_data(sym)
        c5, b5 = _breakout_candidates(sym, "5m", tf, idx)
        c15, b15 = _breakout_candidates(sym, "15m", tf, idx)
        candidates_5[sym] = c5
        candidates_15[sym] = c15
        benchmarks[sym] = float(np.mean([b5, b15])) if (b5 or b15) else 0.0

    grid: list[dict] = []
    for conf in [45, 50, 55]:
        for atr in [1.0, 1.5, 2.0]:
            for rr in [2.0, 3.0]:
                for mt in [10, 20, 30]:
                    cfg = AlphaConfig(confidence_threshold=conf, atr_multiplier=atr, rr_ratio=rr, max_trades_per_day=mt)
                    rows = []
                    for sym in LIQUID_NIFTY_ALPHA:
                        merged = pd.concat([candidates_5[sym], candidates_15[sym]], ignore_index=True)
                        tr = _apply_alpha_config(merged, cfg)
                        if not tr.empty:
                            rows.append(tr)
                    all_trades = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

                    m = _calc_metrics(all_trades, benchmark_return=float(np.mean(list(benchmarks.values()))) if benchmarks else 0.0)
                    score = (m["total_return"] * 100.0) + (0.2 * m["profit_factor"]) - (0.5 * abs(m["max_drawdown"]))
                    grid.append({"cfg": cfg, "trades": all_trades, "metrics": m, "score": score})

    grid.sort(key=lambda x: (x["metrics"]["total_return"], x["metrics"]["profit_factor"], -abs(x["metrics"]["max_drawdown"])), reverse=True)

    valid = [
        g for g in grid
        if g["metrics"]["profit_factor"] > 1.5 and g["metrics"]["win_rate"] >= 55.0 and g["metrics"]["num_trades"] >= 50
    ]

    best = valid[0] if valid else grid[0]

    trades = best["trades"].copy()
    intraday_metrics = best["metrics"]
    option_metrics = _calc_metrics(
        pd.DataFrame({"pnl": trades.get("options_pnl", pd.Series(dtype=float)), "rr": np.full(len(trades), 2.0)}),
        benchmark_return=0.0,
        capital=20000.0,
    ) if not trades.empty else _calc_metrics(pd.DataFrame(), benchmark_return=0.0, capital=20000.0)

    top_opportunities = _latest_scan_rank(
        pd.concat(list(candidates_5.values()), ignore_index=True) if candidates_5 else pd.DataFrame(),
        pd.concat(list(candidates_15.values()), ignore_index=True) if candidates_15 else pd.DataFrame(),
        top_n=30,
    )

    swing_report_path = Path("backtest/swing_validation_report.json")
    swing_return = 0.0
    swing_win_rate = 0.0
    swing_drawdown = 0.0
    if swing_report_path.exists():
        with open(swing_report_path, "r", encoding="utf-8") as f:
            srep = json.load(f)
        ps = srep.get("portfolio_summary", {})
        swing_return = float(ps.get("total_return", 0.0))
        swing_win_rate = float(ps.get("win_rate", 0.0))
        swing_drawdown = float(ps.get("max_drawdown", 0.0))

    combined = {
        "capital_allocation": {
            "swing_low_risk": 0.50,
            "intraday_alpha": 0.30,
            "high_risk_alpha": 0.20,
        },
        "returns": {
            "swing_return": swing_return,
            "intraday_return": float(intraday_metrics.get("total_return", 0.0)),
            "high_risk_alpha_return": float(option_metrics.get("total_return", 0.0)),
            "combined_portfolio_return": float(
                0.50 * swing_return
                + 0.30 * float(intraday_metrics.get("total_return", 0.0))
                + 0.20 * float(option_metrics.get("total_return", 0.0))
            ),
        },
        "risk": {
            "swing_drawdown": swing_drawdown,
            "intraday_drawdown": float(intraday_metrics.get("max_drawdown", 0.0)),
            "combined_expected_win_rate": float(
                0.50 * (swing_win_rate / 100.0) + 0.50 * (float(intraday_metrics.get("win_rate", 0.0)) / 100.0)
            ) * 100.0,
        },
        "trade_frequency": {
            "intraday_num_trades": int(intraday_metrics.get("num_trades", 0)),
            "minimum_required": 50,
            "meets_requirement": bool(int(intraday_metrics.get("num_trades", 0)) >= 50),
        },
    }

    intraday_report = {
        "engine": "alpha_intraday",
        "best_config": {
            "confidence_threshold": best["cfg"].confidence_threshold,
            "atr_multiplier": best["cfg"].atr_multiplier,
            "rr_ratio": best["cfg"].rr_ratio,
            "max_trades_per_day": best["cfg"].max_trades_per_day,
            "scanner_universe_size": len(LIQUID_NIFTY_ALPHA),
            "intervals": ["5m", "15m"],
        },
        "optimization_target": "maximize_total_return_with_pf_gt_1_5_and_winrate_gte_55",
        "intraday_metrics": intraday_metrics,
        "options_layer_metrics": option_metrics,
        "top_opportunities": top_opportunities,
    }

    out_dir = Path("backtest")
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "intraday_alpha_report.json", "w", encoding="utf-8") as f:
        json.dump(intraday_report, f, indent=2)

    with open(out_dir / "combined_portfolio_report.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    if not trades.empty:
        trades.to_csv(out_dir / "intraday_alpha_trades.csv", index=False)

    return {
        "intraday_report": intraday_report,
        "combined_report": combined,
    }


if __name__ == "__main__":
    result = run_alpha_engine()
    print(json.dumps(result, indent=2))
