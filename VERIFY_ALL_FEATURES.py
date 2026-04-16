#!/usr/bin/env python3
"""
🎯 COMPLETE SYSTEM FEATURE VERIFICATION
Tests ALL features: Auth, Trading, Wallet, Portfolio, Predictions, etc.
Run: python VERIFY_ALL_FEATURES.py
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Configuration
API_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:8080"
CORS_ORIGIN = FRONTEND_BASE

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Test results tracking
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

# Global test data
test_user = {
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "name": "Test User"
}
auth_token = None
user_id = None
wallet_id = None

def print_header(title: str):
    """Print section header"""
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}🔍 {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

def print_test(feature: str, status: bool, message: str = ""):
    """Print test result"""
    results["total"] += 1
    if status:
        results["passed"] += 1
        print(f"{GREEN}✅ {feature:<40} PASS{RESET} {message}")
    else:
        results["failed"] += 1
        print(f"{RED}❌ {feature:<40} FAIL{RESET} {message}")
        results["errors"].append((feature, message))

def api_call(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    token: Optional[str] = None,
) -> Tuple[bool, Optional[Dict], str]:
    """Make API call and return (success, response, error_msg)"""
    url = f"{API_BASE}{endpoint}"
    headers = {
        'Content-Type': 'application/json',
        'Origin': CORS_ORIGIN,
    }
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=5)
        elif method == 'POST':
            resp = requests.post(url, json=data, headers=headers, timeout=5)
        elif method == 'PUT':
            resp = requests.put(url, json=data, headers=headers, timeout=5)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, timeout=5)
        else:
            return False, None, f"Unknown method: {method}"
        
        if resp.status_code >= 200 and resp.status_code < 300:
            try:
                return True, resp.json(), ""
            except:
                return True, {"status": "ok"}, ""
        else:
            return False, None, f"Status {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, None, f"Connection error: {str(e)}"

def test_backend_health():
    """Test backend connectivity"""
    print_header("BACKEND CONNECTIVITY")
    
    success, resp, err = api_call("GET", "/health")
    print_test("Backend health check", success, err if not success else "Server responding")
    
    if not success:
        print(f"\n{RED}⚠️  Backend not responding at {API_BASE}{RESET}")
        print(f"{YELLOW}Start backend with: python -m uvicorn api.app:app --host 0.0.0.0 --port 8000{RESET}")
        return False
    
    return True

def test_frontend_connectivity():
    """Test frontend connectivity"""
    print_header("FRONTEND CONNECTIVITY")
    
    try:
        resp = requests.get(FRONTEND_BASE, timeout=5)
        print_test("Frontend accessibility", resp.status_code == 200, "Frontend running")
    except:
        print_test("Frontend accessibility", False, f"Not accessible at {FRONTEND_BASE}")
        print(f"{YELLOW}Start frontend with: cd frontend && npm run dev{RESET}")

def test_authentication():
    """Test auth endpoints"""
    print_header("AUTHENTICATION SYSTEM")
    global auth_token, user_id
    
    # Test signup
    signup_data = {
        "email": test_user["email"],
        "password": test_user["password"],
        "name": test_user["name"]
    }
    success, resp, err = api_call("POST", "/api/auth/signup", signup_data)
    print_test("User signup", success, err if not success else f"User created: {test_user['email']}")
    
    if success and resp:
        if "token" in resp:
            auth_token = resp["token"]
            user_id = resp.get("user_id")
            print_test("Auth token received", True, "Token stored")
        else:
            print_test("Auth token received", False, "No token in response")
    
    # Test login (if signup worked)
    if success:
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        success, resp, err = api_call("POST", "/api/auth/login", login_data)
        print_test("User login", success, err if not success else "Login successful")
        
        if success and resp and "token" in resp:
            auth_token = resp["token"]
            print_test("Login token received", True, "Token updated")

def test_wallet_system():
    """Test wallet endpoints"""
    print_header("WALLET SYSTEM")
    global wallet_id
    
    if not auth_token:
        print_test("Wallet operations", False, "Not authenticated")
        return
    
    # Get wallet
    success, resp, err = api_call("GET", "/api/wallet", token=auth_token)
    print_test("Get wallet", success, err if not success else "Wallet retrieved")
    
    if success and resp:
        wallet_id = resp.get("id") or resp.get("wallet_id")
        balance = resp.get("balance", 0)
        print_test("Wallet balance", balance >= 0, f"Balance: ₹{balance:,}")
    
    # Get wallet details
    success, resp, err = api_call("GET", "/api/wallet/details", token=auth_token)
    print_test("Get wallet details", success, err if not success else "Details retrieved")

def test_trading_system():
    """Test trading endpoints"""
    print_header("TRADING SYSTEM")
    
    if not auth_token:
        print_test("Trading operations", False, "Not authenticated")
        return
    
    # Get available stocks
    success, resp, err = api_call("GET", "/api/stocks", token=auth_token)
    print_test("Get available stocks", success, err if not success else f"{len(resp or []) or '?'} stocks available")
    
    stocks = resp or []
    
    # Get market data
    success, resp, err = api_call("GET", "/api/stocks/market", token=auth_token)
    print_test("Get market data", success, err if not success else "Market data available")
    
    # Get trading pairs
    success, resp, err = api_call("GET", "/api/stocks/pairs", token=auth_token)
    print_test("Get trading pairs", success, err if not success else f"{len(resp or []) or '?'} pairs available")
    
    # Get prices
    success, resp, err = api_call("GET", "/api/stocks/prices", token=auth_token)
    print_test("Get stock prices", success, err if not success else f"{len(resp or []) or '?'} prices loaded")

def test_portfolio_system():
    """Test portfolio endpoints"""
    print_header("PORTFOLIO SYSTEM")
    
    if not auth_token:
        print_test("Portfolio operations", False, "Not authenticated")
        return
    
    # Get holdings
    success, resp, err = api_call("GET", "/api/portfolio/holdings", token=auth_token)
    print_test("Get holdings", success, err if not success else f"Holdings retrieved")
    
    # Get portfolio summary
    success, resp, err = api_call("GET", "/api/portfolio", token=auth_token)
    print_test("Get portfolio summary", success, err if not success else "Summary retrieved")
    
    # Get transactions
    success, resp, err = api_call("GET", "/api/portfolio/transactions", token=auth_token)
    print_test("Get transactions", success, err if not success else "Transactions retrieved")

def test_prediction_system():
    """Test prediction endpoints"""
    print_header("PREDICTION SYSTEM")
    
    if not auth_token:
        print_test("Prediction operations", False, "Not authenticated")
        return
    
    # Get signals
    success, resp, err = api_call("GET", "/api/signals", token=auth_token)
    print_test("Get trading signals", success, err if not success else "Signals available")
    
    # Get predictions
    success, resp, err = api_call("GET", "/api/predictions", token=auth_token)
    print_test("Get API predictions", success, err if not success else "Predictions available")
    
    # Get trending
    success, resp, err = api_call("GET", "/api/trending", token=auth_token)
    print_test("Get trending stocks", success, err if not success else "Trending available")
    
    # Get discovery recommendations
    success, resp, err = api_call("GET", "/api/discovery", token=auth_token)
    print_test("Get discovery stocks", success, err if not success else "Discovery available")

def test_database_integrity():
    """Test database access"""
    print_header("DATABASE INTEGRITY")
    
    try:
        from api.core.database import get_db
        db = next(get_db())
        
        # Check users table
        user_count = db.execute("SELECT COUNT(*) FROM users").scalar()
        print_test("Users table", user_count >= 0, f"{user_count} users in DB")
        
        # Check wallet table
        wallet_count = db.execute("SELECT COUNT(*) FROM wallet").scalar()
        print_test("Wallet table", wallet_count >= 0, f"{wallet_count} wallets in DB")
        
        # Check holdings table
        holdings_count = db.execute("SELECT COUNT(*) FROM holdings").scalar()
        print_test("Holdings table", holdings_count >= 0, f"{holdings_count} holdings in DB")
        
        # Check transactions table
        trans_count = db.execute("SELECT COUNT(*) FROM transactions").scalar()
        print_test("Transactions table", trans_count >= 0, f"{trans_count} transactions in DB")
        
        db.close()
    except Exception as e:
        print_test("Database access", False, str(e))

def test_ml_system():
    """Test ML prediction system"""
    print_header("ML PREDICTION SYSTEM")
    
    try:
        from api.services.model_loader import ModelLoader
        from api.services.predictor import Predictor
        
        loader = ModelLoader()
        print_test("ML model loader", True, "Model loader initialized")
        
        predictor = Predictor()
        print_test("ML predictor", True, "Predictor initialized")
        
    except Exception as e:
        print_test("ML system", False, str(e)[:100])

def test_cors():
    """Test CORS configuration"""
    print_header("CORS CONFIGURATION")
    
    try:
        headers = {
            'Origin': FRONTEND_BASE,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        resp = requests.options(f"{API_BASE}/api/auth/signup", headers=headers, timeout=5)
        
        cors_origin = resp.headers.get('Access-Control-Allow-Origin')
        cors_methods = resp.headers.get('Access-Control-Allow-Methods')
        cors_headers = resp.headers.get('Access-Control-Allow-Headers')
        
        print_test("CORS Allow-Origin", cors_origin is not None, f"Value: {cors_origin}")
        print_test("CORS Allow-Methods", cors_methods is not None, f"Value: {cors_methods}")
        print_test("CORS Allow-Headers", cors_headers is not None, f"Value: {cors_headers}")
        
    except Exception as e:
        print_test("CORS preflight", False, str(e))

def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = results["total"]
    passed = results["passed"]
    failed = results["failed"]
    
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"{BOLD}Results:{RESET}")
    print(f"  {GREEN}✅ Passed: {passed}/{total}{RESET}")
    print(f"  {RED}❌ Failed: {failed}/{total}{RESET}")
    print(f"  {CYAN}Overall: {percentage:.1f}%{RESET}\n")
    
    if results["errors"]:
        print(f"{BOLD}{RED}Failed Tests:{RESET}")
        for feature, msg in results["errors"]:
            print(f"  • {feature}: {msg}")
        print()
    
    # Final status
    if failed == 0:
        print(f"{BOLD}{GREEN}🎉 ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}System is ready for production use.{RESET}\n")
        return True
    elif percentage >= 80:
        print(f"{BOLD}{YELLOW}⚠️  PARTIAL SUCCESS ({percentage:.0f}%){RESET}")
        print(f"{YELLOW}Most features working. Review failures above.{RESET}\n")
        return False
    else:
        print(f"{BOLD}{RED}❌ SYSTEM NOT READY ({percentage:.0f}%){RESET}")
        print(f"{RED}Multiple failures detected. Check setup.{RESET}\n")
        return False

def main():
    """Run all feature tests"""
    print(f"\n{BOLD}{CYAN}╔{'='*68}╗{RESET}")
    print(f"{BOLD}{CYAN}║ 🎯 COMPLETE SYSTEM FEATURE VERIFICATION{' '*27}║{RESET}")
    print(f"{BOLD}{CYAN}║ Testing all features: Auth | Trading | Wallet | Portfolio             ║{RESET}")
    print(f"{BOLD}{CYAN}╚{'='*68}╝{RESET}\n")
    
    print(f"{YELLOW}ℹ️  Backend: {API_BASE}{RESET}")
    print(f"{YELLOW}ℹ️  Frontend: {FRONTEND_BASE}{RESET}\n")
    
    # Run all tests
    if not test_backend_health():
        print(f"\n{RED}{BOLD}❌ Cannot proceed - backend not responding{RESET}")
        sys.exit(1)
    
    test_frontend_connectivity()
    test_authentication()
    test_wallet_system()
    test_trading_system()
    test_portfolio_system()
    test_prediction_system()
    test_cors()
    test_database_integrity()
    test_ml_system()
    
    # Print summary
    success = print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
