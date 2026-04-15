from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskLimits:
    capital: float = 100000.0
    risk_per_trade: float = 0.01
    max_daily_loss_pct: float = 0.05
    max_consecutive_losses: int = 3
    max_trades_per_day: int = 3


@dataclass
class DayRiskState:
    daily_realized_pnl: float = 0.0
    consecutive_losses: int = 0
    trades_taken: int = 0


class RiskManager:
    def __init__(self, limits: RiskLimits | None = None):
        self.limits = limits or RiskLimits()
        self.state = DayRiskState()

    def can_trade(self) -> bool:
        if self.state.trades_taken >= self.limits.max_trades_per_day:
            return False
        if self.state.consecutive_losses >= self.limits.max_consecutive_losses:
            return False
        if self.state.daily_realized_pnl <= -(self.limits.capital * self.limits.max_daily_loss_pct):
            return False
        return True

    def position_size(self, entry_price: float, stop_loss: float) -> int:
        risk_amount = self.limits.capital * self.limits.risk_per_trade
        per_unit_risk = max(abs(entry_price - stop_loss), 1e-6)
        size = int(risk_amount / per_unit_risk)
        return max(size, 0)

    def record_trade_result(self, pnl: float) -> None:
        self.state.trades_taken += 1
        self.state.daily_realized_pnl += pnl
        if pnl < 0:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0


def trailing_stop(current_price: float, last_stop: float, atr: float, side: str = "long") -> float:
    atr = max(float(atr), 1e-6)
    if side.lower() == "long":
        return max(last_stop, current_price - (1.2 * atr))
    return min(last_stop, current_price + (1.2 * atr))
