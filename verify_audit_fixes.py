#!/usr/bin/env python3
"""
StockPulse Audit Validation Script
Checks if critical bugs have been fixed
"""

import sqlite3
import ast
import os
from pathlib import Path


def check_database_commits():
    """Check if get_db() has commit statement"""
    print("\n[1/5] Checking Database Commits...")
    
    with open('api/models.py', 'r') as f:
        content = f.read()
    
    if 'db.commit()' in content and 'def get_db()' in content:
        # Check if commit is after yield
        lines = content.split('\n')
        in_get_db = False
        has_commit = False
        
        for i, line in enumerate(lines):
            if 'def get_db()' in line:
                in_get_db = True
            if in_get_db and 'db.commit()' in line:
                has_commit = True
                break
            if in_get_db and 'def ' in line and 'get_db' not in line:
                break
        
        if has_commit:
            print("✅ PASS: db.commit() found in get_db()")
            return True
    
    print("❌ FAIL: db.commit() missing from get_db()")
    return False


def check_wallet_model():
    """Check if Wallet model has required fields"""
    print("[2/5] Checking Wallet Model...")
    
    with open('api/models.py', 'r') as f:
        content = f.read()
    
    wallet_class = content[content.find('class Wallet'):content.find('class Holding')]
    
    has_balance = 'balance' in wallet_class
    has_available = 'available_balance' in wallet_class
    has_used = 'used_balance' in wallet_class
    
    if has_balance and (has_available or has_used):
        print("✅ PASS: Wallet model has required fields")
        return True
    
    if has_balance and not (has_available or has_used):
        print("⚠️  PARTIAL: Wallet only has 'balance' field")
        print("   Option A: Add available_balance and used_balance columns")
        print("   Option B: Remove from WalletResponse model")
        return True  # Acceptable if response also updated
    
    print("❌ FAIL: Wallet model fields missing")
    return False


def check_wallet_response():
    """Check if WalletResponse matches Wallet model"""
    print("[3/5] Checking WalletResponse Fields...")
    
    with open('api/routes.py', 'r') as f:
        content = f.read()
    
    response_class = content[content.find('class WalletResponse'):content.find('class HoldingResponse')]
    
    has_balance = 'balance' in response_class
    has_available = 'available_balance' in response_class
    has_used = 'used_balance' in response_class
    
    # Check if fields exist in Wallet model
    with open('api/models.py', 'r') as f:
        model_content = f.read()
    
    wallet_class = model_content[model_content.find('class Wallet'):model_content.find('class Holding')]
    wallet_has_available = 'available_balance' in wallet_class
    wallet_has_used = 'used_balance' in wallet_class
    
    if (not has_available and not has_used) or (wallet_has_available and wallet_has_used):
        print("✅ PASS: WalletResponse fields match Wallet model")
        return True
    
    print("❌ FAIL: WalletResponse fields don't match Wallet model")
    print(f"   Model has: balance{', available_balance' if wallet_has_available else ''}{', used_balance' if wallet_has_used else ''}")
    print(f"   Response expects: balance{', available_balance' if has_available else ''}{', used_balance' if has_used else ''}")
    return False


def check_buy_endpoint():
    """Check if buy endpoint has db.commit()"""
    print("[4/5] Checking Buy Endpoint Commit...")
    
    with open('api/routes.py', 'r') as f:
        lines = f.readlines()
    
    # Find @router.post("/trading/buy")
    in_buy = False
    has_commit = False
    brace_count = 0
    
    for i, line in enumerate(lines):
        if '@router.post("/trading/buy")' in line:
            in_buy = True
            start_line = i
        
        if in_buy:
            if 'def buy_stock' in line:
                # Count braces to find end of function
                brace_start = i
            
            if 'db.commit()' in line and in_buy:
                has_commit = True
            
            # Check if we've reached a return statement near the end
            if 'return {' in line and in_buy:
                # Check if commit appears before this return
                check_lines = lines[start_line:i+5]
                if any('db.commit()' in l for l in check_lines):
                    has_commit = True
    
    if has_commit:
        print("✅ PASS: buy_stock() has db.commit()")
        return True
    
    print("❌ FAIL: buy_stock() missing db.commit()")
    return False


def check_portfolio_endpoint():
    """Check if portfolio endpoint computes holding properties"""
    print("[5/5] Checking Portfolio Endpoint...")
    
    with open('api/routes.py', 'r') as f:
        content = f.read()
    
    portfolio_func = content[content.find('def get_portfolio'):content.find('def get_transactions')]
    
    # Check for computed properties
    computes_price = 'get_stock_price' in portfolio_func
    computes_investment = 'total_investment' in portfolio_func and '*' in portfolio_func
    computes_pnl = 'pnl' in portfolio_func
    
    if computes_price and computes_investment and computes_pnl:
        print("✅ PASS: Portfolio endpoint computes holding properties")
        return True
    
    print("❌ FAIL: Portfolio endpoint doesn't compute properties properly")
    if not computes_price:
        print("   Missing: current_price computation")
    if not computes_investment:
        print("   Missing: total_investment computation")
    if not computes_pnl:
        print("   Missing: P&L computation")
    return False


def check_refund_function():
    """Check if refund_to_wallet function exists"""
    print("\n[BONUS] Checking Refund Function...")
    
    try:
        with open('api/db_utils.py', 'r') as f:
            content = f.read()
        
        if 'def refund_to_wallet' in content:
            print("✅ PASS: refund_to_wallet() function exists")
            return True
    except:
        pass
    
    print("⚠️  INFO: refund_to_wallet() not found (optional)")
    return True  # Not critical


def run_audit():
    """Run all checks"""
    print("=" * 60)
    print("StockPulse System - Audit Validation Script")
    print("=" * 60)
    
    results = []
    
    # Run checks
    results.append(("Database Commits", check_database_commits()))
    results.append(("Wallet Model", check_wallet_model()))
    results.append(("Wallet Response", check_wallet_response()))
    results.append(("Buy Endpoint", check_buy_endpoint()))
    results.append(("Portfolio Endpoint", check_portfolio_endpoint()))
    check_refund_function()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - System is fixed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} issues remaining")
        return 1


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    exit(run_audit())
