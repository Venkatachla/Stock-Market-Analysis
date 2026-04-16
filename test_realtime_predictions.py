#!/usr/bin/env python3
"""
🧪 REAL-TIME PREDICTION TESTING - Verify dynamic signals update every time

Run: python test_realtime_predictions.py
"""

import requests
import json
import time
from datetime import datetime
import sys

API_BASE = "http://localhost:8000"

# Colors for terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(title):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}🔍 {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

def test_realtime_updates():
    """Fetch predictions 3 times and show how they change"""
    print_header("REAL-TIME PREDICTION TEST")
    
    predictions = []
    
    try:
        # Fetch 3 times to show changes
        for iteration in range(3):
            print(f"{BOLD}📊 Fetch #{iteration+1} at {datetime.now().strftime('%H:%M:%S')}{RESET}")
            
            response = requests.get(f"{API_BASE}/api/signals/active", timeout=10)
            
            if response.status_code != 200:
                print(f"{RED}❌ Error: {response.status_code}{RESET}\n")
                continue
            
            data = response.json()
            signals = data.get("signals", [])
            
            print(f"✅ Retrieved {len(signals)} signals\n")
            
            # Show first 3 stocks
            for i, signal in enumerate(signals[:3]):
                symbol = signal.get("symbol", "?")
                signal_type = signal.get("signal_type", "?")
                confidence = signal.get("confidence", 0)
                reason = signal.get("reason", "")
                price = signal.get("price", 0)
                change = signal.get("changePercent", 0)
                
                print(f"  {symbol:12} | {signal_type:4} | Conf: {confidence:.2f} | ₹{price:8.2f} ({change:+.2f}%)")
                print(f"  └─ Reason: {reason}")
            
            print()
            predictions.append({
                "timestamp": datetime.now().isoformat(),
                "signals": signals
            })
            
            # Wait before next fetch
            if iteration < 2:
                print(f"{YELLOW}⏳ Waiting 10 seconds...{RESET}")
                for i in range(10, 0, -1):
                    print(f"\r  {i}s ", end="", flush=True)
                    time.sleep(1)
                print("\n")
        
        # Compare predictions
        print_header("COMPARISON: What Changed?")
        
        changed_count = 0
        
        for stock_idx in range(len(predictions[0]["signals"])):
            symbol = predictions[0]["signals"][stock_idx]["symbol"]
            
            signal1 = predictions[0]["signals"][stock_idx]
            signal2 = predictions[1]["signals"][stock_idx]
            signal3 = predictions[2]["signals"][stock_idx]
            
            # Check if changed
            if (signal1["signal_type"] != signal2["signal_type"] or 
                signal1["confidence"] != signal2["confidence"] or
                signal1["price"] != signal2["price"]):
                
                print(f"{GREEN}✅ {symbol:12} - UPDATED{RESET}")
                print(f"  Fetch #1: {signal1['signal_type']} ({signal1['confidence']:.2f}) - ₹{signal1['price']:.2f}")
                print(f"  Fetch #2: {signal2['signal_type']} ({signal2['confidence']:.2f}) - ₹{signal2['price']:.2f}")
                print(f"  Fetch #3: {signal3['signal_type']} ({signal3['confidence']:.2f}) - ₹{signal3['price']:.2f}")
                print()
                changed_count += 1
            else:
                print(f"{YELLOW}⚠️  {symbol:12} - No change (still {signal1['signal_type']}){RESET}\n")
        
        print_header("TEST RESULTS")
        
        if changed_count > 0:
            print(f"{GREEN}✅ SUCCESS! {changed_count} stocks updated dynamically{RESET}")
            print(f"\n✨ Real-time prediction engine is WORKING!\n")
            return True
        else:
            print(f"{RED}❌ FAILED - No predictions changed!{RESET}")
            print(f"\n⚠️  Predictions appear to be static (not dynamic)\n")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Cannot connect to backend at {API_BASE}{RESET}")
        print(f"   Make sure backend is running: python -m uvicorn api.app_simple:app --host 127.0.0.1 --port 8000\n")
        return False
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}\n")
        return False

def test_signal_variety():
    """Check if we have both BUY and SELL signals"""
    print_header("SIGNAL VARIETY TEST")
    
    try:
        response = requests.get(f"{API_BASE}/api/signals/active", timeout=10)
        data = response.json()
        signals = data.get("signals", [])
        
        buy_count = len([s for s in signals if s["signal_type"] == "BUY"])
        sell_count = len([s for s in signals if s["signal_type"] == "SELL"])
        
        print(f"🟢 BUY signals:  {buy_count}/8")
        print(f"🔴 SELL signals: {sell_count}/8\n")
        
        if buy_count > 0 and sell_count > 0:
            print(f"{GREEN}✅ Mix of BUY and SELL signals - Good!{RESET}\n")
            return True
        elif buy_count == 0 and sell_count == 0:
            print(f"{RED}❌ No signals at all!{RESET}\n")
            return False
        else:
            print(f"{YELLOW}⚠️  Only one type of signal (needs both){RESET}\n")
            return False
            
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}\n")
        return False

def test_confidence_range():
    """Check if confidence values vary (not all the same)"""
    print_header("CONFIDENCE RANGE TEST")
    
    try:
        response = requests.get(f"{API_BASE}/api/signals/active", timeout=10)
        data = response.json()
        signals = data.get("signals", [])
        
        confidences = [s["confidence"] for s in signals]
        min_conf = min(confidences)
        max_conf = max(confidences)
        avg_conf = sum(confidences) / len(confidences)
        
        print(f"Confidence Range: {min_conf:.2f} - {max_conf:.2f}")
        print(f"Average: {avg_conf:.2f}\n")
        
        if max_conf - min_conf > 0.05:  # At least 0.05 difference
            print(f"{GREEN}✅ Confidence values vary - Dynamic!{RESET}\n")
            return True
        else:
            print(f"{RED}❌ All confidence values are the same!{RESET}\n")
            return False
            
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}\n")
        return False

def main():
    """Run all tests"""
    print(f"\n{BOLD}{CYAN}🧪 REAL-TIME PREDICTION ENGINE TEST SUITE{RESET}\n")
    print(f"Backend: {API_BASE}")
    print(f"Time: {datetime.now().isoformat()}\n")
    
    tests = [
        ("Signal Variety", test_signal_variety),
        ("Confidence Range", test_confidence_range),
        ("Real-Time Updates", test_realtime_updates),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print_header("SUMMARY")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}Real-time prediction engine is working perfectly!{RESET}\n")
        return 0
    else:
        print(f"\n{RED}Some tests failed. Check backend logs for errors.{RESET}\n")
        return 1

if __name__ == "__main__":
    exit(main())
