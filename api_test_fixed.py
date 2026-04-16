#!/usr/bin/env python3
"""
COMPLETE API TEST SUITE - Test all endpoints with proper error handling
Run: python api_test_fixed.py
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
API_BASE = "http://localhost:8000"
CORS_ORIGIN = "http://localhost:8080"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Test data
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Test User"
TOKEN = None
USER_ID = None

def log_info(msg: str):
    """Log info message"""
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def log_success(msg: str):
    """Log success message"""
    print(f"{GREEN}✅ {msg}{RESET}")

def log_error(msg: str):
    """Log error message"""
    print(f"{RED}❌ {msg}{RESET}")

def log_warning(msg: str):
    """Log warning message"""
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def log_header(msg: str):
    """Log header"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{msg}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def test_endpoint(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    token: Optional[str] = None,
    headers: Optional[Dict] = None,
) -> Optional[Dict[str, Any]]:
    """
    Test an API endpoint
    """
    url = f"{API_BASE}{endpoint}"
    
    # Prepare headers
    req_headers = {
        'Content-Type': 'application/json',
        'Origin': CORS_ORIGIN,
    }
    
    if token:
        req_headers['Authorization'] = f'Bearer {token}'
    
    if headers:
        req_headers.update(headers)
    
    log_info(f"[{method}] {endpoint}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=req_headers, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=req_headers, timeout=5)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=req_headers, timeout=5)
        elif method == 'DELETE':
            response = requests.delete(url, headers=req_headers, timeout=5)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Check for CORS headers
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if cors_header:
            log_success(f"CORS Header present: {cors_header}")
        else:
            log_warning("No CORS header in response")
        
        # Check response
        if response.status_code >= 200 and response.status_code < 300:
            try:
                result = response.json()
                log_success(f"Status {response.status_code}: {response.reason}")
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
                return result
            except:
                log_success(f"Status {response.status_code}: {response.reason}")
                return {"status": "ok", "text": response.text[:100]}
        else:
            log_error(f"Status {response.status_code}: {response.reason}")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data)}")
            except:
                print(f"   Error: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        log_error(f"Connection error - is backend running on {API_BASE}?")
        return None
    except requests.exceptions.Timeout:
        log_error("Request timeout")
        return None
    except Exception as e:
        log_error(f"Exception: {str(e)}")
        return None

def main():
    """Run all tests"""
    global TOKEN, USER_ID
    
    print(f"\n{BOLD}{BLUE}")
    print("""
    ██████╗ ██╗███████╗██╗  ██╗ ██████╗  ██████╗ ██╗   ██╗███████╗
    ██╔══██╗██║██╔════╝██║  ██║██╔═████╗██╔════╝ ██║   ██║██╔════╝
    ██████╔╝██║███████╗███████║██║██╔██║██║  ███╗██║   ██║███████╗
    ██╔══██╗██║╚════██║╚════██║████╔╝██║██║   ██║██║   ██║╚════██║
    ██║  ██║██║███████║     ██║╚██████╔╝╚██████╔╝╚██████╔╝███████║
    ╚═╝  ╚═╝╚═╝╚══════╝     ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝
    {RESET}
    """)
    
    log_header("1. HEALTH CHECK")
    result = test_endpoint('GET', '/health')
    if not result:
        log_error("Backend is not running! Start with: START_FIXED.bat")
        return
    
    log_header("2. API INFO")
    test_endpoint('GET', '/')
    
    log_header("3. AUTHENTICATION - SIGNUP")
    log_info(f"Creating user: {TEST_EMAIL}")
    result = test_endpoint('POST', '/api/auth/signup', {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'name': TEST_NAME,
    })
    
    if result and 'token' in result:
        TOKEN = result['token']
        USER_ID = result.get('user_id')
        log_success(f"Got token: {TOKEN[:20]}...")
        log_success(f"User ID: {USER_ID}")
    else:
        log_error("Signup failed - cannot proceed with other tests")
        return
    
    log_header("4. AUTHENTICATION - GET CURRENT USER")
    test_endpoint('GET', '/api/auth/me', token=TOKEN)
    
    log_header("5. MARKET DATA - ACTIVE SIGNALS (with REAL PRICES)")
    result = test_endpoint('GET', '/api/signals/active')
    if result and 'signals' in result:
        signals = result['signals']
        log_success(f"Got {len(signals)} signals")
        for signal in signals[:3]:  # Show first 3
            print(f"   • {signal['symbol']}: ₹{signal.get('price', 'N/A')} ({signal.get('signal_type', 'N/A')})")
    
    log_header("6. WALLET - GET BALANCE")
    test_endpoint('GET', '/wallet', token=TOKEN)
    
    log_header("7. PORTFOLIO - GET HOLDINGS")
    test_endpoint('GET', '/portfolio', token=TOKEN)
    
    log_header("8. TRADING - BUY STOCK")
    log_info("Attempting to buy 2 shares of RELIANCE")
    result = test_endpoint('POST', '/api/trading/buy', {
        'symbol': 'RELIANCE',
        'quantity': 2,
    }, token=TOKEN)
    
    log_header("9. PORTFOLIO - CHECK HOLDINGS AFTER BUY")
    test_endpoint('GET', '/portfolio', token=TOKEN)
    
    log_header("10. TRADING - SELL STOCK")
    log_info("Attempting to sell 1 share of RELIANCE")
    result = test_endpoint('POST', '/api/trading/sell', {
        'symbol': 'RELIANCE',
        'quantity': 1,
    }, token=TOKEN)
    
    log_header("11. TRANSACTION HISTORY")
    test_endpoint('GET', '/portfolio/transactions', token=TOKEN)
    
    log_header("12. PAYMENT - CREATE ORDER")
    result = test_endpoint('POST', '/api/payment/create-order', {
        'amount': 10000,
    }, token=TOKEN)
    
    if result and 'order_id' in result:
        order_id = result['order_id']
        
        log_header("13. PAYMENT - VERIFY ORDER")
        test_endpoint('POST', '/api/payment/verify', {
            'order_id': order_id,
            'payment_id': 'pay_test_123',
            'signature': 'sig_test_123',
        }, token=TOKEN)
    
    log_header("14. FINAL PORTFOLIO CHECK")
    test_endpoint('GET', '/portfolio', token=TOKEN)
    
    log_header("SUMMARY")
    log_success("All endpoints tested!")
    print(f"""
    {GREEN}
    ✅ Backend: {API_BASE}
    ✅ Frontend: http://localhost:8080
    ✅ Test User: {TEST_EMAIL}
    ✅ Token: {TOKEN[:30]}...
    
    {YELLOW}NEXT STEPS:{RESET}
    1. Open http://localhost:8080 in browser
    2. Sign up with: {TEST_EMAIL} / {TEST_PASSWORD}
    3. Check if prices display as ₹ (not ₹0.00)
    4. Try buying/selling stocks
    5. Check portfolio updates
    
    {RESET}
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
    except Exception as e:
        log_error(f"Fatal error: {str(e)}")
