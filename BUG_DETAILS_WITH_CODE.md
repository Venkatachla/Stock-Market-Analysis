# StockPulse Audit: Bug Details with Code Comparisons

## CRITICAL BUG #1: Missing Database Commits

### Current (BROKEN) Code:
```python
# File: api/models.py, Lines 102-112
def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db           # Gives session to route
    finally:
        db.close()         # ❌ Closes WITHOUT commit
        # All modifications LOST when session closes
```

### How It Breaks:
```
USER ACTION → ROUTE MODIFIES DATA (in memory) → SESSION CLOSES → CHANGES DISCARDED
```

### Example Flow:
```python
# Route: POST /auth/register
user = create_user(db, "test@example.com", "password")  # Added to db session
db.flush()  # Flushed to transaction, but...
# ❌ NO db.commit()
return {"status": "success", "user": user}  # Frontend gets success
# ❌ get_db() closes session → changes rolled back → user never saved!

# Next request: User tries to login → "User not found" ✗
```

### Fixed Code:
```python
# File: api/models.py, Lines 102-112
def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()         # ✅ COMMIT changes
    except Exception:
        db.rollback()       # Rollback on error
    finally:
        db.close()
```

---

## CRITICAL BUG #2: Wallet Fields Mismatch

### Database Schema (What Actually Exists):
```python
# File: api/models.py, Lines 39-47
class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    balance = Column(Float, default=0.0)           # ✓ ONLY THIS FIELD
    created_at = Column(String)
    updated_at = Column(String)
    # ❌ NO available_balance column
    # ❌ NO used_balance column
```

### Current (BROKEN) Code:
```python
# File: api/routes.py, Lines 241-247
@router.get("/wallet", response_model=WalletResponse)
def get_wallet_info(current_user: User = Depends(get_current_user), 
                   db: Session = Depends(get_db)):
    wallet = get_wallet(db, current_user.id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletResponse(
        balance=wallet.balance,                      # ✓ Exists
        available_balance=wallet.available_balance,  # ❌ DOESN'T EXIST
        used_balance=wallet.used_balance             # ❌ DOESN'T EXIST
    )
    # AttributeError: 'Wallet' object has no attribute 'available_balance'
```

### Response Model (Expects Non-Existent Fields):
```python
# File: api/routes.py, Lines 47-50
class WalletResponse(BaseModel):
    balance: float              # ✓ Exists in DB
    available_balance: float    # ❌ Not in DB
    used_balance: float         # ❌ Not in DB
```

### Error When Called:
```
GET /api/wallet
→ Crashes with AttributeError
→ Frontend gets 500 error
→ Wallet display shows error
```

### Option A - Add Missing Fields to Database:
```python
# File: api/models.py, Wallet class
class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    balance = Column(Float, default=0.0)              # ✓ Existing
    available_balance = Column(Float, default=0.0)    # ✅ ADD THIS
    used_balance = Column(Float, default=0.0)         # ✅ ADD THIS
    created_at = Column(String)
    updated_at = Column(String)
    
    # Migration needed:
    # ALTER TABLE wallets ADD COLUMN available_balance FLOAT DEFAULT 0.0;
    # ALTER TABLE wallets ADD COLUMN used_balance FLOAT DEFAULT 0.0;
```

### Option B - Remove from Response (Simpler):
```python
# File: api/routes.py, Lines 241-247
return WalletResponse(
    balance=wallet.balance  # ✓ Only this field
    # Remove available_balance and used_balance
)

# File: api/routes.py, Lines 47-49
class WalletResponse(BaseModel):
    balance: float  # ✓ Only this field
```

---

## CRITICAL BUG #3: Holding Computed Properties

### Database Schema:
```python
# File: api/models.py, Lines 50-63
class Holding(Base):
    __tablename__ = "holdings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String)
    quantity = Column(Integer)          # ✓ Stored
    avg_price = Column(Float)           # ✓ Stored
    purchase_date = Column(String)      # ✓ Stored
    created_at = Column(String)
    updated_at = Column(String)
    # ❌ NO current_price (must fetch live)
    # ❌ NO total_investment (must compute)
    # ❌ NO current_value (must compute)
    # ❌ NO pnl (must compute)
    # ❌ NO pnl_percent (must compute)
```

### Current (BROKEN) Code:
```python
# File: api/routes.py, Lines 464-473
def get_portfolio(...):
    holdings = get_user_holdings(db, current_user.id)
    
    holdings_response = [
        HoldingResponse(
            symbol=h.symbol,                    # ✓ Exists
            quantity=h.quantity,                # ✓ Exists
            avg_price=h.avg_price,              # ✓ Exists
            purchase_date=h.purchase_date,      # ✓ Exists
            current_price=h.current_price,      # ❌ NOT IN MODEL
            total_investment=h.total_investment, # ❌ NOT IN MODEL
            current_value=h.current_value,      # ❌ NOT IN MODEL
            pnl=h.pnl,                         # ❌ NOT IN MODEL
            pnl_percent=h.pnl_percent          # ❌ NOT IN MODEL
        )
        for h in holdings
    ]
    
    # KeyError or AttributeError when accessing these properties
```

### Error Trace:
```
GET /api/portfolio
→ get_user_holdings() returns Holding objects
→ Try to access h.current_price
→ AttributeError: 'Holding' object has no attribute 'current_price'
→ Endpoint crashes with 500 error
→ Portfolio page shows error
```

