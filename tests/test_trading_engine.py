"""
Tests for trading/ modules — pure computation, no mocking needed.

Covers:
- trading/engine.py: build_trade_plan()
- trading/risk.py: RiskManager, RiskLimits, trailing_stop()
- trading/options_engine.py: decide_options_strategy()
- trading/decision_engine.py: decide_trade(), format_trade_signal()
"""
import pytest
from trading.engine import build_trade_plan, TradePlan
from trading.risk import RiskManager, RiskLimits, DayRiskState, trailing_stop
from trading.options_engine import decide_options_strategy, OptionsDecision
from trading.decision_engine import decide_trade, format_trade_signal, TradeDecision


# ===================== build_trade_plan =====================

class TestBuildTradePlan:
    def test_returns_trade_plan(self):
        plan = build_trade_plan(latest_price=1000, atr=20, confidence_score=75)
        assert isinstance(plan, TradePlan)

    def test_stop_loss_below_entry(self):
        plan = build_trade_plan(latest_price=1000, atr=20, confidence_score=75)
        assert plan.stop_loss < plan.entry_price

    def test_take_profit_above_entry(self):
        plan = build_trade_plan(latest_price=1000, atr=20, confidence_score=75)
        assert plan.take_profit > plan.entry_price

    def test_trade_validity_high_confidence(self):
        plan = build_trade_plan(latest_price=1000, atr=20, confidence_score=75)
        assert plan.trade_validity is True

    def test_trade_validity_low_confidence(self):
        plan = build_trade_plan(latest_price=1000, atr=20, confidence_score=50)
        assert plan.trade_validity is False

    def test_position_size_positive(self):
        plan = build_trade_plan(latest_price=1000, atr=20, confidence_score=75, capital=100000)
        assert plan.position_size > 0

    def test_zero_atr_handled(self):
        # atr=0 should be clamped to 0.0001, not cause division by zero
        plan = build_trade_plan(latest_price=1000, atr=0, confidence_score=75)
        assert plan.position_size >= 0

    def test_custom_risk_and_reward(self):
        plan = build_trade_plan(
            latest_price=500, atr=10, confidence_score=80,
            capital=200000, risk_pct=0.02, reward_multiple=3.0,
        )
        assert plan.risk_reward == 3.0


# ===================== RiskManager =====================

class TestRiskManager:
    def test_default_can_trade(self):
        rm = RiskManager()
        assert rm.can_trade() is True

    def test_max_trades_per_day_blocks(self):
        rm = RiskManager(RiskLimits(max_trades_per_day=2))
        rm.state.trades_taken = 2
        assert rm.can_trade() is False

    def test_consecutive_losses_blocks(self):
        rm = RiskManager(RiskLimits(max_consecutive_losses=3))
        rm.state.consecutive_losses = 3
        assert rm.can_trade() is False

    def test_daily_loss_limit_blocks(self):
        rm = RiskManager(RiskLimits(capital=100000, max_daily_loss_pct=0.05))
        rm.state.daily_realized_pnl = -5001  # exceeds 5% of 100k
        assert rm.can_trade() is False

    def test_position_size_calculation(self):
        rm = RiskManager(RiskLimits(capital=100000, risk_per_trade=0.01))
        # Risk amount = 1000, per-unit risk = |1000 - 950| = 50
        size = rm.position_size(entry_price=1000, stop_loss=950)
        assert size == 20  # 1000 / 50

    def test_position_size_zero_risk(self):
        rm = RiskManager()
        # Entry == Stop → near-zero risk → large size capped by int
        size = rm.position_size(entry_price=1000, stop_loss=1000)
        assert size >= 0

    def test_record_winning_trade(self):
        rm = RiskManager()
        rm.record_trade_result(500)
        assert rm.state.trades_taken == 1
        assert rm.state.daily_realized_pnl == 500
        assert rm.state.consecutive_losses == 0

    def test_record_losing_trade(self):
        rm = RiskManager()
        rm.record_trade_result(-200)
        assert rm.state.consecutive_losses == 1
        assert rm.state.daily_realized_pnl == -200

    def test_consecutive_losses_reset_on_win(self):
        rm = RiskManager()
        rm.record_trade_result(-100)
        rm.record_trade_result(-100)
        assert rm.state.consecutive_losses == 2
        rm.record_trade_result(100)
        assert rm.state.consecutive_losses == 0


# ===================== trailing_stop =====================

