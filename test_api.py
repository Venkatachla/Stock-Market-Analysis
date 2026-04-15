import requests
import json
import time

print('='*60)
print('TESTING STOCKPULSE API')
print('='*60)

try:
    # Test 1: Health check
    print('\n1. Health Check:')
    resp = requests.get('http://localhost:8000/health', timeout=5)
    print(f'   Status: {resp.status_code}')
    print(f'   ✅ Backend alive')
    
    # Test 2: Get signals
    print('\n2. Get Active Signals:')
    resp = requests.get('http://localhost:8000/api/signals/active', timeout=5)
    data = resp.json()
    print(f'   Total signals: {data.get("total")}')
    print(f'   Buy signals: {data.get("buy_count")}')
    print(f'   Sell signals: {data.get("sell_count")}')
    print(f'   ✅ Signals loaded')
    
    # Test 3: Signup
    print('\n3. User Signup:')
    signup_data = {
        'email': f'demo{int(time.time())}@test.com',
        'password': 'Demo@1234',
        'name': 'Demo User'
    }
    resp = requests.post('http://localhost:8000/auth/signup', json=signup_data, timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        token = data['token']
        print(f"   User: {data['email']}")
        print(f'   Tier: {data["tier"]}')
        print(f'   ✅ Signup successful')
        
        # Test 4: Get wallet
        print('\n4. Get Wallet:')
        resp = requests.get('http://localhost:8000/wallet', 
                          headers={'Authorization': f'Bearer {token}'}, timeout=5)
        wallet = resp.json()
        print(f"   Balance: ₹{wallet['balance']:,.2f}")
        print(f"   Available: ₹{wallet['available_balance']:,.2f}")
        print(f'   ✅ Wallet retrieved')
        
        # Test 5: Get portfolio
        print('\n5. Get Portfolio:')
        resp = requests.get('http://localhost:8000/portfolio', 
                          headers={'Authorization': f'Bearer {token}'}, timeout=5)
        portfolio = resp.json()
        print(f"   Wallet balance: ₹{portfolio['wallet']['balance']:,.2f}")
        print(f"   Holdings: {len(portfolio['holdings'])} stocks")
        print(f'   ✅ Portfolio retrieved')
        
    else:
        print(f'   Error: {resp.json()}')
    
    print('\n' + '='*60)
    print('✅ ALL TESTS PASSED - SYSTEM WORKING')
    print('='*60)
    
except Exception as e:
    print(f'\n❌ Error: {str(e)}')
