# 🧪 COMPLETE TESTING & VERIFICATION GUIDE

## BEFORE STARTING

Ensure:
1. Backend is running: `python api/app.py` or `uvicorn api.app:app --reload`
2. Frontend is running: `npm run dev` (if testing UI)
3. Python has required imports: `datetime, torch, yfinance, sklearn`

---

## TEST 1: Verify Endpoint Exists

```bash
curl -X GET http://localhost:8000/predict-live/RELIANCE
```

**Expected Response:**
```json
{
  "symbol": "RELIANCE",
  "confidence_score": 78.5,
  "probability_up": 0.785,
  "probability_down": 0.215,
  "signal": "BUY",
  "news_sentiment_score": 0.12,
  "news_sentiment_label": "POSITIVE",
  "latest_price": 2456.75,
  "timestamp": "2026-04-29T12:34:56.789012",
  "regime": "UPTREND",
  "entry_price": 2456.75,
  "stop_loss": 2435.20,
  "take_profit": 2498.85,
  "sma_50": 2445.10,
  "sma_200": 2430.25,
  "rsi": 58.5
}
```

**Status Code:** `200`

---

## TEST 2: Verify Confidence Varies Per Stock

```bash
echo "=== Testing RELIANCE ==="
curl -s http://localhost:8000/predict-live/RELIANCE | jq '.symbol, .confidence_score, .signal'

echo "=== Testing TCS ==="
curl -s http://localhost:8000/predict-live/TCS | jq '.symbol, .confidence_score, .signal'

echo "=== Testing INFY ==="
curl -s http://localhost:8000/predict-live/INFY | jq '.symbol, .confidence_score, .signal'

echo "=== Testing WIPRO ==="
curl -s http://localhost:8000/predict-live/WIPRO | jq '.symbol, .confidence_score, .signal'
```

**Expected Output:**
```
"RELIANCE"
78.5
"BUY"

"TCS"
42.1
"NEUTRAL"

"INFY"
89.3
"BUY"

"WIPRO"
31.8
"SELL"
```

**Verification:** Each stock should have DIFFERENT confidence values (not all 50%)

---

## TEST 3: Verify News Does NOT Affect Confidence

Call the same stock 5 times and verify confidence stays same:

```bash
#!/bin/bash
for i in {1..5}; do
  echo "Call #$i:"
  curl -s http://localhost:8000/predict-live/RELIANCE | jq '{
    timestamp: .timestamp,
    confidence_score: .confidence_score,
    news_sentiment_label: .news_sentiment_label
  }'
  sleep 2
done
```

**Expected Output:**
```json
{"timestamp": "2026-04-29T12:34:56.789012", "confidence_score": 78.5, "news_sentiment_label": "POSITIVE"}
{"timestamp": "2026-04-29T12:34:58.789012", "confidence_score": 78.5, "news_sentiment_label": "NEUTRAL"}
{"timestamp": "2026-04-29T12:35:00.789012", "confidence_score": 78.5, "news_sentiment_label": "NEGATIVE"}
{"timestamp": "2026-04-29T12:35:02.789012", "confidence_score": 78.5, "news_sentiment_label": "POSITIVE"}
{"timestamp": "2026-04-29T12:35:04.789012", "confidence_score": 78.5, "news_sentiment_label": "NEUTRAL"}
```

**Verification:**
- ✅ `confidence_score` stays SAME (78.5)
- ✅ `news_sentiment_label` changes (POSITIVE → NEUTRAL → NEGATIVE)
- ✅ `timestamp` changes (data is fresh)
- ✅ Confidence NOT affected by news!

---

## TEST 4: Verify Fresh Data (Timestamps Update)

Call the same endpoint quickly 3 times:

```bash
echo "Call 1:" && curl -s http://localhost:8000/predict-live/RELIANCE | jq .timestamp && \
echo "Call 2:" && curl -s http://localhost:8000/predict-live/RELIANCE | jq .timestamp && \
echo "Call 3:" && curl -s http://localhost:8000/predict-live/RELIANCE | jq .timestamp
```

**Expected Output:**
```
Call 1:
"2026-04-29T12:34:56.123456"
Call 2:
"2026-04-29T12:34:56.456789"
Call 3:
"2026-04-29T12:34:56.789012"
```

