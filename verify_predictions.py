#!/usr/bin/env python3
"""
Quick verification: Show exact predictions from each stock (proof they're different)
"""

import requests
import json

API = "http://localhost:8000"

print("\n" + "="*80)
print("🎯 INDIVIDUAL STOCK PREDICTIONS - Verify Each is Unique")
print("="*80 + "\n")

r = requests.get(f"{API}/api/signals/active").json()
signals = r.get("signals", [])

for i, signal in enumerate(signals, 1):
    symbol = signal["symbol"]
    signal_type = signal["signal_type"]
    confidence = signal["confidence"]
    reason = signal["reason"]
    price = signal["price"]
    change = signal["changePercent"]
    
    emoji = "🟢" if signal_type == "BUY" else "🔴"
    
    print(f"{i}. {emoji} {symbol:12} | {signal_type:4} | Conf: {confidence:.2f} ")
    print(f"   Price: ₹{price:8.2f} | Change: {change:+.2f}%")
    print(f"   Reason: {reason}")
    print()

# Summary
signals_buy = len([s for s in signals if s["signal_type"] == "BUY"])
signals_sell = len(signals) - signals_buy
confidences = [s["confidence"] for s in signals]

print("="*80)
print("📊 SUMMARY")
print("="*80)
print(f"BUY Signals:  {signals_buy}/8")
print(f"SELL Signals: {signals_sell}/8")
print(f"Confidence Range: {min(confidences):.2f} - {max(confidences):.2f}")
print(f"Average: {sum(confidences)/len(confidences):.2f}")

if len(set(s["signal_type"] for s in signals)) > 1 and max(confidences) - min(confidences) > 0.05:
    print("\n✅ PREDICTIONS ARE DIVERSE - Fix Working!\n")
else:
    print("\n❌ Predictions still too similar\n")
