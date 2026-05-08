"""
Tests for signal and prompt endpoints in api/app_fixed.py.

Covers:
- GET /api/signals/active — returns all stock signals with counts
- POST /api/prompt — AI prompt filtering by bullish/bearish/general queries
"""
import pytest


class TestActiveSignals:
    def test_signals_returns_200(self, client):
        resp = client.get("/api/signals/active")
        assert resp.status_code == 200

    def test_signals_response_shape(self, client):
        data = client.get("/api/signals/active").json()
        for key in ("signals", "total", "buy_count", "sell_count", "timestamp"):
            assert key in data

    def test_signals_count_matches_config(self, client):
        data = client.get("/api/signals/active").json()
        assert data["total"] == 8

    def test_signals_buy_sell_counts_correct(self, client):
        data = client.get("/api/signals/active").json()
        assert data["buy_count"] == 5
        assert data["sell_count"] == 3

    def test_each_signal_has_required_fields(self, client):
        data = client.get("/api/signals/active").json()
        for s in data["signals"]:
            for f in ("symbol", "price", "signal_type", "confidence", "reason"):
                assert f in s


class TestPromptEndpoint:
    def test_prompt_buy_query_returns_bullish(self, client):
        resp = client.post("/api/prompt", json={"query": "show me buy signals"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "bullish"
        for r in data["results"]:
            assert r["signal_type"] == "BUY"

    def test_prompt_sell_query_returns_bearish(self, client):
        data = client.post("/api/prompt", json={"query": "sell signals"}).json()
        assert data["intent"] == "bearish"
        for r in data["results"]:
            assert r["signal_type"] == "SELL"

    def test_prompt_symbol_search(self, client):
        data = client.post("/api/prompt", json={"query": "reliance"}).json()
        assert data["intent"] == "general"
        assert len(data["results"]) >= 1

    def test_prompt_with_limit(self, client):
        data = client.post("/api/prompt", json={"query": "buy", "limit": 2}).json()
        assert len(data["results"]) <= 2

    def test_prompt_no_match_returns_empty(self, client):
        data = client.post("/api/prompt", json={"query": "zzzznonexistent"}).json()
        assert len(data["results"]) == 0

    def test_prompt_results_sorted_by_confidence(self, client):
        data = client.post("/api/prompt", json={"query": "buy"}).json()
        confs = [r["confidence"] for r in data["results"]]
        assert confs == sorted(confs, reverse=True)
