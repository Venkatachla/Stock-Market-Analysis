from __future__ import annotations

from dataclasses import dataclass

from trading.options_engine import decide_options_strategy
from trading.risk import RiskManager


@dataclass
class TradeDecision:
    symbol: str
    trade_type: str
    action: str
    entry_price: float
    stop_loss: float
    target: float
    confidence: float
    risk_pct: float
    position_size: int
    probability_up: float
    reason: str


def decide_trade(
    symbol: str,
    trade_type: str,
    probability_up: float,
    confidence_score: float,
    entry_price: float,
    atr: float,
    liquidity_score: float,
    risk_manager: RiskManager,
    put_call_ratio: float = 1.0,
    open_interest_change: float = 0.0,
    iv_percentile: float = 0.5,
    iv_expansion_probability: float = 0.5,
    optimized_threshold: float = 60.0,
    higher_tf_trend: float = 0.0,
    regime: str | None = None,
) -> TradeDecision:
    if confidence_score < optimized_threshold:
        return TradeDecision(symbol, trade_type, "NO_TRADE", entry_price, entry_price, entry_price, confidence_score, risk_manager.limits.risk_per_trade * 100, 0, probability_up, f"Confidence below optimized threshold {optimized_threshold:.0f}")

    if liquidity_score < 0.35:
        return TradeDecision(symbol, trade_type, "NO_TRADE", entry_price, entry_price, entry_price, confidence_score, risk_manager.limits.risk_per_trade * 100, 0, probability_up, "Low liquidity")

    if regime is not None and regime.upper() in {"SIDEWAYS", "LOW_VOLATILITY"}:
        return TradeDecision(symbol, trade_type, "NO_TRADE", entry_price, entry_price, entry_price, confidence_score, risk_manager.limits.risk_per_trade * 100, 0, probability_up, f"Regime filtered: {regime}")

    if higher_tf_trend > 0 and probability_up < 0.5:
        return TradeDecision(symbol, trade_type, "NO_TRADE", entry_price, entry_price, entry_price, confidence_score, risk_manager.limits.risk_per_trade * 100, 0, probability_up, "Against higher timeframe bullish trend")
    if higher_tf_trend < 0 and probability_up > 0.5:
        return TradeDecision(symbol, trade_type, "NO_TRADE", entry_price, entry_price, entry_price, confidence_score, risk_manager.limits.risk_per_trade * 100, 0, probability_up, "Against higher timeframe bearish trend")

    if not risk_manager.can_trade():
        return TradeDecision(symbol, trade_type, "NO_TRADE", entry_price, entry_price, entry_price, confidence_score, risk_manager.limits.risk_per_trade * 100, 0, probability_up, "Risk guard active")

    atr = max(float(atr), 1e-6)
    side = "BUY" if probability_up >= 0.5 else "SELL"
    stop = entry_price - (1.5 * atr) if side == "BUY" else entry_price + (1.5 * atr)
    target = entry_price + (3.0 * atr) if side == "BUY" else entry_price - (3.0 * atr)

    if trade_type.lower() == "options":
        options = decide_options_strategy(
            probability_up=probability_up,
            confidence_score=confidence_score,
            put_call_ratio=put_call_ratio,
            open_interest_change=open_interest_change,
            iv_percentile=iv_percentile,
            iv_expansion_probability=iv_expansion_probability,
        )
        if options.action == "NO_TRADE":
            return TradeDecision(symbol, trade_type, "NO_TRADE", entry_price, stop, target, confidence_score, risk_manager.limits.risk_per_trade * 100, 0, probability_up, options.reason)
        side = options.strategy

    size = risk_manager.position_size(entry_price=entry_price, stop_loss=stop)

    return TradeDecision(
        symbol=symbol,
        trade_type=trade_type.upper(),
        action=side,
        entry_price=float(entry_price),
        stop_loss=float(stop),
        target=float(target),
        confidence=float(confidence_score),
        risk_pct=float(risk_manager.limits.risk_per_trade * 100),
        position_size=int(size),
        probability_up=float(probability_up),
        reason="High-confidence setup",
    )


def format_trade_signal(decision: TradeDecision) -> str:
    return (
        f"SYMBOL: {decision.symbol}\n"
        f"TYPE: {decision.trade_type}\n"
        f"ACTION: {decision.action}\n"
        f"ENTRY: {decision.entry_price:.2f}\n"
        f"STOP LOSS: {decision.stop_loss:.2f}\n"
        f"TARGET: {decision.target:.2f}\n"
        f"CONFIDENCE: {decision.confidence:.1f}%\n"
        f"RISK: {decision.risk_pct:.2f}%"
    )
