from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OptionsDecision:
    action: str
    strategy: str
    reason: str


def decide_options_strategy(
    probability_up: float,
    confidence_score: float,
    put_call_ratio: float,
    open_interest_change: float,
    iv_percentile: float,
    iv_expansion_probability: float,
) -> OptionsDecision:
    if confidence_score < 60:
        return OptionsDecision(action="NO_TRADE", strategy="NONE", reason="Confidence below threshold")

    if iv_percentile > 0.8:
        return OptionsDecision(action="NO_TRADE", strategy="AVOID_LONG_OPTIONS", reason="IV too high for long premium")

    if iv_percentile < 0.35 and iv_expansion_probability > 0.58:
        return OptionsDecision(action="BUY", strategy="LONG_STRADDLE_OR_STRANGLE", reason="Low IV with expansion edge")

    bullish = probability_up > 0.60 and put_call_ratio < 1.0 and open_interest_change > 0
    bearish = probability_up < 0.40 and put_call_ratio > 1.0 and open_interest_change > 0

    if bullish:
        return OptionsDecision(action="BUY", strategy="BUY_CE", reason="Bullish directional setup")
    if bearish:
        return OptionsDecision(action="BUY", strategy="BUY_PE", reason="Bearish directional setup")
    return OptionsDecision(action="NO_TRADE", strategy="NONE", reason="No options edge")
