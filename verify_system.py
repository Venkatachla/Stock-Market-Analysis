#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""StockPulse System Verification - Complete Integration Test"""

import requests
import json
import time
from datetime import datetime

BASE_URL = 'http://localhost:8000'
FRONTEND_URL = 'http://localhost:8080'

def print_section(title):
    print('\n' + '='*70)
    print(title.center(70))
    print('='*70)

def test_backend():
    print_section('BACKEND HEALTH CHECK')
    try:
        resp = requests.get(f'{BASE_URL}/health', timeout=5)
        if resp.status_code == 200:
            print('[PASS] Backend running on port 8000')
            return True
        else:
            print(f'[FAIL] Backend returned {resp.status_code}')
            return False
    except Exception as e:
        print(f'[FAIL] Backend connection failed: {str(e)}')
        return False

def test_signals():
    print_section('STOCK SIGNALS')
    try:
        resp = requests.get(f'{BASE_URL}/api/signals/active', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Total signals: {data['total']}")
            print(f"BUY signals: {data['buy_count']}")
            print(f"SELL signals: {data['sell_count']}")
            print('[PASS] Signals endpoint working')
            return True
        else:
            print(f'[FAIL] {resp.text}')
            return False
    except Exception as e:
        print(f'[FAIL] {str(e)}')
        return False

def test_auth():
    print_section('AUTHENTICATION')
    
    email = f'test{int(time.time())}@demo.com'
    password = 'Test@123'
    name = 'User'
    
    try:
        resp = requests.post(f'{BASE_URL}/auth/signup', 
            json={'email': email, 'password': password, 'name': name}, 
            timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            token = data['token']
            print('[PASS] Signup successful')
            
            resp = requests.post(f'{BASE_URL}/auth/login',
                json={'email': email, 'password': password}, timeout=5)
            if resp.status_code == 200:
                print('[PASS] Login successful')
                return True, token
        
        print(f'[FAIL] Auth failed: {resp.text}')
        return False, None
    except Exception as e:
        print(f'[FAIL] {str(e)}')
        return False, None

def test_wallet(token):
    print_section('WALLET')
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        resp = requests.get(f'{BASE_URL}/wallet', headers=headers, timeout=5)
        if resp.status_code == 200:
            wallet = resp.json()
            print(f"[PASS] Balance: Rs {wallet['balance']:,.2f}")
            return True
        else:
            print(f'[FAIL] {resp.text}')
            return False
    except Exception as e:
        print(f'[FAIL] {str(e)}')
        return False

def test_trading(token):
    print_section('TRADING')
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        # Buy
        resp = requests.post(f'{BASE_URL}/trading/buy',
            json={'symbol': 'RELIANCE', 'quantity': 5, 'price': 2850},
            headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[PASS] Buy: Rs {data['total_cost']:,.2f}")
        else:
            print(f'[FAIL] Buy: {resp.text}')
            return False
        
        # Sell
        resp = requests.post(f'{BASE_URL}/trading/sell',
            json={'symbol': 'RELIANCE', 'quantity': 2, 'price': 2860},
            headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[PASS] Sell: Rs {data['total_sale']:,.2f}")
            return True
        else:
            print(f'[FAIL] Sell: {resp.text}')
            return False
        
    except Exception as e:
        print(f'[FAIL] {str(e)}')
        return False

def test_portfolio(token):
    print_section('PORTFOLIO')
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        resp = requests.get(f'{BASE_URL}/portfolio', headers=headers, timeout=5)
        if resp.status_code == 200:
            portfolio = resp.json()
            holdings = portfolio.get('holdings', [])
            print(f"[PASS] Holdings: {len(holdings)} stocks")
            print(f"       Balance: Rs {portfolio.get('wallet', {}).get('balance', 0):,.2f}")
            return True
        else:
            print(f'[FAIL] {resp.text}')
            return False
    except Exception as e:
        print(f'[FAIL] {str(e)}')
        return False

def test_frontend():
    print_section('FRONTEND')
    try:
        resp = requests.get(FRONTEND_URL, timeout=5)
        if resp.status_code == 200:
            print('[PASS] Frontend running on port 8080')
            return True
        else:
            print(f'[WARN] Status {resp.status_code}')
            return False
    except Exception as e:
        print(f'[WARN] Frontend not running: npm run dev (in frontend/)')
        return False

def main():
    print('\n' + '='*70)
    print('STOCKPULSE SYSTEM VERIFICATION'.center(70))
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(70))
    print('='*70)
    
    results = {}
    
    results['Backend'] = test_backend()
    if not results['Backend']:
        print('\nStart backend: python -m uvicorn api.production:app --port 8000')
        return
    
    results['Signals'] = test_signals()
    
    auth_ok, token = test_auth()
    results['Auth'] = auth_ok
    
    if auth_ok and token:
        results['Wallet'] = test_wallet(token)
        results['Trading'] = test_trading(token)
        results['Portfolio'] = test_portfolio(token)
    
    results['Frontend'] = test_frontend()
    
    print_section('SUMMARY')
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for key, result in results.items():
        status = 'PASS' if result else 'FAIL'
        print(f'[{status}] {key:20}')
    
    print(f'\nResult: {passed}/{total} tests passed')
    if passed >= 6:
        print('\n*** READY FOR PRODUCTION DEPLOYMENT ***\n')
    
if __name__ == '__main__':
    main()
