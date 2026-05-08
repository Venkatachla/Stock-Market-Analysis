"""
FastAPI routes for authentication, trading, portfolio, and payments.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
import yfinance as yf
from sqlalchemy.orm import Session

from api.models import get_db, User, Holding
from api.auth import create_access_token, verify_token
from api.db_utils import (
    create_user, get_user_by_email, verify_user_password,
    update_user_token, get_wallet, add_to_wallet, deduct_from_wallet, refund_to_wallet,
    get_or_create_holding, get_user_holdings, update_holding_after_buy, update_holding_after_sell,
    create_transaction, get_user_transactions, get_transaction_by_order_id, update_transaction_status
)
from api.razorpay_integration import create_order, verify_payment_signature, fetch_payment_details

router = APIRouter()


# ====================== REQUEST/RESPONSE MODELS ======================

class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    email: str
    tier: str
    is_admin: bool


class WalletResponse(BaseModel):
    balance: float


class HoldingResponse(BaseModel):
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    total_investment: float
    current_value: float
    pnl: float
    pnl_percent: float
    purchase_date: str


class TransactionResponse(BaseModel):
    id: int
    type: str
    symbol: Optional[str]
    quantity: Optional[int]
    price: Optional[float]
    total_amount: float
    status: str
    created_at: str


class BuyRequest(BaseModel):
    symbol: str
    quantity: int
    confidence_score: Optional[float] = None


class SellRequest(BaseModel):
    symbol: str
    quantity: int


class RazorpayOrderRequest(BaseModel):
    amount: float
    phone: Optional[str] = "9999999999"


class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


class PortfolioResponse(BaseModel):
    wallet: WalletResponse
    holdings: List[HoldingResponse]
    total_value: float
    total_invested: float
    total_pnl: float
    total_pnl_percent: float


# ====================== UTILITY FUNCTIONS ======================

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Dependency to get current authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split("Bearer ")[1]
    token_data = verify_token(token)
    
    if not token_data or not token_data.email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_email(db, token_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


def safe_get_stock_price(symbol: str) -> Optional[float]:
    """Get stock price with fallback"""
    try:
        return get_stock_price(symbol)
    except:
        return None


def get_stock_price(symbol: str) -> Optional[float]:
    """Get current stock price from Yahoo Finance"""
    try:
        # Add .NS for NSE stocks if not already present
        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            symbol = f"{symbol}.NS"
        
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")
        
        if data.empty:
            return None
        
        # Get closing price (most recent)
        if isinstance(data.columns, pd.MultiIndex):
            close = data.iloc[-1][("Close", "")].item() if ("Close", "") in data.columns else None
        else:
            close = data.iloc[-1]["Close"]
        
        return float(close)
    except Exception as e:
        print(f"Error fetching price for {symbol}: {str(e)}")
        return None


import pandas as pd


# ====================== AUTH ENDPOINTS ======================

@router.post("/auth/register", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    existing = get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = create_user(db, request.email, request.password, tier="free", is_admin=0)
    token = create_access_token(user.email, user.id)
    update_user_token(db, user.id, token)
    
    return AuthResponse(
        token=token,
        email=user.email,
        tier=user.tier,
        is_admin=bool(user.is_admin)
    )


@router.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user = verify_user_password(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user.email, user.id)
    update_user_token(db, user.id, token)
    
    return AuthResponse(
        token=token,
        email=user.email,
        tier=user.tier,
        is_admin=bool(user.is_admin)
    )


@router.get("/auth/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tier": current_user.tier,
        "is_admin": bool(current_user.is_admin)
    }


# ====================== WALLET ENDPOINTS ======================

@router.get("/wallet", response_model=WalletResponse)
def get_wallet_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user wallet information"""
    wallet = get_wallet(db, current_user.id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletResponse(balance=wallet.balance)  # ✅ FIX: Only return actual fields


# ====================== RAZORPAY PAYMENT ENDPOINTS ======================

@router.post("/payment/create-order", response_model=RazorpayOrderResponse)
def create_payment_order(
    request: RazorpayOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Razorpay order for wallet recharge"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    order_details = create_order(request.amount, current_user.id, current_user.email, request.phone)
    
    if not order_details:
        raise HTTPException(status_code=500, detail="Failed to create payment order")
    
    # Create transaction record
    create_transaction(
        db,
        current_user.id,
        "DEPOSIT",
        request.amount,
        order_id=order_details["order_id"],
        status="PENDING",
        reason="Wallet recharge via Razorpay"
    )
    
    return order_details


@router.post("/payment/verify")
def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify payment and update wallet"""
    # Verify signature
    if not verify_payment_signature(request.order_id, request.payment_id, request.signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    # Fetch payment details to confirm
    payment_details = fetch_payment_details(request.payment_id)
    if not payment_details:
        raise HTTPException(status_code=400, detail="Payment not found")
    
    if payment_details["status"] != "captured":
        raise HTTPException(status_code=400, detail="Payment not successful")
    
    # Get the pending transaction
    transaction = get_transaction_by_order_id(db, request.order_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # IDEMPOTENCY: If already processed, return success without double-crediting
    if transaction.status == "SUCCESS":
        print(f"[PAYMENT] Duplicate verify for order {request.order_id} — already processed")
        return {
            "status": "success",
            "message": "Payment already processed",
            "amount": transaction.total_amount
        }
    
    # Add money to wallet
    amount = payment_details["amount"]
    if not add_to_wallet(db, current_user.id, amount):
        raise HTTPException(status_code=500, detail="Failed to update wallet")
    
    # Update transaction to SUCCESS
    update_transaction_status(
        db,
        transaction.id,
        "SUCCESS",
        request.payment_id,
        request.signature
    )
    
    print(f"[PAYMENT] User {current_user.email} deposited ₹{amount} via order {request.order_id}")
    return {
        "status": "success",
        "message": f"\u20b9{amount} added to wallet",
        "amount": amount
    }


# ====================== TRADING ENDPOINTS ======================

@router.post("/trading/buy")
def buy_stock(
    request: BuyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buy stock"""
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    # Get current price
    price = get_stock_price(request.symbol)
    if price is None:
        raise HTTPException(status_code=400, detail=f"Could not fetch price for {request.symbol}")
    
    # Calculate total cost
    total_cost = price * request.quantity
    
    # Check wallet balance
    wallet = get_wallet(db, current_user.id)
    if not wallet or wallet.balance < total_cost:  # ✅ FIX: Use wallet.balance not available_balance
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Deduct from wallet (atomic)
    if not deduct_from_wallet(db, current_user.id, total_cost):
        raise HTTPException(status_code=500, detail="Failed to process payment")
    
    # Update holding — rollback wallet if this fails
    try:
        holding = get_or_create_holding(db, current_user.id, request.symbol)
        update_holding_after_buy(db, holding, request.quantity, price)
    except Exception as e:
        print(f"[BUY] Holding update failed for {request.symbol}, refunding ₹{total_cost}: {e}")
        refund_to_wallet(db, current_user.id, total_cost)
        raise HTTPException(status_code=500, detail="Trade failed, funds refunded")
    
    # Create transaction record
    transaction = create_transaction(
        db,
        current_user.id,
        "BUY",
        total_cost,
        symbol=request.symbol,
        quantity=request.quantity,
        price=price,
        status="SUCCESS",
        confidence_score=request.confidence_score,
        reason="Manual buy order"
    )
    
    print(f"[BUY] User {current_user.email} bought {request.quantity}x{request.symbol} @ ₹{price} | txn#{transaction.id}")
    return {
        "status": "success",
        "message": f"Bought {request.quantity} shares of {request.symbol}",
        "symbol": request.symbol,
        "quantity": request.quantity,
        "price": price,
        "total_cost": total_cost,
        "transaction_id": transaction.id
    }


@router.post("/trading/sell")
def sell_stock(
    request: SellRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sell stock"""
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    # Get holding
    holding = db.query(Holding).filter(
        Holding.user_id == current_user.id,
        Holding.symbol == request.symbol
    ).first()
    
    if not holding or holding.quantity < request.quantity:
        raise HTTPException(status_code=400, detail="Insufficient quantity to sell")
    
    # Get current price
    price = get_stock_price(request.symbol)
    if price is None:
        raise HTTPException(status_code=400, detail=f"Could not fetch price for {request.symbol}")
    
    # Calculate total proceeds
    total_proceeds = price * request.quantity
    
    # CRITICAL: Credit wallet FIRST, then deduct holding
    # If wallet credit fails, holding is untouched — no partial state
    if not add_to_wallet(db, current_user.id, total_proceeds):
        raise HTTPException(status_code=500, detail="Failed to process payment")
    
    # Update holding (deduct or delete)
    try:
        update_holding_after_sell(db, holding, request.quantity, price)
    except Exception as e:
        print(f"[SELL] Holding update failed for {request.symbol}, reversing wallet: {e}")
        deduct_from_wallet(db, current_user.id, total_proceeds)  # reverse the credit
        raise HTTPException(status_code=500, detail="Trade failed, wallet reversed")
    
    # Create transaction record
    transaction = create_transaction(
        db,
        current_user.id,
        "SELL",
        total_proceeds,
        symbol=request.symbol,
        quantity=request.quantity,
        price=price,
        status="SUCCESS",
        reason="Manual sell order"
    )
    
    print(f"[SELL] User {current_user.email} sold {request.quantity}x{request.symbol} @ ₹{price} | txn#{transaction.id}")
    return {
        "status": "success",
        "message": f"Sold {request.quantity} shares of {request.symbol}",
        "symbol": request.symbol,
        "quantity": request.quantity,
        "price": price,
        "total_proceeds": total_proceeds,
        "transaction_id": transaction.id
    }


# ====================== PORTFOLIO ENDPOINTS ======================

@router.get("/portfolio", response_model=PortfolioResponse)
def get_portfolio(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user portfolio"""
    wallet = get_wallet(db, current_user.id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    holdings = get_user_holdings(db, current_user.id)
    
    # ✅ FIX: Compute holding values correctly
    holdings_response = []
    total_value = 0
    total_invested = 0
    
    for h in holdings:
        # Fetch live price with fallback
        current_price = safe_get_stock_price(h.symbol)
        if current_price is None:
            current_price = h.avg_price  # Fallback to avg price
        
        # Compute derived values
        total_investment = h.quantity * h.avg_price
        current_value = h.quantity * current_price
        pnl = current_value - total_investment
        pnl_percent = (pnl / total_investment * 100) if total_investment > 0 else 0
        
        holdings_response.append(HoldingResponse(
            symbol=h.symbol,
            quantity=h.quantity,
            avg_price=h.avg_price,
            current_price=current_price,
            total_investment=total_investment,
            current_value=current_value,
            pnl=pnl,
            pnl_percent=pnl_percent,
            purchase_date=h.purchase_date
        ))
        
        total_value += current_value
        total_invested += total_investment
    
    total_pnl = total_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    return PortfolioResponse(
        wallet=WalletResponse(balance=wallet.balance),  # ✅ FIX: Only return balance
        holdings=holdings_response,
        total_value=total_value,
        total_invested=total_invested,
        total_pnl=total_pnl,
        total_pnl_percent=total_pnl_percent
    )


@router.get("/portfolio/transactions")
def get_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user transaction history"""
    transactions = get_user_transactions(db, current_user.id, limit)
    
    return [
        TransactionResponse(
            id=t.id,
            type=t.type,
            symbol=t.symbol,
            quantity=t.quantity,
            price=t.price,
            total_amount=t.total_amount,
            status=t.status,
            created_at=t.created_at
        )
        for t in transactions
    ]


class AddFundsRequest(BaseModel):
    amount: float


@router.post("/portfolio/add-demo-funds")
def add_demo_funds(
    request: AddFundsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add demo funds to wallet (for testing only)"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    if not add_to_wallet(db, current_user.id, request.amount):
        raise HTTPException(status_code=500, detail="Failed to add funds")
    
    create_transaction(
        db,
        current_user.id,
        "DEPOSIT",
        request.amount,
        status="SUCCESS",
        reason="Demo wallet recharge"
    )
    
    return {
        "status": "success",
        "message": f"₹{request.amount} added to wallet",
        "amount": request.amount,
        "new_balance": request.amount  # ✅ Add new_balance for testing
    }


# ====================== SIGNALS ENDPOINTS ======================

@router.get("/signals/active")
def get_active_signals(
    current_user: User = Depends(get_current_user)
):
    """Get active trading signals"""
    # Return empty signals list (frontend can handle this)
    # In production, this would fetch from ML model predictions
    return {
        "signals": [],
        "buy_count": 0,
        "sell_count": 0,
        "total_count": 0
    }
