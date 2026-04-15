"""
Simplified FastAPI backend - Runs without heavy ML dependencies.
Provides core auth, trading, and search/prompt functionality.
Use this while full ML system loads in background.
"""

import os
os.environ["PYTHONWARNINGS"] = "ignore::ResourceWarning"

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import sqlite3
from typing import List, Optional, Dict, Any

app = FastAPI(
    title="STOCK Trading API",
    description="Stock dashboard & trading system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class UserSignup(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user_id: int
    email: str
    name: str

class StockSignal(BaseModel):
    symbol: str
    signal_type: str  # "BUY", "SELL"
    confidence: float
    reason: str

class PromptQuery(BaseModel):
    query: str
    limit: int = 10

# ==================== MOCK DATA ====================

STOCK_SIGNALS = [
    {"symbol": "RELIANCE", "signal_type": "BUY", "confidence": 0.85, "reason": "Bullish breakout on daily"},
    {"symbol": "TCS", "signal_type": "BUY", "confidence": 0.78, "reason": "RSI oversold, reversal pattern"},
    {"symbol": "INFY", "signal_type": "SELL", "confidence": 0.72, "reason": "Bearish divergence"},
    {"symbol": "WIPRO", "signal_type": "BUY", "confidence": 0.81, "reason": "Golden cross on weekly"},
    {"symbol": "HDFCBANK", "signal_type": "SELL", "confidence": 0.68, "reason": "Support break below 1500"},
    {"symbol": "ICICIBANK", "signal_type": "BUY", "confidence": 0.75, "reason": "Hammer pattern on daily"},
    {"symbol": "BAJAJFINSV", "signal_type": "BUY", "confidence": 0.79, "reason": "Volume breakout"},
    {"symbol": "LT", "signal_type": "SELL", "confidence": 0.71, "reason": "Resistance rejected twice"},
]

MOCK_PORTFOLIO = {
    "total_value": 50000,
    "cash_balance": 10000,
    "portfolio_return": 12.5,
    "today_change": 250,
    "holdings": [
        {"symbol": "RELIANCE", "qty": 10, "current_price": 2850, "invested": 28000, "current_value": 28500},
        {"symbol": "TCS", "qty": 5, "current_price": 3500, "invested": 17000, "current_value": 17500},
    ]
}

USERS = {
    1: {
        "id": 1,
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "name": "Test User",
        "balance": 50000,
        "created_at": datetime.now().isoformat()
    }
}

TOKENS = {}

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(user: UserSignup):
    """Create new user account"""
    # Simple mock - in production would use proper hashing
    user_id = len(USERS) + 1
    USERS[user_id] = {
        "id": user_id,
        "email": user.email,
        "password_hash": user.password,
        "name": user.name,
        "balance": 100000,
        "created_at": datetime.now().isoformat()
    }
    
    token = f"token_{user_id}_{datetime.now().timestamp()}"
    TOKENS[token] = user_id
    
    return {
        "token": token,
        "user_id": user_id,
        "email": user.email,
        "name": user.name
    }

@app.post("/api/auth/login", response_model=AuthResponse)
def login(user: UserLogin):
    """Login to account"""
    for uid, u in USERS.items():
        if u["email"] == user.email and u["password_hash"] == user.password:
            token = f"token_{uid}_{datetime.now().timestamp()}"
            TOKENS[token] = uid
            return {
                "token": token,
                "user_id": uid,
                "email": u["email"],
                "name": u["name"]
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

def get_user(authorization: Optional[str] = Header(None)):
    """Get current user from token"""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    user_id = TOKENS.get(token)
    return user_id

# ==================== SIGNAL ENDPOINTS ====================

@app.get("/api/signals/active")
def get_active_signals(user_id: Optional[int] = Depends(get_user)):
    """Get all active buy/sell signals"""
    return {
        "signals": STOCK_SIGNALS,
        "total": len(STOCK_SIGNALS),
        "buy_count": sum(1 for s in STOCK_SIGNALS if s["signal_type"] == "BUY"),
        "sell_count": sum(1 for s in STOCK_SIGNALS if s["signal_type"] == "SELL")
    }

@app.get("/stocks/top-bulls")
def top_bulls(limit: int = 5):
    """Top bullish stocks"""
    bulls = [s for s in STOCK_SIGNALS if s["signal_type"] == "BUY"]
    bulls = sorted(bulls, key=lambda x: x["confidence"], reverse=True)
    return {"stocks": bulls[:limit], "total": len(bulls)}

@app.get("/stocks/top-bears")
def top_bears(limit: int = 5):
    """Top bearish stocks"""
    bears = [s for s in STOCK_SIGNALS if s["signal_type"] == "SELL"]
    bears = sorted(bears, key=lambda x: x["confidence"], reverse=True)
    return {"stocks": bears[:limit], "total": len(bears)}

@app.get("/stocks/top-losers")
def top_losers(limit: int = 5):
    """Top losing stocks"""
    losers = sorted(STOCK_SIGNALS, key=lambda x: x["confidence"])
    return {"stocks": losers[:limit], "total": len(losers)}

@app.get("/alerts/live")
def live_alerts(limit: int = 50):
    """Live trading alerts"""
    return {"alerts": STOCK_SIGNALS[:limit], "total": len(STOCK_SIGNALS)}

@app.post("/api/search")
def search_stocks(query: PromptQuery):
    """Search/filter stocks by query"""
    q = query.query.lower().strip()
    
    results = []
    for signal in STOCK_SIGNALS:
        # Search by symbol
        if q in signal["symbol"].lower():
            results.append(signal)
        # Search by signal type
        elif q in signal["signal_type"].lower():
            results.append(signal)
        # Search by keyword in reason
        elif q in signal["reason"].lower():
            results.append(signal)
    
    return {
        "query": query.query,
        "results": results[:query.limit],
        "total": len(results)
    }

@app.post("/api/prompt")
def handle_prompt(query: PromptQuery):
    """Handle user prompt/query for stock insights"""
    q = query.query.lower().strip()
    
    # Simple intent matching
    if "bullish" in q or "buy" in q or "strong" in q:
        signals = [s for s in STOCK_SIGNALS if s["signal_type"] == "BUY"]
        signals = sorted(signals, key=lambda x: x["confidence"], reverse=True)
        return {
            "query": query.query,
            "intent": "bullish_stocks",
            "results": signals[:query.limit],
            "message": f"Found {len(signals)} strong BUY signals"
        }
    
    elif "bearish" in q or "sell" in q or "weak" in q:
        signals = [s for s in STOCK_SIGNALS if s["signal_type"] == "SELL"]
        signals = sorted(signals, key=lambda x: x["confidence"], reverse=True)
        return {
            "query": query.query,
            "intent": "bearish_stocks",
            "results": signals[:query.limit],
            "message": f"Found {len(signals)} SELL signals"
        }
    
    elif "portfolio" in q or "holdings" in q:
        return {
            "query": query.query,
            "intent": "portfolio",
            "results": MOCK_PORTFOLIO,
            "message": "Here's your portfolio summary"
        }
    
    elif "high confidence" in q or "confidence" in q:
        signals = sorted(STOCK_SIGNALS, key=lambda x: x["confidence"], reverse=True)
        signals = [s for s in signals if s["confidence"] > 0.7]
        return {
            "query": query.query,
            "intent": "high_confidence",
            "results": signals[:query.limit],
            "message": f"Showing {len(signals)} high-confidence signals (>70%)"
        }
    
    else:
        # Default: return all signals
        return {
            "query": query.query,
            "intent": "general",
            "results": STOCK_SIGNALS[:query.limit],
            "message": f"Showing {len(STOCK_SIGNALS)} active signals"
        }

# ==================== PORTFOLIO ENDPOINTS ====================

@app.get("/api/portfolio")
def get_portfolio(user_id: Optional[int] = Depends(get_user)):
    """Get user portfolio summary"""
    return MOCK_PORTFOLIO

@app.get("/api/portfolio/holdings")
def get_holdings(user_id: Optional[int] = Depends(get_user)):
    """Get detailed holdings"""
    return {
        "holdings": MOCK_PORTFOLIO["holdings"],
        "total_value": MOCK_PORTFOLIO["total_value"],
        "cash": MOCK_PORTFOLIO["cash_balance"]
    }

# ==================== TRADING ENDPOINTS ====================

@app.post("/api/trading/buy")
def buy_stock(symbol: str, qty: int, price: float, user_id: Optional[int] = Depends(get_user)):
    """Buy stock (demo)"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    total_cost = qty * price
    if total_cost > MOCK_PORTFOLIO["cash_balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    return {
        "status": "success",
        "transaction_id": f"BUY_{datetime.now().timestamp()}",
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "total": total_cost,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/trading/sell")
def sell_stock(symbol: str, qty: int, price: float, user_id: Optional[int] = Depends(get_user)):
    """Sell stock (demo)"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {
        "status": "success",
        "transaction_id": f"SELL_{datetime.now().timestamp()}",
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "total": qty * price,
        "timestamp": datetime.now().isoformat()
    }

# ==================== HEALTH & INFO ====================

@app.get("/health")
def health():
    """Health check"""
    return {"status": "alive", "version": "1.0.0"}

@app.get("/")
def root():
    """Welcome message"""
    return {"message": "STOCK Trading API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
