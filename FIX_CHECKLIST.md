# 📋 StockPulse Audit - Fix Checklist

## Pre-Fix Verification

```bash
# Run the audit validation script to identify all issues
python verify_audit_fixes.py

# Expected output (before fixes):
# ❌ FAIL: Database Commits
# ❌ FAIL: Wallet Model  
# ❌ FAIL: Wallet Response
# ❌ FAIL: Buy Endpoint
# ❌ FAIL: Portfolio Endpoint
```

---

## Fix Implementation Order

### PHASE 1: Database Persistence (Blocks Everything)

#### [ ] Fix #1: Add Database Commits to get_db()

**File:** `api/models.py`  
**Lines:** 102-112  
**Priority:** 🔴 CRITICAL

**Current:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Fixed:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

**Verification:**
```bash
grep -n "db.commit()" api/models.py | grep -A2 "get_db"
# Should show: db.commit() inside get_db function
```

---

### PHASE 2: Fix Model/Response Mismatches

#### [ ] Fix #2: Update Wallet Model Fields

**File:** `api/models.py`  
**Lines:** 39-47  
**Priority:** 🔴 CRITICAL

**Option A - Add Missing Columns (if you want available_balance tracking):**

```python
class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    balance = Column(Float, default=0.0, nullable=False)
    available_balance = Column(Float, default=0.0, nullable=False)  # ✅ ADD
    used_balance = Column(Float, default=0.0, nullable=False)       # ✅ ADD
    created_at = Column(String, nullable=False, default=...)
    updated_at = Column(String, nullable=False, default=...)
    
    user = relationship("User", back_populates="wallet")
```

Then add database migration:
```sql
ALTER TABLE wallets ADD COLUMN available_balance FLOAT DEFAULT 0.0;
ALTER TABLE wallets ADD COLUMN used_balance FLOAT DEFAULT 0.0;
```

**OR Option B - Simplify Response (Simpler):**

Update `api/routes.py` lines 241-247:
```python
return WalletResponse(
    balance=wallet.balance
    # Remove: available_balance, used_balance
)
```

Update `api/routes.py` lines 47-49:
```python
class WalletResponse(BaseModel):
    balance: float
    # Remove: available_balance, used_balance
```

**Recommendation:** Use Option B (simpler, fewer changes)

**Verification:**
```bash
# Check that response matches model
grep -A3 "class WalletResponse" api/routes.py
grep -A5 "class Wallet" api/models.py
# Should have same fields
```

---

#### [ ] Fix #3: Update Holding Response Model

**File:** `api/routes.py`  
**Lines:** 48-58  
**Priority:** 🔴 CRITICAL

**Current:**
```python
class HoldingResponse(BaseModel):
    symbol: str
    quantity: int
    avg_price: float
    current_price: float        # ❌ Computed, not in DB
    total_investment: float     # ❌ Computed, not in DB
    current_value: float        # ❌ Computed, not in DB
    pnl: float                  # ❌ Computed, not in DB
    pnl_percent: float          # ❌ Computed, not in DB
    purchase_date: str
```

**Note:** Response model is OK, but route must compute values before returning.

**Verification:** See Fix #4 below.

---

### PHASE 3: Add Missing Computations

#### [ ] Fix #4: Compute Holding Properties in Portfolio Endpoint

**File:** `api/routes.py`  
**Lines:** 460-480  
**Priority:** 🔴 CRITICAL

**Current (BROKEN):**
```python
holdings_response = [
    HoldingResponse(
        symbol=h.symbol,
        quantity=h.quantity,
        avg_price=h.avg_price,
        current_price=h.current_price,  # ❌ DOESN'T EXIST
        total_investment=h.total_investment,  # ❌ DOESN'T EXIST
        current_value=h.current_value,  # ❌ DOESN'T EXIST
        pnl=h.pnl,  # ❌ DOESN'T EXIST
        pnl_percent=h.pnl_percent,  # ❌ DOESN'T EXIST
        purchase_date=h.purchase_date
    )
    for h in holdings
]
```

**Fixed:**
```python
holdings_response = []
for h in holdings:
    # Fetch live price
    try:
        current_price = get_stock_price(h.symbol)
    except:
        current_price = h.avg_price
    
    if current_price is None:
        current_price = h.avg_price
    
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
```

**Verification:**
```bash
# Test portfolio endpoint
curl -X GET http://localhost:8000/api/portfolio \
  -H "Authorization: Bearer {token}"
# Should return holdings with valid current_price, pnl, etc.
```

---

### PHASE 4: Add Missing Database Commits to Routes

#### [ ] Fix #5: Add Commit to Signup Route

**File:** `api/routes.py`  
**Lines:** 153-168  
**Priority:** 🟠 MAJOR

**Current:**
```python
@router.post("/auth/register", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # ... validation ...
    user = create_user(db, request.email, request.password, tier="free", is_admin=0)
    token = create_access_token(user.email, user.id)
    update_user_token(db, user.id, token)
    # ❌ NO COMMIT
    return AuthResponse(...)
```

**Fixed:**
```python
@router.post("/auth/register", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # ... validation ...
    user = create_user(db, request.email, request.password, tier="free", is_admin=0)
    token = create_access_token(user.email, user.id)
    update_user_token(db, user.id, token)
    db.commit()  # ✅ ADD THIS
    return AuthResponse(...)
```

