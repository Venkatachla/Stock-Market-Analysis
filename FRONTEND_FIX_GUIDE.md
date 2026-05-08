# FRONTEND REAL-TIME UPDATE FIX

## PROBLEM: Frontend polls every 30 seconds
**File:** `frontend/src/pages/StockDetail.tsx`

**Current (SLOW):**
```typescript
const { data: stock } = usePolling<StockSignal>(
  pollStockDetail,
  30000  // 30 seconds = 30,000ms
);
```

**Result:** Prices update every 30s, not real-time

---

## SOLUTION: Change polling interval to 5-10 seconds

### Option 1: Update polling interval in StockDetail.tsx

Find this section:
```typescript
const pollStockDetail = useCallback(
  () => fetchStockDetail(symbol!),
  [symbol]
);

const { data: stock } = usePolling<StockSignal>(
  pollStockDetail,
  30000  // ← CHANGE THIS
);
```

Replace with:
```typescript
const pollStockDetail = useCallback(
  () => fetchStockDetail(symbol!),
  [symbol]
);

const { data: stock } = usePolling<StockSignal>(
  pollStockDetail,
  10000  // 10 seconds for better real-time feel
);
```

---

### Option 2: Use /predict-live endpoint (RECOMMENDED)

Replace the stockDetail fetch with the new live endpoint:

```typescript
const pollStockDetail = useCallback(async () => {
  try {
    // Use the new FIXED endpoint with pure ML confidence
    const response = await fetch(
      `${import.meta.env.VITE_API_URL}/predict-live/${symbol}`
    );
    if (!response.ok) throw new Error('Failed to fetch');
    
    const data = await response.json();
    
    // Transform backend response to StockSignal format
    return {
      symbol: data.symbol,
      name: data.symbol,
      price: data.latest_price,
      change: 0,  // Calculate from entry_price if needed
      changePercent: 0,
      signal: data.signal,
      confidence: data.confidence_score / 100,  // Convert to 0-1
      volume: 0,
      timestamp: data.timestamp,
      news_sentiment: data.news_sentiment_label
    } as StockSignal;
  } catch (error) {
    console.error('Prediction error:', error);
    return null;
  }
}, [symbol]);

// Fetch every 10 seconds for near real-time
const { data: stock } = usePolling<StockSignal>(
  pollStockDetail,
  10000  // 10 seconds
);
```

---

## FRONTEND METRICS DISPLAY FIX

### Show confidence as percentage (0-100)

**Current (WRONG):**
```typescript
<span className="text-lg font-semibold">
  {(stock.confidence * 100).toFixed(0)}%  // Shows as 0-100%
</span>
```

**Expected with fix:**
```
78%  ← Pure ML probability, varies per stock
45%  ← Lower confidence for uncertain stock
92%  ← High confidence prediction
```

---

## FRONTEND API SERVICE UPDATE

### Update `frontend/src/services/api.ts`:

Add new service function:

```typescript
/**
 * Fetch FIXED live prediction with pure ML confidence
 */
export async function fetchLivePrediction(symbol: string): Promise<any> {
  const response = await fetch(
    `${API_URL}/predict-live/${symbol}`
  );
  if (!response.ok) throw new Error(`Failed to fetch prediction for ${symbol}`);
  
  const data = await response.json();
  
  return {
    symbol: data.symbol,
    price: data.latest_price,
    confidence: data.confidence_score / 100,  // Convert to 0-1
    signal: data.signal,
    timestamp: new Date(data.timestamp),
    news_sentiment: data.news_sentiment_label,
    news_score: data.news_sentiment_score,
    regime: data.regime,
    rsi: data.rsi,
    sma50: data.sma_50,
    sma200: data.sma_200,
  };
}

/**
 * Batch live predictions
 */
export async function fetchBatchLive(symbols: string[]): Promise<any[]> {
  const response = await fetch(
    `${API_URL}/batch-live?symbols=${symbols.join(',')}`
  );
  if (!response.ok) throw new Error('Failed to fetch batch predictions');
  
  const data = await response.json();
  return data.predictions || [];
}
```

---

## TESTING THE FIX

### Test 1: Check confidence varies per stock

```bash
curl http://localhost:8000/predict-live/RELIANCE
curl http://localhost:8000/predict-live/TCS
curl http://localhost:8000/predict-live/INFY
```

**Expected:**
- RELIANCE: `"confidence_score": 78.5` (not 50%)
- TCS: `"confidence_score": 42.1` (different per stock)
- INFY: `"confidence_score": 89.3` (different per stock)

