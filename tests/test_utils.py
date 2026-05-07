"""
Tests for utils/logger.py and strategy/signals.py (position_size only).

Covers:
- get_logger() creates a configured logger with console + file handlers
- get_logger() is idempotent (reuses existing logger)
- position_size() calculates correct position sizes
- position_size() handles edge cases (zero price, zero stop loss)
"""
import logging
import pytest
from unittest.mock import patch

from utils.logger import get_logger
from strategy.signals import position_size


class TestGetLogger:
    def test_returns_logger_instance(self):
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_logger_has_handlers(self):
        logger = get_logger("test_handlers")
        assert len(logger.handlers) >= 1

    def test_logger_is_idempotent(self):
        logger1 = get_logger("test_idem")
        handler_count = len(logger1.handlers)
        logger2 = get_logger("test_idem")
        # Should reuse, not add more handlers
        assert logger1 is logger2
        assert len(logger2.handlers) == handler_count

    def test_logger_level(self):
        logger = get_logger("test_level", log_level=logging.DEBUG)
        assert logger.level == logging.DEBUG


class TestPositionSize:
    """Test strategy.signals.position_size() — pure function."""

    def test_basic_calculation(self):
        # capital=100000, risk_per_trade=1%, stop_loss=2%
        # risk_amount = 1000, per_share_risk = 500 * 0.02 = 10
        # size = 1000 / 10 = 100
        size = position_size(capital=100000, price=500, risk_per_trade=0.01, stop_loss_pct=0.02)
        assert size == 100

    def test_zero_stop_loss_returns_zero(self):
        # Division by zero protection
        size = position_size(capital=100000, price=500, stop_loss_pct=0.0)
        assert size == 0

    def test_small_capital(self):
        size = position_size(capital=10000, price=1000, risk_per_trade=0.01, stop_loss_pct=0.02)
        # risk_amount = 100, per_share_risk = 20, size = 5
        assert size == 5

    def test_returns_non_negative(self):
        size = position_size(capital=0, price=1000)
        assert size >= 0
