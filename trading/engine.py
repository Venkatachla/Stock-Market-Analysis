from dataclasses import dataclass


@dataclass
class TradePlan:
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: int
    risk_reward: float
    trade_validity: bool


def build_trade_plan(
    latest_price: float,
    atr: float,
    confidence_score: float,
    capital: float = 100000.0,
    risk_pct: float = 0.01,
    reward_multiple: float = 2.0,
    min_confidence: float = 60.0,
) -> TradePlan:
    atr = max(float(atr), 0.0001)
    stop_distance = atr * 1.5
    stop_loss = latest_price - stop_distance
    take_profit = latest_price + (stop_distance * reward_multiple)

    risk_amount = capital * risk_pct
    per_share_risk = max(latest_price - stop_loss, 0.0001)
    size = int(risk_amount / per_share_risk)
    size = max(size, 0)

    return TradePlan(
        entry_price=float(latest_price),
        stop_loss=float(stop_loss),
        take_profit=float(take_profit),
        position_size=size,
        risk_reward=float(reward_multiple),
        trade_validity=bool(confidence_score >= min_confidence),
    )
