#!/usr/bin/env python3
"""Pytest integration tests for StockPulse backend endpoints."""

from __future__ import annotations

import random
import string
from typing import Dict

import requests

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"
TIMEOUT = 20


def _random_email(prefix: str = "test") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"{prefix}{suffix}@example.com"


def test_health() -> None:
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") in {"ok", "alive"}


def test_login() -> None:
    email = _random_email("login")
    password = "password123"

    signup_response = requests.post(
        f"{API_BASE}/auth/signup",
        json={"email": email, "password": password, "name": "CI Login User"},
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    assert signup_response.status_code == 200

    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("token")
    assert data.get("email") == email


def _create_user_and_headers() -> Dict[str, str]:
    email = _random_email("wallet")
    password = "password123"
    response = requests.post(
        f"{API_BASE}/auth/signup",
        json={"email": email, "password": password, "name": "CI Test User"},
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200
    token = response.json().get("token")
    assert token
    return {"Authorization": f"Bearer {token}"}


def test_wallet() -> None:
    headers = _create_user_and_headers()
    response = requests.get(f"{BASE_URL}/wallet", headers=headers, timeout=TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert "available_balance" in data
    assert "used_balance" in data
    assert "total_balance" in data


def test_portfolio() -> None:
    headers = _create_user_and_headers()
    response = requests.get(f"{BASE_URL}/portfolio", headers=headers, timeout=TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert "holdings" in data
    assert "available_balance" in data
    assert "portfolio_value" in data


def test_buy_stock() -> None:
    headers = _create_user_and_headers()
    fund_response = requests.post(
        f"{API_BASE}/portfolio/add-demo-funds",
        params={"amount": 10000},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert fund_response.status_code == 200

    response = requests.post(
        f"{API_BASE}/trading/buy",
        json={"symbol": "RELIANCE", "quantity": 1},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    assert data.get("total_cost") is not None


def test_transactions() -> None:
    headers = _create_user_and_headers()
    response = requests.get(f"{BASE_URL}/portfolio/transactions", headers=headers, timeout=TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert isinstance(data["transactions"], list)
