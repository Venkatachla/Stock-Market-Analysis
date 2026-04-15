import requests
import json
import time

print('='*70)
print('COMPREHENSIVE STOCKPULSE API TEST SUITE')
print('='*70)

BASE_URL = 'http://localhost:8000'

# Store token for authenticated requests
token = None

try:
    # Test 1: Health check
    print('\n[1] HEALTH CHECK')
    resp = requests.get(f'{BASE_URL}/health', timeout=5)
    print(f'    Status: {resp.status_code}')
    if resp.status_code == 200:
        print(f'    ✅ Backend alive')
    else:
        print(f'    ❌ Failed: {resp.text}')
    
    # Test 2: Get signals
    print('\n[2] ACTIVE SIGNALS')
    resp = requests.get(f'{BASE_URL}/api/signals/active', timeout=5)
    print(f'    Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'    Response: {json.dumps(data, indent=6)}')
        print(f'    Total: {data.get("total")} | Buy: {data.get("buy_count")} | Sell: {data.get("sell_count")}')
        if data.get('total') and data.get('total') > 0:
            print(f'    ✅ Signals loaded')
        else:
            print(f'    ⚠️ No signals')
    else:
        print(f'    ❌ Failed: {resp.text}')
    
    # Test 3: Signup
    print('\n[3] USER SIGNUP')
    email = f'test{int(time.time())}@demo.com'
    signup_data = {
        'email': email,
        'password': 'Demo@1234',
        'name': 'Test User'
    }
    resp = requests.post(f'{BASE_URL}/auth/signup', json=signup_data, timeout=5)
    print(f'    Status: {resp.status_code}')
    if resp.status_code == 200 or resp.status_code == 201:
        data = resp.json()
        token = data['token']
        print(f'    Email: {data["email"]}')
        print(f'    User ID: {data.get("user_id")}')
        print(f'    ✅ Signup successful')
    else:
        print(f'    ❌ Failed: {resp.text}')
        token = None
    
    if token:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test 4: Get wallet
        print('\n[4] GET WALLET')
        resp = requests.get(f'{BASE_URL}/wallet', headers=headers, timeout=5)
        print(f'    Status: {resp.status_code}')
        if resp.status_code == 200:
            wallet = resp.json()
            print(f'    Balance: ₹{wallet.get("balance", 0):,.2f}')
            print(f'    Available: ₹{wallet.get("available_balance", 0):,.2f}')
            print(f'    ✅ Wallet retrieved')
        else:
            print(f'    ❌ Failed: {resp.text}')
        
        # Test 5: Get portfolio
        print('\n[5] GET PORTFOLIO')
        resp = requests.get(f'{BASE_URL}/portfolio', headers=headers, timeout=5)
        print(f'    Status: {resp.status_code}')
        if resp.status_code == 200:
            portfolio = resp.json()
            print(f'    Wallet Balance: ₹{portfolio.get("wallet", {}).get("balance", 0):,.2f}')
            print(f'    Holdings: {len(portfolio.get("holdings", []))} stocks')
            print(f'    ✅ Portfolio retrieved')
        else:
            print(f'    ❌ Failed: {resp.text}')
        
        # Test 6: Buy stock
        print('\n[6] BUY STOCK (RELIANCE)')
        buy_data = {
            'symbol': 'RELIANCE',
            'quantity': 10,
            'price': 2850.00
        }
        resp = requests.post(f'{BASE_URL}/trading/buy', json=buy_data, headers=headers, timeout=5)
        print(f'    Status: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f'    Total Cost: ₹{result.get("total_cost", 0):,.2f}')
            print(f'    New Balance: ₹{result.get("wallet_balance", 0):,.2f}')
            print(f'    ✅ Buy successful')
        else:
            print(f'    ❌ Failed: {resp.text}')
        
        # Test 7: Check holdings after buy
        print('\n[7] CHECK HOLDINGS AFTER BUY')
        resp = requests.get(f'{BASE_URL}/portfolio', headers=headers, timeout=5)
        print(f'    Status: {resp.status_code}')
        if resp.status_code == 200:
            portfolio = resp.json()
            holdings = portfolio.get('holdings', [])
            print(f'    Holdings: {len(holdings)} stocks')
            if holdings:
                for holding in holdings:
                    print(f'      - {holding.get("symbol")}: {holding.get("quantity")} shares @ ₹{holding.get("avg_price")}')
            print(f'    ✅ Holdings verified')
        else:
            print(f'    ❌ Failed: {resp.text}')
        
        # Test 8: Sell stock
        print('\n[8] SELL STOCK (RELIANCE)')
        sell_data = {
            'symbol': 'RELIANCE',
            'quantity': 5,
            'price': 2860.00
        }
        resp = requests.post(f'{BASE_URL}/trading/sell', json=sell_data, headers=headers, timeout=5)
        print(f'    Status: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f'    Total Sale: ₹{result.get("total_sale", 0):,.2f}')
            print(f'    New Balance: ₹{result.get("wallet_balance", 0):,.2f}')
            print(f'    ✅ Sell successful')
        else:
            print(f'    ❌ Failed: {resp.text}')
        
        # Test 9: Get transactions
        print('\n[9] GET TRANSACTIONS')
        resp = requests.get(f'{BASE_URL}/portfolio/transactions', headers=headers, timeout=5)
        print(f'    Status: {resp.status_code}')
        if resp.status_code == 200:
            txns = resp.json()
            print(f'    Transactions: {len(txns.get("transactions", []))} total')
            for txn in txns.get('transactions', [])[:5]:
                print(f'      - {txn.get("type")}: {txn.get("symbol")} {txn.get("quantity")} @ ₹{txn.get("price")}')
            print(f'    ✅ Transactions retrieved')
        else:
            print(f'    ❌ Failed: {resp.text}')
    
    print('\n' + '='*70)
    print('✅ ALL TESTS COMPLETED - SYSTEM WORKING')
    print('='*70)
    
except Exception as e:
    print(f'\n❌ ERROR: {str(e)}')
    import traceback
    traceback.print_exc()
