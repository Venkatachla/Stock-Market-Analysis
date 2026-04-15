# Veeeee ML Trading System - Setup & Run Guide

## Quick Start (2 terminals)

### Terminal 1: Start Backend API
```bash
cd C:\Users\magan\OneDrive\Desktop\STCOK
pip install -r requirements.txt
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```
You should see: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 2: Start Frontend
```bash
cd C:\Users\magan\OneDrive\Desktop\STCOK\frontend
npm install
npm run dev
```
You should see: `Local: http://localhost:5173/`

## How to Use
1. Open http://localhost:5173 in your browser
2. Type any NSE stock symbol (e.g., RELIANCE, TCS, HDFCBANK, INFY, WIPRO)
3. Click "Search" or press Enter
4. View the predictions:
   - **Probability Up**: Model predicts stock will go up tomorrow
   - **Probability Down**: Model predicts stock will go down tomorrow
   - **Model Breakdown**: Individual scores from XGBoost, LightGBM, RandomForest, LSTM

## What's Happening Behind the Scenes
1. **Frontend** sends: `GET http://localhost:8000/predict?symbol=RELIANCE`
2. **Backend API** (in `api/server.py`):
   - Downloads 2 years of OHLCV from Yahoo Finance
   - Computes 19 technical features (RSI, MACD, SMAs, Bollinger Bands, etc.)
   - Loads trained models from `models/tree_models.pkl` and `models/lstm.pt`
   - Runs ensemble predictions (40% XGB + 30% LGBM + 20% RF + 10% LSTM)
   - Returns probabilities and per-model scores
3. **Frontend** displays probability bars and model details

## API Endpoints
- `GET http://localhost:8000/health` - Check if API is running
- `GET http://localhost:8000/predict?symbol=RELIANCE` - Single stock prediction
- `POST http://localhost:8000/predict` - Batch predictions (send JSON with `{ "symbols": ["TCS", "HDFCBANK"] }`)

## Notes
- Models were trained on 10 years of NSE data with ~200-300 tickers
- Features include RSI, MACD, SMAs/EMAs, Bollinger Bands, ATR, volatility, momentum
- Target is binary: whether stock goes UP (1) or DOWN (0) next trading day
- Ensemble weights: XGBoost 40%, LightGBM 30%, RandomForest 20%, LSTM 10%
- API calls Yahoo Finance, so internet connection is required
- If Yahoo rate-limits, API returns cached data or error message

## Files Created/Modified
- `api/server.py` - New FastAPI inference server
- `frontend/src/pages/Predictor.tsx` - New simple search UI
- `frontend/src/App.tsx` - Updated routing to show Predictor as homepage
- `frontend/.env` - Added VITE_API_URL
- `requirements.txt` - Added fastapi, uvicorn
