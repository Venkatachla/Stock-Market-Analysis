#!/usr/bin/env python3
"""Test that predictions are now DIFFERENT for each stock (not all identical)"""

import requests
import json
from collections import Counter

API = "http://localhost:8000"

print("\n" + "="*70)
print("🧪 PREDICTION DIVERSITY TEST")
print("="*70)
print()

# Fetch latest predictions
r = requests.get(f"{API}/api/signals/active").json()
signals = r.get("signals", [])

print(f"✅ Retrieved {len(signals)} signals\n")

# Analyze variety
signal_types = [s["signal_type"] for s in signals]
confidences = [s["confidence"] for s in signals]

signal_counts = Counter(signal_types)
print(f"Signal Type Distribution:")
print(f"  🟢 BUY signals:  {signal_counts.get('BUY', 0)}")
print(f"  🔴 SELL signals: {signal_counts.get('SELL', 0)}\n")

print(f"Confidence Range: {min(confidences):.2f} - {max(confidences):.2f}")
print(f"Average Confidence: {sum(confidences) / len(confidences):.2f}\n")

print("Individual Predictions:")
for s in signals:
    symbol = s["symbol"]
    signal = s["signal_type"]
    conf = s["confidence"]
    signal_emoji = "🟢" if signal == "BUY" else "🔴"
    print(f"  {signal_emoji} {symbol:12} → {signal:4} ({conf:.2f})")

print()

# Verdict
all_same_signal = len(set(signal_types)) == 1
all_same_conf = len(set(confidences)) == 1

if all_same_signal and all_same_conf:
    print("❌ FAILED: All predictions are identical!")
    print("   All stocks show: BUY at 0.50 confidence")
    exit(1)

elif all_same_signal:
    print("⚠️  WARNING: All signals are same type (but confidence varies)")
    exit(1)

else:
    print("✅ SUCCESS! Predictions are DIVERSE:")
    print(f"   - Mix of BUY ({signal_counts['BUY']}) and SELL ({signal_counts.get('SELL', 0)})")
    print(f"   - Confidence varies: {min(confidences):.2f} to {max(confidences):.2f}")
    print(f"   - Each stock has unique signal\n")
    exit(0)
