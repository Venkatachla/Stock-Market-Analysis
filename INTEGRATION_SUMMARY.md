# What We Built - Complete Summary

## Backend: FastAPI Inference Server (`api/server.py`)
- **Purpose**: Serves ML model predictions for any NSE stock
- **How it works**:
  1. Accepts stock symbol (e.g., RELIANCE)
  2. Downloads 2 years of OHLCV data from Yahoo Finance
  3. Computes 19 technical features (RSI, MACD, SMAs, Bollinger Bands, ATR, volatility, etc.)
  4. Loads trained ensemble models:
     - `models/tree_models.pkl` (XGBoost, LightGBM, RandomForest, Scaler)
     - `models/lstm.pt` (LSTM neural network)
  5. Computes per-model probabilities and combines them with weights:
     - XGBoost: 40%
     - LightGBM: 30%
     - RandomForest: 20%
     - LSTM: 10%
  6. Returns ensemble probability (prob_up, prob_down) + individual model scores

- **Endpoints**:
  - `GET /health` - Check API health
  - `GET /predict?symbol=RELIANCE` - Single stock prediction
  - `POST /predict` - Batch predictions (JSON: { "symbols": [...] })

- **Error handling**: Gracefully falls back if Yahoo Finance is rate-limited or data is insufficient

## Frontend: Simple React UI (`frontend/src/pages/Predictor.tsx`)
- **Purpose**: Search bar for any NSE stock + display model predictions
- **Features**:
  - Beautiful dark UI with gradient design
  - Search input for stock symbols
  - Real-time API calls to backend
  - Displays:
    - Main signal (BULLISH/BEARISH/NEUTRAL)
    - Probability bars (up vs down)
    - Individual model scores (XGB, LGBM, RF, LSTM)
    - Data freshness (as of date)
  - Error handling for API failures

- **Integration**:
  - `frontend/.env` - Set `VITE_API_URL=http://localhost:8000`
  - `frontend/src/App.tsx` - Routes to Predictor as homepage
  - Uses React Query for async data fetching

## How to Run (2 terminals)

### Terminal 1: Start Backend API
```bash
cd C:\Users\magan\OneDrive\Desktop\STCOK
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```
Output: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 2: Start Frontend
```bash
cd C:\Users\magan\OneDrive\Desktop\STCOK\frontend
npm install   # (if not done)
npm run dev
```
Output: Local URL like `http://localhost:5173`

## User Workflow
1. Open http://localhost:5173 in browser
2. Type stock symbol: RELIANCE, TCS, INFY, WIPRO, etc.
3. Click Search or press Enter
4. See predictions:
   - **Prob Up**: Likelihood stock goes up tomorrow (from ensemble)
   - **Prob Down**: Likelihood stock goes down tomorrow
   - Model breakdown shows how confident each model is (helps understand consensus)

## Data Flow
```
User Types "RELIANCE"
    ↓
Frontend calls GET /predict?symbol=RELIANCE
    ↓
Backend API:
  - Fetches 2 years OHLCV from Yahoo Finance
  - Computes 19 technical features
  - Loads models from disk
  - Runs predictions through ensemble
    ↓
Returns: {
  symbol: "RELIANCE",
  prob_up: 0.62,           // 62% chance up
  prob_down: 0.38,         // 38% chance down
  detail: {
    xgb: 0.58,
    lgbm: 0.65,
    rf: 0.62,
    lstm: 0.68
  },
  rows_used: 504,
  asof: "2026-03-12"
}
    ↓
Frontend displays beautiful UI with probability bars
```

## Files Modified/Created
1. **New**: `api/server.py` - FastAPI inference server
2. **New**: `api/__init__.py` - Package marker
3. **New**: `frontend/src/pages/Predictor.tsx` - Search UI
4. **New**: `SETUP.md` - Quick start guide
5. **Modified**: `frontend/src/App.tsx` - Routes to Predictor, disabled chat
6. **Modified**: `frontend/.env` - Added VITE_API_URL
7. **Modified**: `requirements.txt` - Added fastapi, uvicorn
8. **Modified**: `frontend/README.md` - Backend+Frontend instructions

## Features & Notes
- **0 Database required** - Everything is in-memory. If you provide MongoDB ID later, we can add persistence.
- **No authentication** - API is open and calls Yahoo freely
- **Graceful fallback** - If Yahoo blocks, API returns error (frontend shows friendly message)
- **Real predictions** - Using actual trained models on 10 years of NSE data with ~200+ tickers
- **Fast inference** - Each prediction ~1-2 seconds once Yahoo data is downloaded (cached)
- **Batch support** - Can query multiple symbols in one call

## Next Steps (Optional)
1. **MongoDB Integration**: Store predictions/history for trending/watchlist
2. **All NSE Symbols**: Load full symbol list, let users browse/filter
3. **Real-time Updates**: WebSocket for live quote streaming
4. **Portfolio Tracking**: Save favorite symbols, compare with predictions
5. **Alerts**: Notify when prediction crosses certain thresholds
