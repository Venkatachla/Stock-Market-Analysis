#!/usr/bin/env python3
"""End-to-end trading flow integration test."""

from __future__ import annotations

import random
import string

import requests

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"
TIMEOUT = 20


def _random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"trader{suffix}@example.com"


def test_complete_flow() -> None:
    email = _random_email()
    password = "password123"

    register_response = requests.post(
        f"{API_BASE}/auth/signup",
        json={"email": email, "password": password, "name": "Trading Flow User"},
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    assert register_response.status_code == 200
    token = register_response.json().get("token")
    assert token
    headers = {"Authorization": f"Bearer {token}"}

    wallet_response = requests.get(f"{BASE_URL}/wallet", headers=headers, timeout=TIMEOUT)
    assert wallet_response.status_code == 200

    fund_response = requests.post(
        f"{API_BASE}/portfolio/add-demo-funds",
        params={"amount": 15000},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert fund_response.status_code == 200

    buy_response = requests.post(
        f"{API_BASE}/trading/buy",
        json={"symbol": "RELIANCE", "quantity": 1},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert buy_response.status_code == 200
    assert buy_response.json().get("status") == "success"

    portfolio_after_buy = requests.get(f"{BASE_URL}/portfolio", headers=headers, timeout=TIMEOUT)
    assert portfolio_after_buy.status_code == 200
    holdings = portfolio_after_buy.json().get("holdings", [])
    assert isinstance(holdings, list)

    transactions_response = requests.get(
        f"{BASE_URL}/portfolio/transactions",
        headers=headers,
        timeout=TIMEOUT,
    )
    assert transactions_response.status_code == 200
    transactions = transactions_response.json().get("transactions", [])
    assert isinstance(transactions, list)

    sell_response = requests.post(
        f"{API_BASE}/trading/sell",
        json={"symbol": "RELIANCE", "quantity": 1},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert sell_response.status_code == 200
    assert sell_response.json().get("status") == "success"

    final_portfolio = requests.get(f"{BASE_URL}/portfolio", headers=headers, timeout=TIMEOUT)
    assert final_portfolio.status_code == 200