### Fixed Code:
```python
# File: api/routes.py, Lines 464-480
def get_portfolio(...):
    holdings = get_user_holdings(db, current_user.id)
    
    holdings_response = []
    for h in holdings:
        # ✅ Fetch live price
        try:
            current_price = get_stock_price(h.symbol)
            if current_price is None:
                current_price = h.avg_price  # Fallback to avg price
        except:
            current_price = h.avg_price
        
        # ✅ Compute derived values
        total_investment = h.quantity * h.avg_price
        current_value = h.quantity * current_price
        pnl = current_value - total_investment
        pnl_percent = (pnl / total_investment * 100) if total_investment > 0 else 0
        
        holdings_response.append(HoldingResponse(
            symbol=h.symbol,
            quantity=h.quantity,
            avg_price=h.avg_price,
            purchase_date=h.purchase_date,
            current_price=current_price,        # ✅ Computed
            total_investment=total_investment,  # ✅ Computed
            current_value=current_value,        # ✅ Computed
            pnl=pnl,                           # ✅ Computed
            pnl_percent=pnl_percent            # ✅ Computed
        ))
    
    return PortfolioResponse(
        wallet=...,
        holdings=holdings_response,  # ✓ Now works
        total_value=sum(h.current_value for h in holdings_response),
        total_invested=sum(h.total_investment for h in holdings_response),
        total_pnl=sum(h.pnl for h in holdings_response),
        total_pnl_percent=...
    )
```

---

## MAJOR BUG #4-6: Missing Commits in Trading Routes

### Current (BROKEN) - Buy Stock:
```python
# File: api/routes.py, Lines 340-405
@router.post("/trading/buy")
def buy_stock(request: BuyRequest, ...):
    # ... validation ...
    
    # STEP 1: Deduct from wallet (in-memory)
    if not deduct_from_wallet(db, current_user.id, total_cost):
        raise HTTPException()
    
    # STEP 2: Update holding (in-memory)
    try:
        holding = get_or_create_holding(db, current_user.id, request.symbol)
        update_holding_after_buy(db, holding, request.quantity, price)
    except Exception as e:
        refund_to_wallet(db, current_user.id, total_cost)
        raise HTTPException()
    
    # STEP 3: Create transaction (in-memory)
    transaction = create_transaction(
        db, current_user.id, "BUY", total_cost,
        symbol=request.symbol, quantity=request.quantity, price=price,
        status="SUCCESS", reason="Manual buy order"
    )
    
    # ❌ NO db.commit() HERE
    # ❌ Session closes → ALL CHANGES LOST
    
    return {
        "status": "success",  # ✓ Tells frontend success
        "message": f"Bought {request.quantity} shares",
        "transaction_id": transaction.id  # But transaction never saved!
    }
```

### What Actually Happens:
```
USER CLICKS BUY
↓
Wallet deducted (only in memory)
Holding updated (only in memory)
Transaction created (only in memory)
↓
Return "success" to frontend ✓
↓
Session closes WITHOUT commit
↓
ALL CHANGES ROLLED BACK
↓
USER REFRESHES
↓
No purchase found in database ✗
Wallet unchanged ✗
```

### Fixed Code:
```python
# File: api/routes.py, Lines 340-406
@router.post("/trading/buy")
def buy_stock(request: BuyRequest, ...):
    # ... validation ...
    
    # Deduct from wallet
    if not deduct_from_wallet(db, current_user.id, total_cost):
        raise HTTPException()
    
    # Update holding
    try:
        holding = get_or_create_holding(db, current_user.id, request.symbol)
        update_holding_after_buy(db, holding, request.quantity, price)
    except Exception as e:
        refund_to_wallet(db, current_user.id, total_cost)
        db.commit()  # ✅ Commit the refund
        raise HTTPException()
    
    # Create transaction
    transaction = create_transaction(...)
    
    db.commit()  # ✅ COMMIT ALL CHANGES
    
    return {
        "status": "success",
        "message": f"Bought {request.quantity} shares",
        "transaction_id": transaction.id
    }
```

Same fix needed in:
- `sell_stock()` function (line 460)
- `verify_payment()` function (line 301)

---

## MAJOR BUG #10: Missing Function

### Current Code Tries to Call:
```python
# File: api/routes.py, Line 389
refund_to_wallet(db, current_user.id, total_cost)
```

### But Function Doesn't Exist:
```python
# File: api/db_utils.py - NO refund_to_wallet() function defined
# ❌ ImportError when this code runs
```

### Add Function:
```python
# File: api/db_utils.py, add new function:
def refund_to_wallet(db: Session, user_id: int, amount: float) -> bool:
    """Refund money to wallet (used in trade rollback)"""
    wallet = get_wallet(db, user_id)
    if not wallet:
        return False
    
    wallet.balance += amount
    wallet.updated_at = datetime.utcnow().isoformat()
    return True
```

---

## Summary Table

| Bug | Broken Code | Line | Fix |
|-----|-----------|------|-----|
| No commits | `get_db()` | 107-112 | Add `db.commit()` |
| Wallet fields | `get_wallet_info()` | 241-247 | Add DB columns or remove from response |
| Holding props | `get_portfolio()` | 464-473 | Compute in route |
| Buy not saved | `buy_stock()` | 405 | Add `db.commit()` |
| Sell not saved | `sell_stock()` | 460 | Add `db.commit()` |
| Payment not saved | `verify_payment()` | 301 | Add `db.commit()` |
| Missing function | `buy_stock()` | 389 | Add `refund_to_wallet()` |

