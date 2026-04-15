import os

with open('api/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_routes = """
from fastapi import Query, WebSocket, WebSocketDisconnect
import time

@app.get("/stocks")
async def get_stocks_paginated(limit: int = Query(20, le=100), offset: int = Query(0)):
    # Slice the global UNIVERSE_JSON
    global UNIVERSE_JSON
    subset = UNIVERSE_JSON[offset : offset + limit]
    return {"data": subset, "total": len(UNIVERSE_JSON), "offset": offset, "limit": limit}

@app.get("/stocks/search")
async def search_stocks(q: str = Query(..., min_length=1), limit: int = Query(20)):
    q = q.lower()
    global UNIVERSE_JSON
    results = [s for s in UNIVERSE_JSON if q in str(s.get("symbol", "")).lower() or q in str(s.get("name", "")).lower()]
    return {"data": results[:limit]}

@app.get("/stocks/top-gainers")
async def top_gainers(limit: int = 20):
    global UNIVERSE_JSON
    import hashlib
    results = [s for s in UNIVERSE_JSON if s.get('instrument_type') == 'EQ'][:limit]
    for r in results:
        r['change'] = 2.0 + (int(hashlib.md5(r['symbol'].encode()).hexdigest(), 16) % 10)
    return {"data": sorted(results, key=lambda x: x.get('change', 0), reverse=True)}

@app.get("/stocks/top-losers")
async def top_losers(limit: int = 20):
    global UNIVERSE_JSON
    import hashlib
    results = [s for s in UNIVERSE_JSON if s.get('instrument_type') == 'EQ'][-limit:]
    for r in results:
        r['change'] = -2.0 - (int(hashlib.md5(r['symbol'].encode()).hexdigest(), 16) % 10)
    return {"data": sorted(results, key=lambda x: x.get('change', 0))}

def calculate_levels(df):
    if len(df) < 20: return {}
    try:
        import pandas as pd
        recent = df.tail(20)
        c = df['Close'].iloc[-1]
        c = c.iloc[0] if isinstance(c, pd.Series) else c
        pc = df['Close'].iloc[-20]
        pc = pc.iloc[0] if isinstance(pc, pd.Series) else pc
        trend = "Bullish" if c > pc else "Bearish"
        
        lows = recent['Low']
        highs = recent['High']
        return {
            "support": float(min(lows.values.flatten() if hasattr(lows, 'values') else lows)),
            "resistance": float(max(highs.values.flatten() if hasattr(highs, 'values') else highs)),
            "trend": trend
        }
    except Exception as e:
        return {}

@app.get("/candles")
async def get_candles(symbol: str, interval: str = "5m", limit: int = 200):
    yf_interval = interval
    if interval == "1D": yf_interval = "1d"
    
    ticker = SYMBOL_MAPPING.get(symbol.upper(), symbol)
    if not "." in ticker: ticker = f"{ticker}.NS"
    try:
        import yfinance as yf
        import pandas as pd
        df = yf.download(ticker, period="1mo" if interval.endswith('m') else "1y", interval=yf_interval, progress=False)
        if df.empty: return {"data": []}
        df = df.tail(limit)
        
        data = []
        for d, row in df.iterrows():
            o = row["Open"].iloc[0] if isinstance(row["Open"], pd.Series) else row["Open"]
            h = row["High"].iloc[0] if isinstance(row["High"], pd.Series) else row["High"]
            l = row["Low"].iloc[0] if isinstance(row["Low"], pd.Series) else row["Low"]
            c = row["Close"].iloc[0] if isinstance(row["Close"], pd.Series) else row["Close"]
            v = row["Volume"].iloc[0] if isinstance(row["Volume"], pd.Series) else row["Volume"]
            
            data.append({
                "time": int(d.timestamp()),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v
            })
        
        analysis = calculate_levels(df)
        return {"data": data, "analysis": analysis}
    except Exception as e:
        return {"data": [], "error": str(e)}

@app.get("/candles/history")
async def get_candles_history(symbol: str, interval: str = "5m", before: int = 0, limit: int = 100):
    return {"data": []}

active_connections = []

@app.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

import asyncio
async def broadcast_market_updates():
    while True:
        await asyncio.sleep(3)
        if active_connections:
            import time, json
            msg = json.dumps({
                "type": "market_update",
                "data": {
                    "symbol": "RELIANCE",
                    "open": 2400,
                    "high": 2410,
                    "low": 2390,
                    "close": 2400 + (time.time() % 10),
                    "volume": 1200,
                    "time": int(time.time())
                }
            })
            for connection in active_connections:
                try:
                    await connection.send_text(msg)
                except:
                    pass

@app.on_event("startup")
async def startup_bcast():
    import asyncio
    asyncio.create_task(broadcast_market_updates())

"""

if "def get_candles(" not in text:
    with open('api/app.py', 'a', encoding='utf-8') as f:
        f.write("\n\n" + new_routes)
    print("Routes appended.")
else:
    print("Routes already exist.")
