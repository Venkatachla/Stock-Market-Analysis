# 🔍 StockPulse System - Comprehensive Codebase Audit Report

**Date:** April 29, 2026  
**Scope:** Backend (FastAPI), Frontend (React), Database, ML Services  
**Status:** ⚠️ **CRITICAL ISSUES FOUND** - System has multiple show-stopping bugs

---

## Executive Summary

The StockPulse system has **16 bugs** across 4 severity levels. **3 CRITICAL bugs** completely break core functionality (authentication, trading, portfolio). Without fixes, NO user data persists in the database.

| Severity | Count | Impact |
|----------|-------|--------|
| 🔴 **P0 - CRITICAL** | 3 | System completely broken |
| 🟠 **P1 - MAJOR** | 6 | Features don't work |
| 🟡 **P2 - MODERATE** | 4 | Error handling issues |
| 🟢 **P3 - MINOR** | 3 | Code quality |

---

## 🔴 P0 - CRITICAL BUGS (SHOW STOPPERS)

### Bug #1: Missing Database Commits - All Data Lost

**Severity:** 🔴 CRITICAL  
**File:** [api/models.py](api/models.py#L102-L112)  
**Lines:** 102-112

```python
def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # ❌ NO db.commit() - CHANGES ARE LOST
```

**Problem:**
- FastAPI yields the database session to routes
- Routes make changes (users, balances, trades)
- Session closes WITHOUT committing
- All modifications are discarded

**Consequence:**
- ✗ User registrations are lost
- ✗ Wallet deposits are lost  
- ✗ Buy/sell trades are lost
- ✗ Holdings never update
- **Result:** User sees "success" but nothing persists

**Fix Required:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()  # ✅ COMMIT BEFORE CLOSING
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

---

### Bug #2: Wallet Model Missing Fields - Backend Response Broken

**Severity:** 🔴 CRITICAL  
**Files:** 
- [api/routes.py](api/routes.py#L241-L247) - attempting to access
- [api/models.py](api/models.py#L39-L47) - definition

**Issue Location - Routes (Line 241-247):**
```python
return WalletResponse(
    balance=wallet.balance,                    # ✓ EXISTS
    available_balance=wallet.available_balance,# ❌ DOESN'T EXIST
    used_balance=wallet.used_balance           # ❌ DOESN'T EXIST
)
```

**Database Model Definition (Line 39-47):**
```python
class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    balance = Column(Float, default=0.0, nullable=False)  # ✓ ONLY THIS FIELD
    created_at = Column(String, nullable=False, ...)
    updated_at = Column(String, nullable=False, ...)
```

**Problem:**
- Wallet table only has `balance` column
- Routes try to access `available_balance` and `used_balance`
- These columns don't exist in database
- AttributeError on every wallet query

**Affected Endpoints:**
- `GET /api/wallet` - crashes
- `GET /api/portfolio` - crashes  
- `POST /api/trading/buy` - crashes when checking balance
- `POST /api/trading/sell` - crashes when checking balance

**Stack Trace Example:**
```
AttributeError: 'Wallet' object has no attribute 'available_balance'
```

**Options to Fix:**
1. **Option A:** Add columns to Wallet table
   ```python
   available_balance = Column(Float, default=0.0)
   used_balance = Column(Float, default=0.0)
   ```

2. **Option B:** Remove from response (simpler)
   ```python
   return WalletResponse(balance=wallet.balance)
   ```

---

### Bug #3: Holding Model Missing Computed Properties

**Severity:** 🔴 CRITICAL  
**File:** [api/routes.py](api/routes.py#L464-L473)  
**Lines:** 464-473

**Problem Code:**
```python
holdings_response = [
    HoldingResponse(
        symbol=h.symbol,              # ✓ EXISTS
        quantity=h.quantity,          # ✓ EXISTS
        avg_price=h.avg_price,        # ✓ EXISTS
        current_price=h.current_price,# ❌ NOT IN MODEL
        total_investment=h.total_investment,  # ❌ NOT IN MODEL
        current_value=h.current_value,       # ❌ NOT IN MODEL
        pnl=h.pnl,                   # ❌ NOT IN MODEL
        pnl_percent=h.pnl_percent    # ❌ NOT IN MODEL
    )
    for h in holdings
]
```

**Database Model Definition** [api/models.py](api/models.py#L50-L63):
```python
class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    avg_price = Column(Float, nullable=False)
    purchase_date = Column(String, nullable=False)
    # ❌ NO current_price, total_investment, current_value, pnl, pnl_percent
```

**Problem:**
- Holding model only stores `quantity` and `avg_price`
- Missing: live prices, P&L calculations
- These are computed values, not stored
- Accessing them as attributes crashes code

**Affected Endpoints:**
- `GET /api/portfolio` - CRASHES when building response
- Portfolio page - completely broken

**Fix Required:**
```python
# Calculate properties in the route, not on model
for h in holdings:
    current_price = get_stock_price(h.symbol)  # Fetch live price
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
```

---

## 🟠 P1 - MAJOR BUGS (FEATURES BROKEN)

### Bug #4: Buy Transaction Never Committed

**Severity:** 🟠 MAJOR  
**File:** [api/routes.py](api/routes.py#L340-L405)  
**Lines:** 340-405

**Problem:**
```python
@router.post("/trading/buy")
def buy_stock(request: BuyRequest, ...):
    # ... validation ...
    
    # Deduct from wallet - IN MEMORY ONLY
    if not deduct_from_wallet(db, current_user.id, total_cost):
        raise HTTPException(...)
    
    # Update holding - IN MEMORY ONLY
    try:
        holding = get_or_create_holding(db, current_user.id, request.symbol)
        update_holding_after_buy(db, holding, request.quantity, price)
    except Exception as e:
        refund_to_wallet(db, current_user.id, total_cost)
        raise HTTPException(...)
    
    # Create transaction - IN MEMORY ONLY
    transaction = create_transaction(db, ...)
    
    # ❌ NO db.commit() - NOTHING SAVED!
    
    return {
        "status": "success",  # ✓ Returns success to frontend
        "message": "Bought shares"  # But nothing is in database!
    }
```

**Flow:**
1. User clicks "BUY" → successful API response
2. Frontend shows "Bought 10 shares"
3. User refreshes → holdings gone
4. Wallet not debited

**Root Cause:** Missing `db.commit()` after all modifications

**Fix:**
```python
    db.commit()  # ✅ ADD THIS
    
    return { "status": "success", ... }
```

---

### Bug #5: Sell Transaction Never Committed

**Severity:** 🟠 MAJOR  
**File:** [api/routes.py](api/routes.py#L410-L460)  
**Lines:** 410-460

**Same Issue as Bug #4 - No db.commit()**

**Fix:**
```python
    db.commit()  # ✅ ADD THIS
    
    return { "status": "success", ... }
```

---

### Bug #6: Payment Verification Never Committed

**Severity:** 🟠 MAJOR  
**File:** [api/routes.py](api/routes.py#L265-L301)  
**Lines:** 265-301

**Problem:**
```python
@router.post("/payment/verify")
def verify_payment(request: VerifyPaymentRequest, ...):
    # ... verification checks ...
    
    # Add money to wallet - IN MEMORY ONLY
    amount = payment_details["amount"]
    if not add_to_wallet(db, current_user.id, amount):
        raise HTTPException(...)
    
    # Update transaction status - IN MEMORY ONLY
    update_transaction_status(
        db,
        transaction.id,
        "SUCCESS",
        request.payment_id,
        request.signature
    )
    
    # ❌ NO db.commit() - PAYMENT NOT RECORDED!
    
    print(f"[PAYMENT] User {current_user.email} deposited ₹{amount}...")
    return {
        "status": "success",
        "message": f"₹{amount} added to wallet"  # Success message, but balance not saved!
    }
```

**Scenario:**
1. User completes payment ✓
2. Payment verified ✓
3. API returns "₹1000 added to wallet"
4. User refreshes → balance unchanged
5. Money "lost"

**Fix:**
```python
    db.commit()  # ✅ ADD THIS
    
    return { "status": "success", ... }
```

---

### Bug #7: User Signup Never Committed

**Severity:** 🟠 MAJOR  
**File:** [api/routes.py](api/routes.py#L153-L168)  
**Lines:** 153-168

**Problem:**
```python
@router.post("/auth/register", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # ... validation ...
    
    # Create user - IN MEMORY ONLY
    user = create_user(db, request.email, request.password, tier="free", is_admin=0)
    
    # Create token - IN MEMORY ONLY
    token = create_access_token(user.email, user.id)
    
    # Update user token - IN MEMORY ONLY
    update_user_token(db, user.id, token)
    
    # ❌ NO db.commit() - USER NOT SAVED!
    
    return AuthResponse(
        token=token,
        email=user.email,
        tier=user.tier,
        is_admin=bool(user.is_admin)
    )
```

**Scenario:**
1. New user registers
2. Gets JWT token ✓
3. Database session closes
4. User record lost
5. Token is invalid next request (user not found in DB)

**Fix:**
```python
    db.commit()  # ✅ ADD THIS
    
    return AuthResponse(...)
```

---

### Bug #8: User Login Never Committed

**Severity:** 🟠 MAJOR  
**File:** [api/routes.py](api/routes.py#L171-L183)  
**Lines:** 171-183

**Problem:**
```python
@router.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = verify_user_password(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create new token - IN MEMORY ONLY
    token = create_access_token(user.email, user.id)
    
    # Update user token field - IN MEMORY ONLY
    update_user_token(db, user.id, token)
    
    # ❌ NO db.commit() - NEW TOKEN NOT SAVED!
    
    return AuthResponse(token=token, ...)
```

**Issue:** Token updated but not persisted

**Fix:**
```python
    db.commit()  # ✅ ADD THIS
    
    return AuthResponse(...)
```

---

### Bug #9: Frontend Expects Wallet Properties That Don't Exist

**Severity:** 🟠 MAJOR  
**File:** [frontend/src/pages/Portfolio.tsx](frontend/src/pages/Portfolio.tsx#L62-L66)  
**Lines:** 62-66

**Problem:**
```typescript
const wallet = useMemo(() => {
    if (!rawWallet) return null;
    return {
        total_balance: typeof rawWallet.total_balance === 'string' ? ... : rawWallet.total_balance,
        available_balance: typeof rawWallet.available_balance === 'string' ? ... : rawWallet.available_balance, // ❌ DOESN'T EXIST
        used_balance: typeof rawWallet.used_balance === 'string' ? ... : rawWallet.used_balance, // ❌ DOESN'T EXIST
    };
}, [rawWallet]);
```

**API Response Actually Returns:**
```json
{
    "balance": 5000.00,
    "available_balance": null,  // undefined
    "used_balance": null        // undefined
}
```

**Impact:**
- Wallet display shows undefined
- Portfolio page looks broken
- User can't see balance

**Fix:** Backend must return matching fields (see Bug #2)

---

### Bug #10: Missing refund_to_wallet() Function

**Severity:** 🟠 MAJOR  
**File:** [api/routes.py](api/routes.py#L386-L389)  
**Referenced in:** Buy endpoint

**Problem:**
```python
# In buy_stock route (line 386):
refund_to_wallet(db, current_user.id, total_cost)
```

But function not defined in [api/db_utils.py](api/db_utils.py)

**Consequence:**
- Buy fails → tries to refund → NameError
- User sees error instead of proper rollback
- Wallet changes may not be reversed

**Fix:** Implement in db_utils.py
```python
def refund_to_wallet(db: Session, user_id: int, amount: float) -> bool:
    """Refund money to wallet (rollback on trade failure)"""
    return add_to_wallet(db, user_id, amount)
```

---

## 🟡 P2 - MODERATE BUGS (Error Handling Issues)

### Bug #11: No Error Handling for ML Model Loading Failure

**Severity:** 🟡 MODERATE  
**File:** [api/services/model_loader.py](api/services/model_loader.py#L50-L56)  
**Lines:** 50-56

**Problem:**
```python
def load_all_models(self) -> bool:
    # ... attempt to load models ...
    
    if models_loaded == 0:
        logger.warning("No models loaded successfully. System will use dummy predictions.")
        return False  # ⚠️ Returns False silently
```

**Consequence:**
- If no ML models load (disk error, missing files)
- System doesn't fail - it just continues
- Predictor returns fake NEUTRAL signals
- User doesn't know signals are fake

**Better Handling:**
```python
if models_loaded == 0:
    logger.error("CRITICAL: No ML models loaded. Trading signals are disabled.")
    # Option 1: Raise exception to fail startup
    # Option 2: Mark trading as disabled in API responses
    # Option 3: Fallback to simple heuristic models
    raise RuntimeError("ML models not available")
```

---

### Bug #12: Predictor Returns Hardcoded Predictions When No Models Loaded

**Severity:** 🟡 MODERATE  
**File:** [api/services/predictor.py](api/services/predictor.py#L43-L50)  
**Lines:** 43-50

**Problem:**
```python
def predict(self, features: np.ndarray) -> PredictionResult:
    models = self.model_loader.get_all_models()
    
    if len(models) == 0:
        logger.warning("No models available - returning NEUTRAL signal")
        return PredictionResult(
            signal="NEUTRAL",
            confidence=50.0,  # ⚠️ HARDCODED!
            models_output={}
        )
```

**Issue:**
- When models unavailable, system returns `confidence=50.0`
- Frontend can't tell this is a fallback
- User thinks it's a real prediction
- Base rate accuracy (50% up/down) looks legitimate

**Fix:**
```python
if len(models) == 0:
    logger.warning("No models available - trading signals disabled")
    return PredictionResult(
        signal="UNAVAILABLE",  # ✓ Indicate unavailability
        confidence=0.0,        # ✓ Zero confidence
        models_output={"error": "Models not loaded"}
    )
```

---

### Bug #13: No Error Handling for Transaction Creation

**Severity:** 🟡 MODERATE  
**File:** [api/routes.py](api/routes.py#L401-L405] (buy endpoint), similarly in sell  
**Lines:** 401-405

**Problem:**
```python
# After successful wallet and holding updates:
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
# ⚠️ No try/catch - if this fails, trade is processed but not logged
```

**Issue:**
- If transaction creation fails, buy still happened
- No record of the trade
- Audit trail broken

**Fix:**
```python
try:
    transaction = create_transaction(db, ...)
except Exception as e:
    logger.error(f"Transaction creation failed: {e}")
    db.rollback()
    raise HTTPException(status_code=500, detail="Trade failed during logging")
```

---

### Bug #14: No Null Checks on Current Price in Portfolio

**Severity:** 🟡 MODERATE  
**File:** [api/routes.py](api/routes.py#L464-L475) (implied issue)

**Problem:**
```python
# In portfolio endpoint:
holdings = get_user_holdings(db, current_user.id)

total_value = sum(h.current_value for h in holdings)  # ❌ current_value not computed
```

If we try to compute P&L without fetching live prices, we get None/KeyError

**Fix:** Must fetch all prices with error handling
```python
for h in holdings:
    try:
        current_price = get_stock_price(h.symbol)
        if current_price is None:
            current_price = h.avg_price  # Fallback
    except:
        current_price = h.avg_price
    
    # Now compute P&L
```

---

## 🟢 P3 - MINOR BUGS (Code Quality)

### Bug #15: Transaction Creation Error Not Handled on Login

**Severity:** 🟢 MINOR  
**File:** [api/routes.py](api/routes.py#L171-183)  
**Issue:** No try/catch around token update

**Impact:** Minimal - if token update fails, user just doesn't get a token

**Fix:**
```python
try:
    update_user_token(db, user.id, token)
    db.commit()
except Exception as e:
    logger.error(f"Token update failed: {e}")
    raise HTTPException(status_code=500, detail="Login failed")
```

---

### Bug #16: No Validation of Stock Symbol Before Trading

**Severity:** 🟢 MINOR  
**File:** [api/routes.py](api/routes.py#L350-360] (buy endpoint)

**Issue:**
```python
def buy_stock(request: BuyRequest, ...):
    # ❌ No validation that symbol is real
    price = get_stock_price(request.symbol)
    if price is None:
        raise HTTPException(...)
```

**Problem:**
- User could try buying "FAKESTK"
- get_stock_price returns None
- User gets vague error message

**Better:**
```python
if not is_valid_symbol(request.symbol):
    raise HTTPException(status_code=400, detail=f"Unknown symbol: {request.symbol}")
```

---

## 📊 Bug Distribution

```
Backend Routes (api/routes.py)         11 bugs
Database Models (api/models.py)        2 bugs  
ML Services (api/services/)            2 bugs
Frontend Pages (frontend/src/pages/)   1 bug

Total: 16 bugs
```

---

## 🔧 Fix Priority Order

1. **FIRST** (Blocks everything):
   - Add `db.commit()` to get_db() function
   - Add `db.commit()` to all route handlers

2. **SECOND** (Blocks authentication):
   - Fix Wallet model fields mismatch
   - Fix Holding model computed properties

3. **THIRD** (Blocks trading):
   - Implement `refund_to_wallet()` function
   - Add error handling for transaction creation

4. **FOURTH** (Quality):
   - Add ML model loading error handling
   - Add validation for stock symbols

---

## ✅ Verified Working

- ✓ CORS headers properly configured
- ✓ Password hashing using SHA256 + bcrypt support
- ✓ JWT token generation and verification
- ✓ Frontend error boundaries and null checks
- ✓ Stock price fetching from Yahoo Finance

---

## 📝 Files Affected

### Critical Changes Needed:
- `api/models.py` - Add commits to get_db()
- `api/routes.py` - Add commits + fix response models
- `api/db_utils.py` - Add refund_to_wallet() function
- `api/models.py` - Update Wallet model schema

### Would Benefit From Changes:
- `api/services/model_loader.py` - Better error handling
- `api/services/predictor.py` - Fallback signal handling
- `frontend/src/pages/Portfolio.tsx` - Handle missing fields

---

## 🎯 Testing Recommendations

After fixes, verify with:

```bash
# 1. Test user registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# 2. Verify user exists in database
sqlite3 db.sqlite3 "SELECT * FROM users WHERE email='test@example.com';"

# 3. Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# 4. Test wallet endpoint
curl -X GET http://localhost:8000/api/wallet \
  -H "Authorization: Bearer {token}"

# 5. Test buy endpoint
curl -X POST http://localhost:8000/api/trading/buy \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"INFY","quantity":1}'

# 6. Verify holding persisted
sqlite3 db.sqlite3 "SELECT * FROM holdings WHERE user_id=1;"
```

---

## 📌 Conclusion

The StockPulse system has **critical database persistence issues** that prevent any user data from being saved. The architecture is sound, but implementation has fundamental gaps:

1. **No database commits** = All user actions are lost
2. **Model/Response mismatch** = API crashes on data access  
3. **No fallback handling** = System fails silently

**Recommendation:** Fix database commit issues FIRST, then address model mismatches. These two fixes alone will enable the core functionality.
