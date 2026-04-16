#!/usr/bin/env python3
"""
COMPLETE SYSTEM TEST - Verify all trades, payments, and features work
Run: python COMPLETE_SYSTEM_TEST.py
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:8080"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Test counters
tests_passed = 0
tests_failed = 0
errors = []

def test(name: str, fn):
    """Run a test and track results"""
    global tests_passed, tests_failed
    try:
        fn()
        print(f"{GREEN}✅ {name}{RESET}")
        tests_passed += 1
    except AssertionError as e:
        print(f"{RED}❌ {name}: {e}{RESET}")
        tests_failed += 1
        errors.append((name, str(e)))
    except Exception as e:
        print(f"{RED}❌ {name}: {str(e)[:100]}{RESET}")
        tests_failed += 1
        errors.append((name, str(e)))

def header(title: str):
    """Print section header"""
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}🔍 {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

# Test data
test_email = f"test_{int(time.time())}@example.com"
test_password = "TestPassword123!"
token = None
user_id = None

# ============ TESTS ============

def test_health():
    """Backend health check"""
    r = requests.get(f"{API_BASE}/health", timeout=5)
    assert r.status_code == 200

def test_frontend():
    """Frontend accessible"""
    r = requests.get(FRONTEND_BASE, timeout=5)
    assert r.status_code == 200

def test_signup():
    """User signup"""
    global token, user_id
    r = requests.post(
        f"{API_BASE}/api/auth/signup",
        json={"email": test_email, "password": test_password, "name": "Test User"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    token = data["token"]
    user_id = data["user_id"]
    assert token

def test_login():
    """User login"""
    r = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": test_email, "password": test_password},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert data["token"]

def test_get_wallet():
    """Get wallet balance"""
    r = requests.get(
        f"{API_BASE}/wallet",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert "balance" in data
    assert data["balance"] >= 0

def test_get_signals():
    """Get trading signals"""
    r = requests.get(
        f"{API_BASE}/api/signals/active",
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert "signals" in data
    assert len(data["signals"]) > 0

def test_get_stock_price():
    """Get stock price"""
    r = requests.get(
        f"{API_BASE}/api/stock/INFY/price",
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert "price" in data
    assert data["price"] > 0

def test_buy_stock():
    """Buy stock"""
    r = requests.post(
        f"{API_BASE}/api/trading/buy",
        json={"symbol": "INFY", "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "transaction_id" in data
    assert data["symbol"] == "INFY"

def test_buy_multiple():
    """Buy multiple shares"""
    r = requests.post(
        f"{API_BASE}/api/trading/buy",
        json={"symbol": "TCS", "quantity": 5},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert data["quantity"] == 5

def test_sell_stock():
    """Sell stock"""
    r = requests.post(
        f"{API_BASE}/api/trading/sell",
        json={"symbol": "INFY", "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"

def test_get_portfolio():
    """Get portfolio summary"""
    r = requests.get(
        f"{API_BASE}/portfolio",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert "total_value" in data
    assert "holdings" in data

def test_get_transactions():
    """Get transaction history"""
    r = requests.get(
        f"{API_BASE}/portfolio/transactions",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert "transactions" in data
    assert len(data["transactions"]) > 0

def test_create_payment_order():
    """Create payment order"""
    r = requests.post(
        f"{API_BASE}/api/payment/create-order",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert "order_id" in data

def test_search_stocks():
    """Search stocks"""
    r = requests.post(
        f"{API_BASE}/api/search",
        json={"query": "INFY", "limit": 5},
        timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert "results" in data

# ============ MAIN ============

def main():
    """Run all tests"""
    print(f"\n{BOLD}{CYAN}╔{'='*68}╗{RESET}")
    print(f"{BOLD}{CYAN}║ 🧪 COMPLETE SYSTEM TEST - StockPulse{' '*31}║{RESET}")
    print(f"{BOLD}{CYAN}╚{'='*68}╝{RESET}\n")
    
    print(f"{YELLOW}ℹ️  Backend: {API_BASE}{RESET}")
    print(f"{YELLOW}ℹ️  Frontend: {FRONTEND_BASE}{RESET}\n")
    
    # Auth tests
    header("AUTHENTICATION")
    test("Backend health", test_health)
    test("Frontend accessible", test_frontend)
    test("User signup", test_signup)
    test("User login", test_login)
    
    # Wallet tests
    header("WALLET SYSTEM")
    test("Get wallet balance", test_get_wallet)
    
    # Trading tests
    header("TRADING SYSTEM")
    test("Get stock signals", test_get_signals)
    test("Get stock price", test_get_stock_price)
    test("Buy single share", test_buy_stock)
    test("Buy multiple shares", test_buy_multiple)
    test("Sell shares", test_sell_stock)
    
    # Portfolio tests
    header("PORTFOLIO SYSTEM")
    test("Get portfolio summary", test_get_portfolio)
    test("Get transactions", test_get_transactions)
    
    # Payment tests
    header("PAYMENT SYSTEM")
    test("Create payment order", test_create_payment_order)
    
    # Search tests
    header("SEARCH SYSTEM")
    test("Search stocks", test_search_stocks)
    
    # Summary
    header("TEST SUMMARY")
    
    total = tests_passed + tests_failed
    percentage = (tests_passed / total * 100) if total > 0 else 0
    
    print(f"{GREEN}✅ Passed: {tests_passed}/{total}{RESET}")
    print(f"{RED if tests_failed > 0 else GREEN}❌ Failed: {tests_failed}/{total}{RESET}")
    print(f"{CYAN}Overall: {percentage:.1f}%{RESET}\n")
    
    if errors:
        print(f"{BOLD}{RED}Failed Tests:{RESET}")
        for name, error in errors:
            print(f"  • {name}")
            print(f"    → {error[:100]}")
    
    # Final status
    if tests_failed == 0:
        print(f"\n{BOLD}{GREEN}🎉 ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}System is ready for production use.{RESET}\n")
        return 0
    elif percentage >= 80:
        print(f"\n{BOLD}{YELLOW}⚠️  PARTIAL SUCCESS ({percentage:.0f}%){RESET}")
        print(f"{YELLOW}Most features working. Review failures above.{RESET}\n")
        return 1
    else:
        print(f"\n{BOLD}{RED}❌ SYSTEM NOT READY ({percentage:.0f}%){RESET}")
        print(f"{RED}Multiple failures detected.{RESET}\n")
        return 1

if __name__ == "__main__":
    exit(main())