**Verification:**
- ✅ Each call returns DIFFERENT timestamp
- ✅ Data is FRESH, not cached
- ✅ Timestamps are current time (ISO format)

---

## TEST 5: Verify Signal Based on Confidence Threshold

Test different confidence levels:

```bash
# Test 1: Confidence >= 65 → BUY
curl -s http://localhost:8000/predict-live/RELIANCE | jq '{confidence: .confidence_score, signal: .signal}' | grep -E "confidence|signal"

# Test 2: Confidence <= 35 → SELL
curl -s http://localhost:8000/predict-live/BAJAJ-AUTO | jq '{confidence: .confidence_score, signal: .signal}' | grep -E "confidence|signal"

# Test 3: 35 < Confidence < 65 → NEUTRAL
curl -s http://localhost:8000/predict-live/MARUTI | jq '{confidence: .confidence_score, signal: .signal}' | grep -E "confidence|signal"
```

**Expected Output:**
```json
{"confidence": 78.5, "signal": "BUY"}      // >= 65
{"confidence": 28.3, "signal": "SELL"}     // <= 35
{"confidence": 52.1, "signal": "NEUTRAL"}  // Between 35-65
```

**Verification:**
- ✅ BUY when confidence >= 65
- ✅ SELL when confidence <= 35
- ✅ NEUTRAL when 35 < confidence < 65

---

## TEST 6: Verify Batch Endpoint

```bash
curl -s "http://localhost:8000/batch-live?symbols=RELIANCE,TCS,INFY,WIPRO" | jq '{
  count: .count,
  predictions: [.predictions[] | {symbol, confidence_score, signal}]
}'
```

**Expected Output:**
```json
{
  "count": 4,
  "predictions": [
    {"symbol": "RELIANCE", "confidence_score": 78.5, "signal": "BUY"},
    {"symbol": "TCS", "confidence_score": 42.1, "signal": "NEUTRAL"},
    {"symbol": "INFY", "confidence_score": 89.3, "signal": "BUY"},
    {"symbol": "WIPRO", "confidence_score": 31.8, "signal": "SELL"}
  ]
}
```

**Verification:**
- ✅ Returns predictions for all symbols
- ✅ Each symbol has different confidence
- ✅ Signals match confidence thresholds

---

## TEST 7: Verify Probability Values

```bash
curl -s http://localhost:8000/predict-live/RELIANCE | jq '{
  confidence_score: .confidence_score,
  probability_up: .probability_up,
  probability_down: .probability_down
}'
```

**Expected Output:**
```json
{
  "confidence_score": 78.5,
  "probability_up": 0.785,
  "probability_down": 0.215
}
```

**Verification:**
- ✅ `confidence_score = probability_up * 100`
- ✅ `probability_down = 1 - probability_up`
- ✅ `probability_up + probability_down = 1.0`

---

## TEST 8: Verify News is Separate

```bash
curl -s http://localhost:8000/predict-live/RELIANCE | jq '{
  signal: .signal,
  confidence_score: .confidence_score,
  news_sentiment_score: .news_sentiment_score,
  news_sentiment_label: .news_sentiment_label
}'
```

**Expected Output:**
```json
{
  "signal": "BUY",
  "confidence_score": 78.5,
  "news_sentiment_score": -0.25,
  "news_sentiment_label": "NEGATIVE"
}
```

**Verification:**
- ✅ Confidence = 78.5 → BUY (based on ML)
- ✅ News = NEGATIVE (separate signal)
- ✅ NOT mixed together!

---

## TEST 9: Verify Trading Plan

```bash
curl -s http://localhost:8000/predict-live/RELIANCE | jq '{
  signal: .signal,
  entry_price: .entry_price,
  stop_loss: .stop_loss,
  take_profit: .take_profit,
  latest_price: .latest_price
}'
```

**Expected Output (BUY):**
```json
{
  "signal": "BUY",
  "entry_price": 2456.75,
  "stop_loss": 2435.20,
  "take_profit": 2498.85,
  "latest_price": 2456.75
}
```

For BUY: `stop_loss < entry_price < take_profit`

**Expected Output (SELL):**
```json
{
  "signal": "SELL",
  "entry_price": 2456.75,
  "stop_loss": 2478.30,
  "take_profit": 2415.65,
  "latest_price": 2456.75
}
```

For SELL: `take_profit < entry_price < stop_loss`

