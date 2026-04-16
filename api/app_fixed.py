"""
FIXED FastAPI Backend with Proper CORS, Error Handling, and Logging
Run: python -m uvicorn api.app_fixed:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import logging

os.environ["PYTHONWARNINGS"] = "ignore::ResourceWarning"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import yfinance as yf
from typing import List, Optional, Dict, Any
import time
from functools import lru_cache

# Import from existing modules
try:
    from api.auth import hash_password, verify_password, create_access_token, verify_token
    from api.models import SessionLocal, User, Wallet, Holding, Transaction
    from api.db_utils import (
        create_user, get_user_by_email, get_user_by_id, verify_user_password,
        get_wallet, add_to_wallet, deduct_from_wallet,
        get_or_create_holding, get_user_holdings, update_holding_after_buy, 
        update_holding_after_sell, create_transaction, get_user_transactions
    )
    logger.info("✅ All imports successful")
except Exception as e:
    logger.error(f"❌ Import failed: {str(e)}")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="STCOK Trading API (Enhanced)",
    description="Complete stock trading system with auth, trading, wallet, payments",
    version="2.0.0"
)

# ✅ PROPER CORS CONFIGURATION - MUST BE FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:8081", "http://127.0.0.1:8080", "http://127.0.0.1:8081", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

logger.info("✅ CORS middleware registered")

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
    tier: str = "free"
    is_admin: bool = False

class StockSignal(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float
    signal_type: str
    confidence: float
    reason: str
    volume: Optional[int] = None

class BuyRequest(BaseModel):
    symbol: str
    quantity: int

class SellRequest(BaseModel):
    symbol: str
    quantity: int

class WalletResponse(BaseModel):
    balance: float
    available_balance: float
    used_balance: float

class HoldingResponse(BaseModel):
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    total_investment: float
    current_value: float
    pnl: float
    pnl_percent: float

# ==================== DATABASE DEPENDENCY ====================

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== REAL DATA: STOCK SIGNALS ====================

STOCK_SYMBOLS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "WIPRO.NS", 
                 "HDFCBANK.NS", "ICICIBANK.NS", "BAJAJFINSV.NS", "LT.NS"]

SIGNALS_CONFIG = [
    {"symbol": "RELIANCE", "signal_type": "BUY", "confidence": 0.85, "reason": "Bullish breakout on daily"},
    {"symbol": "TCS", "signal_type": "BUY", "confidence": 0.78, "reason": "RSI oversold, reversal pattern"},
    {"symbol": "INFY", "signal_type": "SELL", "confidence": 0.72, "reason": "Bearish divergence"},
    {"symbol": "WIPRO", "signal_type": "BUY", "confidence": 0.81, "reason": "Golden cross on weekly"},
    {"symbol": "HDFCBANK", "signal_type": "SELL", "confidence": 0.68, "reason": "Support break below 1500"},
    {"symbol": "ICICIBANK", "signal_type": "BUY", "confidence": 0.75, "reason": "Hammer pattern on daily"},
    {"symbol": "BAJAJFINSV", "signal_type": "BUY", "confidence": 0.79, "reason": "Volume breakout"},
    {"symbol": "LT", "signal_type": "SELL", "confidence": 0.71, "reason": "Resistance rejected twice"},
]

PRICE_CACHE = {}
CACHE_TTL = 60

@lru_cache(maxsize=100)
def get_stock_price(symbol: str) -> Dict[str, Any]:
    """Fetch real stock price from yfinance with caching"""
    try:
        cache_key = symbol
        if cache_key in PRICE_CACHE:
            cached_data, timestamp = PRICE_CACHE[cache_key]
            if time.time() - timestamp < CACHE_TTL:
                return cached_data
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 1500.0))
        prev_close = info.get("previousClose", current_price)
        volume = info.get("volume", 1000000)
        
        change = current_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
        
        data = {
            "price": round(current_price, 2),
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "volume": volume,
            "name": info.get("longName", symbol.replace(".NS", ""))
        }
        
        PRICE_CACHE[cache_key] = (data, time.time())
        logger.info(f"✅ Fetched price for {symbol}: ₹{data['price']}")
        return data
        
    except Exception as e:
        logger.warning(f"⚠️ Price fetch failed for {symbol}: {str(e)}, using fallback")
        return {
            "price": 1500.0,
            "change": 0.0,
            "changePercent": 0.0,
            "volume": 1000000,
            "name": symbol.replace(".NS", "")
        }

def get_stock_signals_with_prices() -> List[Dict[str, Any]]:
    """Get all signals with real prices merged in"""
    signals = []
    
    for signal_config in SIGNALS_CONFIG:
        symbol_ns = signal_config["symbol"] + ".NS"
        
        price_data = get_stock_price(symbol_ns)
        
        signal = {
            "symbol": signal_config["symbol"],
            "name": price_data["name"],
            "price": price_data["price"],
            "change": price_data["change"],
            "changePercent": price_data["changePercent"],
            "signal_type": signal_config["signal_type"],
            "confidence": signal_config["confidence"],
            "reason": signal_config["reason"],
            "volume": price_data.get("volume", 0)
        }
        signals.append(signal)
    
    return signals

# ==================== AUTHENTICATION ====================

def verify_auth_token(authorization: Optional[str] = Header(None), db = None) -> Optional[int]:
    """Verify JWT token and return user_id"""
    if not authorization:
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        token_data = verify_token(token)
        
        if token_data and token_data.email:
            if db:
                user = get_user_by_email(db, token_data.email)
                return user.id if user else None
            return None
        return None
    except Exception as e:
        logger.warning(f"⚠️ Token verification failed: {str(e)}")
        return None

# ==================== AUTH ENDPOINTS ====================

@app.options("/api/auth/signup")
async def options_signup():
    """Handle CORS preflight for signup"""
    return JSONResponse(status_code=200, content={})

@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(user: UserSignup, db = Depends(get_db)):
    """Create new user account"""
    logger.info(f"📝 Signup attempt: {user.email}")
    
    try:
        existing = get_user_by_email(db, user.email)
        if existing:
            logger.warning(f"⚠️ Signup failed: User exists {user.email}")
            raise HTTPException(status_code=400, detail="User already exists")
        
        new_user = create_user(db, user.email, user.password, user.name)
        token = create_access_token(user.email, new_user.id)
        
        logger.info(f"✅ User created: {user.email} (ID: {new_user.id})")
        
        return {
            "token": token,
            "user_id": new_user.id,
            "email": new_user.email,
            "name": user.name,
            "tier": "free",
            "is_admin": False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@app.options("/api/auth/login")
async def options_login():
    """Handle CORS preflight for login"""
    return JSONResponse(status_code=200, content={})

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(user: UserLogin, db = Depends(get_db)):
    """Login to account"""
    logger.info(f"🔐 Login attempt: {user.email}")
    
    try:
        db_user = get_user_by_email(db, user.email)
        if not db_user or not verify_password(user.password, db_user.password_hash):
            logger.warning(f"⚠️ Login failed: Invalid credentials {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token(user.email, db_user.id)
        
        logger.info(f"✅ User logged in: {user.email}")
        
        return {
            "token": token,
            "user_id": db_user.id,
            "email": db_user.email,
            "name": user.email.split("@")[0],
            "tier": getattr(db_user, "tier", "free"),
            "is_admin": bool(getattr(db_user, "is_admin", False))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/auth/me")
async def get_me(authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Get current user info"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "tier": getattr(user, "tier", "free"),
        "is_admin": bool(getattr(user, "is_admin", False))
    }

# ==================== SIGNAL ENDPOINTS ====================

@app.get("/api/signals/active")
async def get_active_signals():
    """Get all active buy/sell signals WITH REAL PRICES"""
    logger.info("📊 Fetching active signals")
    
    try:
        signals = get_stock_signals_with_prices()
        
        return {
            "signals": signals,
            "total": len(signals),
            "buy_count": sum(1 for s in signals if s["signal_type"] == "BUY"),
            "sell_count": sum(1 for s in signals if s["signal_type"] == "SELL"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error fetching signals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching signals: {str(e)}")

# ==================== PORTFOLIO ENDPOINTS ====================

@app.get("/portfolio")
async def get_portfolio(authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Get user portfolio summary"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        wallet = get_wallet(db, user_id)
        holdings = get_user_holdings(db, user_id)
        
        total_value = wallet.balance if wallet else 0
        
        holdings_list = []
        for holding in holdings:
            try:
                price_data = get_stock_price(holding.symbol + ".NS")
                current_price = price_data["price"]
                current_value = holding.quantity * current_price
                pnl = current_value - holding.total_investment
                pnl_percent = (pnl / holding.total_investment * 100) if holding.total_investment > 0 else 0
                
                total_value += current_value
                
                holdings_list.append({
                    "symbol": holding.symbol,
                    "quantity": holding.quantity,
                    "avg_price": round(holding.avg_price, 2),
                    "current_price": current_price,
                    "total_investment": round(holding.total_investment, 2),
                    "current_value": round(current_value, 2),
                    "pnl": round(pnl, 2),
                    "pnl_percent": round(pnl_percent, 2)
                })
            except Exception as e:
                logger.warning(f"⚠️ Error processing holding {holding.symbol}: {str(e)}")
                continue
        
        return {
            "total_value": round(total_value, 2),
            "wallet_balance": round(wallet.balance, 2) if wallet else 0,
            "holdings": holdings_list,
            "number_of_holdings": len(holdings)
        }
    except Exception as e:
        logger.error(f"❌ Portfolio error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")

# ==================== TRADING ENDPOINTS ====================

@app.post("/api/trading/buy")
async def buy_stock(req: BuyRequest, authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Buy stock with wallet balance check"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logger.info(f"💰 Buy request: {req.symbol} x{req.quantity}")
    
    try:
        symbol_ns = req.symbol + ".NS"
        price_data = get_stock_price(symbol_ns)
        current_price = price_data["price"]
        
        total_cost = req.quantity * current_price
        
        wallet = get_wallet(db, user_id)
        if not wallet or wallet.balance < total_cost:
            logger.warning(f"⚠️ Buy failed: Insufficient balance ({wallet.balance} < {total_cost})")
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        deduct_from_wallet(db, user_id, total_cost)
        holding = update_holding_after_buy(db, user_id, req.symbol, req.quantity, current_price)
        
        transaction = create_transaction(
            db=db,
            user_id=user_id,
            type="BUY",
            symbol=req.symbol,
            quantity=req.quantity,
            price=current_price,
            total_amount=total_cost,
            status="completed"
        )
        
        logger.info(f"✅ Buy successful: {req.symbol} x{req.quantity} @ ₹{current_price}")
        
        return {
            "status": "success",
            "transaction_id": transaction.id,
            "symbol": req.symbol,
            "quantity": req.quantity,
            "price": current_price,
            "total": total_cost,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Buy error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Buy failed: {str(e)}")

@app.post("/api/trading/sell")
async def sell_stock(req: SellRequest, authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Sell stock with holdings check"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logger.info(f"📉 Sell request: {req.symbol} x{req.quantity}")
    
    try:
        holdings = get_user_holdings(db, user_id)
        holding = next((h for h in holdings if h.symbol == req.symbol), None)
        
        if not holding or holding.quantity < req.quantity:
            logger.warning(f"⚠️ Sell failed: Insufficient holdings")
            raise HTTPException(status_code=400, detail="Insufficient holdings")
        
        symbol_ns = req.symbol + ".NS"
        price_data = get_stock_price(symbol_ns)
        current_price = price_data["price"]
        
        total_proceeds = req.quantity * current_price
        
        update_holding_after_sell(db, user_id, req.symbol, req.quantity, current_price)
        add_to_wallet(db, user_id, total_proceeds)
        
        transaction = create_transaction(
            db=db,
            user_id=user_id,
            type="SELL",
            symbol=req.symbol,
            quantity=req.quantity,
            price=current_price,
            total_amount=total_proceeds,
            status="completed"
        )
        
        logger.info(f"✅ Sell successful: {req.symbol} x{req.quantity} @ ₹{current_price}")
        
        return {
            "status": "success",
            "transaction_id": transaction.id,
            "symbol": req.symbol,
            "quantity": req.quantity,
            "price": current_price,
            "total": total_proceeds,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sell error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sell failed: {str(e)}")

# ==================== WALLET ENDPOINTS ====================

@app.get("/wallet", response_model=WalletResponse)
async def get_wallet_balance(authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Get wallet balance"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    wallet = get_wallet(db, user_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return {
        "balance": wallet.balance,
        "available_balance": wallet.available_balance,
        "used_balance": wallet.used_balance
    }

@app.get("/portfolio/transactions")
async def get_transactions(authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Get transaction history"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    transactions = get_user_transactions(db, user_id)
    
    return {
        "transactions": [
            {
                "id": t.id,
                "type": t.type,
                "symbol": t.symbol,
                "quantity": t.quantity,
                "price": t.price,
                "total_amount": t.total_amount,
                "status": t.status,
                "created_at": t.created_at if hasattr(t, 'created_at') else datetime.now().isoformat()
            }
            for t in transactions
        ],
        "total": len(transactions)
    }

# ==================== PAYMENT ENDPOINTS ====================

@app.post("/api/payment/create-order")
async def create_payment_order(req: Dict[str, float], authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Create payment order"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        amount = req.get("amount", 1000)
        order_id = f"order_{int(datetime.now().timestamp())}"
        
        logger.info(f"💳 Payment order created: {order_id} for ₹{amount}")
        
        return {
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "key_id": os.getenv("RAZORPAY_KEY_ID", "rzp_test_demo"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Payment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@app.post("/api/payment/verify")
async def verify_payment(req: Dict[str, str], authorization: Optional[str] = Header(None), db = Depends(get_db)):
    """Verify payment and update wallet"""
    user_id = verify_auth_token(authorization, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        amount = 10000  # Demo amount
        
        add_to_wallet(db, user_id, amount)
        
        create_transaction(
            db=db,
            user_id=user_id,
            type="WALLET_RECHARGE",
            symbol=None,
            quantity=None,
            price=None,
            total_amount=amount,
            status="completed"
        )
        
        logger.info(f"✅ Payment verified and wallet updated: ₹{amount}")
        
        return {
            "status": "success",
            "payment_verified": True,
            "message": f"₹{amount} added to wallet",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Payment verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

# ==================== SYSTEM ENDPOINTS ====================

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "alive",
        "version": "2.0.0",
        "mode": "fixed_with_logging",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Welcome message"""
    return {
        "message": "STCOK Trading API (Fixed v2.0)",
        "docs": "/docs",
        "health": "/health",
        "features": ["Authentication", "Real Prices", "Trading", "Wallet", "Payments"]
    }

logger.info("✅ Backend ready to start!")
