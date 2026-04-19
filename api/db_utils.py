"""
Database utility functions for user, wallet, holding, and transaction operations.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from api.models import User, Wallet, Holding, Transaction
from api.auth import hash_password, verify_password


# ====================== USER FUNCTIONS ======================

def create_user(db: Session, email: str, password: str, tier: str = "free", is_admin: int = 0) -> Optional[User]:
    """Create a new user"""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return None
    
    user = User(
        email=email,
        password_hash=hash_password(password),
        tier=tier,
        is_admin=is_admin,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    
    # Create wallet for new user
    create_wallet(db, user.id)
    
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def verify_user_password(db: Session, email: str, password: str) -> Optional[User]:
    """Verify user email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def update_user_token(db: Session, user_id: int, token: str) -> bool:
    """Update user token"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    user.token = token
    user.updated_at = datetime.utcnow().isoformat()
    # db.commit() - Controlled at route level
    return True


# ====================== WALLET FUNCTIONS ======================

def create_wallet(db: Session, user_id: int, initial_balance: float = 0.0) -> Wallet:
    """Create wallet for user"""
    wallet = Wallet(
        user_id=user_id,
        balance=initial_balance,
        used_balance=0.0,
        available_balance=initial_balance,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(wallet)
    db.flush()
    db.refresh(wallet)
    return wallet


def get_wallet(db: Session, user_id: int, lock: bool = False) -> Optional[Wallet]:
    """Get user wallet (with optional row-level locking)"""
    query = db.query(Wallet).filter(Wallet.user_id == user_id)
    if lock:
        query = query.with_for_update()
    return query.first()


def add_to_wallet(db: Session, user_id: int, amount: float) -> bool:
    """Add money to wallet"""
    wallet = get_wallet(db, user_id)
    if not wallet:
        return False
    
    wallet.balance += amount
    wallet.available_balance += amount
    wallet.updated_at = datetime.utcnow().isoformat()
    # db.commit() - Controlled at route level
    return True


def deduct_from_wallet(db: Session, user_id: int, amount: float) -> bool:
    """Deduct money from wallet (lock funds for purchase)"""
    wallet = get_wallet(db, user_id)
    if not wallet or wallet.available_balance < amount:
        return False
    
    wallet.available_balance -= amount
    wallet.used_balance += amount
    wallet.updated_at = datetime.utcnow().isoformat()
    # db.commit() - Controlled at route level
    return True


def refund_to_wallet(db: Session, user_id: int, amount: float) -> bool:
    """Refund money to wallet (release locked funds)"""
    wallet = get_wallet(db, user_id)
    if not wallet:
        return False
    
    wallet.available_balance += amount
    wallet.used_balance = max(0, wallet.used_balance - amount)
    wallet.updated_at = datetime.utcnow().isoformat()
    # db.commit() - Controlled at route level
    return True


# ====================== HOLDING FUNCTIONS ======================

def get_holding(db: Session, user_id: int, symbol: str) -> Optional[Holding]:
    """Get existing holding WITHOUT creating (for SELL operations)"""
    return db.query(Holding).filter(
        Holding.user_id == user_id,
        Holding.symbol == symbol
    ).first()


def get_or_create_holding(db: Session, user_id: int, symbol: str) -> Holding:
    """Get existing holding or create new one"""
    holding = db.query(Holding).filter(
        Holding.user_id == user_id,
        Holding.symbol == symbol
    ).first()
    
    if holding:
        return holding
    
    holding = Holding(
        user_id=user_id,
        symbol=symbol,
        quantity=0,
        avg_price=0.0,
        current_price=0.0,
        total_investment=0.0,
        current_value=0.0,
        pnl=0.0,
        pnl_percent=0.0,
        purchase_date=datetime.utcnow().isoformat(),
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(holding)
    db.flush()
    db.refresh(holding)
    return holding


def get_user_holdings(db: Session, user_id: int) -> List[Holding]:
    """Get all holdings for a user"""
    return db.query(Holding).filter(Holding.user_id == user_id).all()


def update_holding_after_buy(db: Session, holding: Holding, quantity: int, price: float) -> None:
    """Update holding after buy transaction"""
    old_qty = holding.quantity
    new_qty = old_qty + quantity
    if old_qty == 0:
        holding.avg_price = price
    else:
        # Calculate new average price using old quantity
        total_cost = (old_qty * holding.avg_price) + (quantity * price)
        holding.avg_price = total_cost / new_qty
    # Always update quantity regardless of branch
    holding.quantity = new_qty
    holding.current_price = price
    holding.total_investment = holding.quantity * holding.avg_price
    holding.current_value = holding.quantity * holding.current_price
    holding.pnl = holding.current_value - holding.total_investment
    holding.pnl_percent = (holding.pnl / holding.total_investment * 100) if holding.total_investment > 0 else 0
    holding.updated_at = datetime.utcnow().isoformat()
    # db.commit() - Controlled at route level



def update_holding_after_sell(db: Session, holding: Holding, quantity: int, price: float) -> None:
    """Update holding after sell transaction"""
    if quantity >= holding.quantity:
        # Sell all units - remove holding
        db.delete(holding)
    else:
        holding.quantity -= quantity
        holding.current_price = price
        holding.total_investment = holding.quantity * holding.avg_price
        holding.current_value = holding.quantity * holding.current_price
        holding.pnl = holding.current_value - holding.total_investment
        holding.pnl_percent = (holding.pnl / holding.total_investment * 100) if holding.total_investment > 0 else 0
        holding.updated_at = datetime.utcnow().isoformat()
    
    # db.commit() - Controlled at route level


# ====================== TRANSACTION FUNCTIONS ======================

def create_transaction(
    db: Session,
    user_id: int,
    trans_type: str,
    total_amount: float,
    symbol: Optional[str] = None,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    order_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    status: str = "PENDING",
    confidence_score: Optional[float] = None,
    reason: Optional[str] = None
) -> Transaction:
    """Create a transaction record"""
    transaction = Transaction(
        user_id=user_id,
        type=trans_type,
        symbol=symbol,
        quantity=quantity,
        price=price,
        total_amount=total_amount,
        order_id=order_id,
        payment_id=payment_id,
        status=status,
        confidence_score=confidence_score,
        reason=reason,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(transaction)
    db.flush()
    db.refresh(transaction)
    return transaction


def get_user_transactions(db: Session, user_id: int, limit: int = 50) -> List[Transaction]:
    """Get user transactions ordered by latest first"""
    return db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.created_at.desc()).limit(limit).all()


def get_transaction_by_order_id(db: Session, order_id: str) -> Optional[Transaction]:
    """Get transaction by Razorpay order ID"""
    return db.query(Transaction).filter(Transaction.order_id == order_id).first()


def update_transaction_status(db: Session, transaction_id: int, status: str, payment_id: Optional[str] = None, signature: Optional[str] = None) -> bool:
    """Update transaction status"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return False
    
    transaction.status = status
    if payment_id:
        transaction.payment_id = payment_id
    if signature:
        transaction.signature = signature
    transaction.updated_at = datetime.utcnow().isoformat()
    # db.commit() - Controlled at route level
    return True