class TestTrailingStop:
    def test_long_trailing_stop_increases(self):
        # Price moved up → stop should ratchet up
        new_stop = trailing_stop(current_price=1100, last_stop=1000, atr=50, side="long")
        assert new_stop >= 1000

    def test_long_trailing_stop_never_decreases(self):
        new_stop = trailing_stop(current_price=900, last_stop=1000, atr=50, side="long")
        assert new_stop == 1000  # should not go below last_stop

    def test_short_trailing_stop_decreases(self):
        new_stop = trailing_stop(current_price=900, last_stop=1000, atr=50, side="short")
        assert new_stop <= 1000

    def test_short_trailing_stop_never_increases(self):
        new_stop = trailing_stop(current_price=1100, last_stop=1000, atr=50, side="short")
        assert new_stop == 1000


# ===================== decide_options_strategy =====================

class TestDecideOptionsStrategy:
    def test_low_confidence_no_trade(self):
        result = decide_options_strategy(0.7, 50, 1.0, 0, 0.5, 0.5)
        assert result.action == "NO_TRADE"

    def test_high_iv_no_trade(self):
        result = decide_options_strategy(0.7, 80, 1.0, 0, 0.85, 0.5)
        assert result.action == "NO_TRADE"
        assert "IV" in result.reason

    def test_low_iv_expansion_straddle(self):
        result = decide_options_strategy(0.5, 70, 1.0, 0, 0.3, 0.6)
        assert result.action == "BUY"
        assert "STRADDLE" in result.strategy

    def test_bullish_setup_buy_ce(self):
        result = decide_options_strategy(0.7, 75, 0.8, 100, 0.5, 0.4)
        assert result.action == "BUY"
        assert result.strategy == "BUY_CE"

    def test_bearish_setup_buy_pe(self):
        result = decide_options_strategy(0.3, 75, 1.5, 100, 0.5, 0.4)
        assert result.action == "BUY"
        assert result.strategy == "BUY_PE"

    def test_no_edge_no_trade(self):
        result = decide_options_strategy(0.5, 70, 1.0, 0, 0.5, 0.4)
        assert result.action == "NO_TRADE"


# ===================== decide_trade =====================

class TestDecideTrade:
    def _make_rm(self):
        return RiskManager(RiskLimits(capital=100000))

    def test_low_confidence_no_trade(self):
        d = decide_trade("INFY", "equity", 0.7, 50, 1000, 20, 0.8, self._make_rm())
        assert d.action == "NO_TRADE"
        assert "threshold" in d.reason.lower()

    def test_low_liquidity_no_trade(self):
        d = decide_trade("INFY", "equity", 0.7, 80, 1000, 20, 0.2, self._make_rm())
        assert d.action == "NO_TRADE"
        assert "liquidity" in d.reason.lower()

    def test_sideways_regime_no_trade(self):
        d = decide_trade("INFY", "equity", 0.7, 80, 1000, 20, 0.8, self._make_rm(), regime="SIDEWAYS")
        assert d.action == "NO_TRADE"

    def test_against_htf_bullish_no_trade(self):
        # Higher TF is bullish (+1) but probability_up < 0.5 → conflict
        d = decide_trade("INFY", "equity", 0.3, 80, 1000, 20, 0.8, self._make_rm(), higher_tf_trend=1.0)
        assert d.action == "NO_TRADE"

    def test_risk_guard_blocks(self):
        rm = self._make_rm()
        rm.state.trades_taken = 999
        d = decide_trade("INFY", "equity", 0.7, 80, 1000, 20, 0.8, rm)
        assert d.action == "NO_TRADE"

    def test_valid_buy_signal(self):
        d = decide_trade("INFY", "equity", 0.7, 80, 1000, 20, 0.8, self._make_rm())
        assert d.action == "BUY"
        assert d.position_size > 0

    def test_valid_sell_signal(self):
        d = decide_trade("INFY", "equity", 0.3, 80, 1000, 20, 0.8, self._make_rm())
        assert d.action == "SELL"

    def test_options_trade_type(self):
        d = decide_trade(
            "INFY", "options", 0.7, 80, 1000, 20, 0.8, self._make_rm(),
            put_call_ratio=0.8, open_interest_change=100,
            iv_percentile=0.5, iv_expansion_probability=0.4,
        )
        assert d.trade_type == "OPTIONS"


# ===================== format_trade_signal =====================

class TestFormatTradeSignal:
    def test_format_contains_key_fields(self):
        d = TradeDecision("INFY", "EQUITY", "BUY", 1000, 970, 1060, 85, 1.0, 33, 0.7, "Test")
        output = format_trade_signal(d)
        assert "INFY" in output
        assert "BUY" in output
        assert "1000" in output
        assert "CONFIDENCE" in output