---

#### [ ] Fix #6: Add Commit to Login Route

**File:** `api/routes.py`  
**Lines:** 171-183  
**Priority:** 🟠 MAJOR

**Add `db.commit()` before return statement**

---

#### [ ] Fix #7: Add Commit to Buy Route

**File:** `api/routes.py`  
**Line:** 405  
**Priority:** 🟠 MAJOR

**Add `db.commit()` before return statement**

---

#### [ ] Fix #8: Add Commit to Sell Route

**File:** `api/routes.py`  
**Line:** 460  
**Priority:** 🟠 MAJOR

**Add `db.commit()` before return statement**

---

#### [ ] Fix #9: Add Commit to Payment Verify Route

**File:** `api/routes.py`  
**Line:** 301  
**Priority:** 🟠 MAJOR

**Add `db.commit()` before return statement**

---

#### [ ] Fix #10: Add Commit to Create Order Route

**File:** `api/routes.py`  
**Line:** 260  
**Priority:** 🟠 MAJOR

**Add `db.commit()` after `create_transaction()` call**

---

### PHASE 5: Fix Missing Functions

#### [ ] Fix #11: Implement refund_to_wallet()

**File:** `api/db_utils.py`  
**Location:** After `add_to_wallet()` function  
**Priority:** 🟠 MAJOR

**Add:**
```python
def refund_to_wallet(db: Session, user_id: int, amount: float) -> bool:
    """Refund money to wallet (used for trade rollback)"""
    wallet = get_wallet(db, user_id)
    if not wallet:
        return False
    
    wallet.balance += amount
    wallet.updated_at = datetime.utcnow().isoformat()
    return True
```

---

### PHASE 6: Error Handling Improvements

#### [ ] Fix #12: Add Error Handling to ML Model Loading (Optional)

**File:** `api/services/model_loader.py`  
**Lines:** 50-56  
**Priority:** 🟡 MODERATE

**Add:**
```python
if models_loaded == 0:
    logger.error("CRITICAL: No ML models loaded. Trading signals disabled.")
    # System continues but with degraded functionality
    return False
```

---

#### [ ] Fix #13: Update Predictor Fallback (Optional)

**File:** `api/services/predictor.py`  
**Lines:** 43-50  
**Priority:** 🟡 MODERATE

**Change:**
```python
if len(models) == 0:
    return PredictionResult(
        signal="UNAVAILABLE",  # Not just NEUTRAL
        confidence=0.0,        # Not 50.0
        models_output={"error": "ML models not available"}
    )
```

---

## Verification Steps

### Step 1: Run Syntax Check
```bash
python -m py_compile api/models.py
python -m py_compile api/routes.py
python -m py_compile api/db_utils.py
```

### Step 2: Run Audit Validation Script
```bash
python verify_audit_fixes.py
# Expected: All tests should PASS
```

### Step 3: Start Server and Test
```bash
# Start backend
python -m uvicorn api.app:app --reload

# In another terminal:
# Test registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Response should be:
# {"token":"...", "email":"test@example.com", "tier":"free", "is_admin":false}

# Verify user saved in database
sqlite3 db.sqlite3 "SELECT COUNT(*) FROM users WHERE email='test@example.com';"
# Should return: 1 (not 0)
```

### Step 4: Test Trading Endpoint
```bash
# Get token from login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | jq -r '.token')

# Deposit money (mock payment)
# First need wallet with balance - test buy with insufficient balance
curl -X POST http://localhost:8000/api/trading/buy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"INFY","quantity":1}'
# Should fail with "Insufficient balance"

# Verify transaction attempted but failed
sqlite3 db.sqlite3 "SELECT * FROM transactions ORDER BY id DESC LIMIT 1;"
# Should show FAILED status
```

### Step 5: Full System Test
```bash
# Run included test
python FINAL_TEST.py

# Expected: 8/8 tests PASS
```

---

## Rollback Plan (If Issues Arise)

### Option 1: Revert Changes
```bash
git diff  # See what changed
git checkout -- .  # Revert to original
```

### Option 2: Restore Database
```bash
rm db.sqlite3
# System will recreate empty database on next run
```

---

## Summary

| Phase | Fixes | Time Est. | Impact |
|-------|-------|----------|--------|
| Phase 1 | #1 | 2 min | Enables persistence |
| Phase 2 | #2-3 | 5 min | Fixes wallet/holding |
| Phase 3 | #4 | 10 min | Fixes portfolio |
| Phase 4 | #5-10 | 10 min | Saves all trades |
| Phase 5 | #11 | 3 min | Enables rollbacks |
| Phase 6 | #12-13 | 5 min | Better errors |

**Total Time: ~35 minutes**

**Total Lines Changed: ~100 lines**

**Risk Level: LOW** (straightforward bug fixes)

---

## Success Criteria

- [ ] `verify_audit_fixes.py` returns 100% pass
- [ ] User registration persists in database
- [ ] Stock purchases persist in database
- [ ] Wallet balance updates persist
- [ ] Portfolio shows current prices and P&L
- [ ] All 8 FINAL_TEST.py tests pass

**Status After Fixes:** ✅ PRODUCTION READY
