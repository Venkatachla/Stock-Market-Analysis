"""
SQLAlchemy ORM models for the trading system.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    tier = Column(String, default="free", nullable=False)
    token = Column(String, nullable=True)
    is_admin = Column(Integer, default=0, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    balance = Column(Float, default=0.0, nullable=False)
    used_balance = Column(Float, default=0.0, nullable=False)
    available_balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user = relationship("User", back_populates="wallet")


class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    total_investment = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    pnl_percent = Column(Float, nullable=False)
    purchase_date = Column(String, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    
    # Unique constraint on user_id and symbol
    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', name='unique_user_stock'),
        Index('idx_user_symbol', 'user_id', 'symbol'),
    )
    
    # Relationships
    user = relationship("User", back_populates="holdings")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # BUY, SELL, DEPOSIT, WITHDRAWAL
    symbol = Column(String, nullable=True, index=True)
    quantity = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=False)
    order_id = Column(String, nullable=True)  # Razorpay order ID
    payment_id = Column(String, nullable=True)  # Razorpay payment ID
    signature = Column(String, nullable=True)  # Razorpay signature
    status = Column(String, default="PENDING", nullable=False)  # PENDING, SUCCESS, FAILED
    confidence_score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat(), index=True)
    updated_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user = relationship("User", back_populates="transactions")


# Create all tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