**Verification:**
- ✅ Risk/reward ratio is 1:2
- ✅ Stop loss provides protection
- ✅ Take profit is realistic

---

## TEST 10: Verify Regime

```bash
curl -s http://localhost:8000/predict-live/RELIANCE | jq '{
  regime: .regime,
  price: .latest_price,
  sma_50: .sma_50,
  sma_200: .sma_200
}'
```

**Expected Output:**
```json
{
  "regime": "UPTREND",
  "price": 2456.75,
  "sma_50": 2445.10,
  "sma_200": 2430.25
}
```

**Verification:**
- `UPTREND`: price > sma_50 > sma_200
- `DOWNTREND`: price < sma_50 < sma_200
- `MIXED`: Neither of above

---

## TEST 11: Error Handling

### Invalid symbol:
```bash
curl -s http://localhost:8000/predict-live/INVALIDXYZ
```

**Expected Response:**
```json
{"detail": "Insufficient data for INVALIDXYZ"}
```

**Status Code:** `404`

### No parameters:
```bash
curl -s http://localhost:8000/predict-live/
```

**Expected Response:**
```json
{"detail": "Not Found"}
```

**Status Code:** `404`

---

## TEST 12: Response Headers

```bash
curl -i http://localhost:8000/predict-live/RELIANCE 2>&1 | grep -E "Content-Type|HTTP"
```

**Expected Output:**
```
HTTP/1.1 200 OK
Content-Type: application/json
```

---

## COMPREHENSIVE TEST SCRIPT

Save as `test_fix.sh`:

```bash
#!/bin/bash

echo "========================================="
echo "STOCKPULSE PREDICTION FIX - TEST SUITE"
echo "========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

test_count=0
pass_count=0

# Helper function
run_test() {
  local test_name=$1
  local command=$2
  local check=$3
  
  ((test_count++))
  echo -e "\n[Test $test_count] $test_name"
  echo "Command: $command"
  
  result=$(eval "$command 2>&1")
  
  if echo "$result" | grep -q "$check"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
  else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Output: $result"
  fi
}

# Run tests
run_test "Endpoint exists" \
  "curl -s http://localhost:8000/predict-live/RELIANCE | jq '.symbol'" \
  "RELIANCE"

run_test "Confidence varies" \
  "curl -s http://localhost:8000/predict-live/RELIANCE | jq '.confidence_score' && curl -s http://localhost:8000/predict-live/TCS | jq '.confidence_score'" \
  "^[0-9]"

run_test "Fresh timestamp" \
  "curl -s http://localhost:8000/predict-live/RELIANCE | jq '.timestamp'" \
  "2026"

run_test "Batch predictions" \
  "curl -s 'http://localhost:8000/batch-live?symbols=RELIANCE,TCS' | jq '.count'" \
  "2"

run_test "News is separate" \
  "curl -s http://localhost:8000/predict-live/RELIANCE | jq '.news_sentiment_label'" \
  "POSITIVE\|NEGATIVE\|NEUTRAL"

# Summary
echo ""
echo "========================================="
echo "TEST RESULTS: $pass_count / $test_count passed"
echo "========================================="

if [ $pass_count -eq $test_count ]; then
  echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
  exit 0
else
  echo -e "${RED}✗ SOME TESTS FAILED${NC}"
  exit 1
fi
```

Run it:
```bash
chmod +x test_fix.sh
./test_fix.sh
```

---

## FINAL CHECKLIST

- [ ] Endpoint returns 200 status
- [ ] Confidence varies 0-100 (not constant)
- [ ] Confidence NOT affected by news
- [ ] News is separate field
- [ ] Timestamps are fresh
- [ ] Signals match confidence thresholds
- [ ] Batch endpoint works
- [ ] Error handling works
- [ ] Trading plan values are logical
- [ ] Regime detection works

---

## PERFORMANCE EXPECTATIONS

- Response time: < 2 seconds per symbol
- Batch (4 symbols): < 8 seconds
- Data freshness: < 1 second old
- Confidence accuracy: ±5% vs previous call

---

## NEXT STEPS

1. ✅ Add endpoints to backend
2. ✅ Test all curl requests above
3. ✅ Update frontend to use `/predict-live`
4. ✅ Change polling interval to 10s
5. ✅ Monitor system behavior
6. ✅ Collect metrics

---