### Test 2: Confidence NOT affected by news

Check same stock at different times:
```bash
# First call
curl http://localhost:8000/predict-live/RELIANCE
# Response: "confidence_score": 78.5

# Wait, news changes
# Second call
curl http://localhost:8000/predict-live/RELIANCE
# Response: "confidence_score": 78.5 (same, because ML model unchanged)
```

**Expected:** Confidence stays constant. Only `news_sentiment_score` changes.

### Test 3: Prices update dynamically

Hit the endpoint 3 times in quick succession:

```bash
curl http://localhost:8000/predict-live/RELIANCE
sleep 2
curl http://localhost:8000/predict-live/RELIANCE
sleep 2
curl http://localhost:8000/predict-live/RELIANCE
```

**Expected:** 
- Timestamps differ by ~2s
- Prices might change (real market movement)
- Confidence might change slightly (fresh feature computation)

### Test 4: Separate news signal

```bash
curl http://localhost:8000/predict-live/RELIANCE | jq '{
  confidence_score,
  signal,
  news_sentiment_score,
  news_sentiment_label
}'
```

**Expected Output:**
```json
{
  "confidence_score": 78.5,
  "signal": "BUY",
  "news_sentiment_score": -0.15,
  "news_sentiment_label": "NEGATIVE"
}
```

Notice:
- Confidence=78.5 → BUY signal (confidence driven)
- But News=NEGATIVE (separate, informational)
- Not mixed together!

---

## VERIFICATION CHECKLIST

- [ ] Endpoint returns fresh data (timestamps change)
- [ ] Confidence varies 0-100 per stock (not constant 50%)
- [ ] Confidence NOT affected by news headlines
- [ ] News score is separate field
- [ ] Frontend polls every 10s (not 30s)
- [ ] Multiple stocks show different confidences
- [ ] Confidence is pure model probability (0.5 = 50%, 0.78 = 78%)

---

## ROLLOUT STEPS

1. Add `/predict-live/{symbol}` endpoint to `api/app.py` ✅
2. Update `frontend/src/pages/StockDetail.tsx` polling interval to 10s
3. Update `frontend/src/services/api.ts` to use new endpoint
4. Test with manual curl requests
5. Monitor system behavior
6. Keep old endpoints for backward compatibility

---

## KEY DIFFERENCES FROM OLD SYSTEM

| Aspect | Old | Fixed |
|--------|-----|-------|
| **Confidence** | Mixed signal (50-85%) | Pure ML probability (0-100%) |
| **News** | In confidence calculation | Separate signal |
| **Data** | Cached/static | Fresh every request |
| **Poll interval** | 30 seconds | 10 seconds |
| **Timestamp** | Sometimes stale | Always current |
| **Signal** | Complex rules | Confidence threshold (65/35) |

---

## EXPECTED RESULTS AFTER FIX

### Before:
```json
{
  "symbol": "RELIANCE",
  "confidence": 0.62,  // Looks like all stocks have ~60%
  "timestamp": "2026-04-29T10:00:00",  // Old timestamp
  "signal": "WEAK BUY"  // Complex signal
}
```

### After:
```json
{
  "symbol": "RELIANCE",
  "confidence_score": 78.5,  // Varies per stock (0-100)
  "probability_up": 0.785,
  "signal": "BUY",  // Simple: BUY/SELL/NEUTRAL
  "news_sentiment_score": -0.15,  // Separate
  "timestamp": "2026-04-29T12:34:56.789012",  // Fresh
  "regime": "UPTREND"  // Additional context
}
```

---

## ADDITIONAL ENHANCEMENTS

### Add confidence gauge to UI

```tsx
<div className="confidence-gauge">
  <div className="gauge-container">
    <div 
      className="gauge-fill" 
      style={{
        width: `${stock.confidence * 100}%`,
        backgroundColor: stock.confidence >= 0.65 ? '#22c55e' : stock.confidence <= 0.35 ? '#ef4444' : '#f59e0b'
      }}
    />
  </div>
  <span className="text-sm">{(stock.confidence * 100).toFixed(1)}%</span>
</div>
```

### Show news sentiment separately

```tsx
<div className="news-section">
  <h4>Market Sentiment</h4>
  <span className={`sentiment-${stock.news_sentiment_label.toLowerCase()}`}>
    {stock.news_sentiment_label}: {stock.news_sentiment_score > 0 ? '+' : ''}{stock.news_sentiment_score.toFixed(2)}
  </span>
</div>
```

---
