# 🚨 CRITICAL BUGS QUICK REFERENCE

## System Status: ⛔ BROKEN - All Data Persistence Lost

---

## Top 3 Show-Stoppers (Fix These FIRST)

### 1️⃣ NO DATABASE COMMITS
**File:** `api/models.py` [Line 102-112]  
**Issue:** Database changes not saved  
**Fix:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()  # ✅ ADD THIS LINE
    except Exception:
        db.rollback()
    finally:
        db.close()
```
**Impact:** Without this, ALL user data (accounts, trades, payments) is lost

---

### 2️⃣ WALLET FIELDS DON'T EXIST
**File:** `api/routes.py` [Line 241-247]  
**Issue:** Code tries to access `available_balance` and `used_balance` but Wallet model only has `balance`
**Fix:** Option A - Add fields to model:
```python
# In api/models.py Wallet class:
available_balance = Column(Float, default=0.0)
used_balance = Column(Float, default=0.0)
```
Or Option B - Remove from response:
```python
return WalletResponse(balance=wallet.balance)
```
**Impact:** Every wallet query crashes with AttributeError

---

### 3️⃣ HOLDING COMPUTED FIELDS MISSING
**File:** `api/routes.py` [Line 464-473]  
**Issue:** Code accesses `current_price`, `total_investment`, `pnl`, `pnl_percent` but Holding model doesn't have these
**Fix:**
```python
# Compute in route, not on model:
for h in holdings:
    current_price = get_stock_price(h.symbol) or h.avg_price
    total_investment = h.quantity * h.avg_price
    current_value = h.quantity * current_price
    pnl = current_value - total_investment
    pnl_percent = (pnl / total_investment * 100) if total_investment > 0 else 0
```
**Impact:** Portfolio page crashes completely

---

## Database Commit Points Missing

| Endpoint | Location | Issue |
|----------|----------|-------|
| POST /auth/register | Line 168 | User not saved ⛔ |
| POST /auth/login | Line 183 | Token not saved ⛔ |
| POST /trading/buy | Line 405 | Trade not saved ⛔ |
| POST /trading/sell | Line 460 | Trade not saved ⛔ |
| POST /payment/verify | Line 301 | Deposit not saved ⛔ |
| POST /payment/create-order | Line 260 | Transaction not saved ⛔ |

**All need:** `db.commit()` before return statement

---

## Other Major Issues

| Bug | File | Fix Complexity |
|-----|------|-----------------|
| Missing `refund_to_wallet()` function | db_utils.py | 2 lines |
| No error handling for ML model loading | model_loader.py | Add raise statement |
| Hardcoded fallback predictions | predictor.py | Change confidence=0 |
| Missing CORS validation | app.py | ✓ Already OK |

---

## Quick Impact Test

```bash
# Test 1: Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'

# Check if saved in DB:
sqlite3 db.sqlite3 "SELECT COUNT(*) FROM users;"
# Expected: 1 (but probably returns 0)

# Test 2: Try to get portfolio
curl -X GET http://localhost:8000/api/portfolio \
  -H "Authorization: Bearer {token}"
# Expected: Works
# Actual: Crashes with AttributeError
```

---

## Recommended Fix Order

1. ✅ Fix `get_db()` - add `db.commit()`
2. ✅ Add commits to all 6 route handlers  
3. ✅ Fix Wallet model (add 2 fields or update response)
4. ✅ Fix Holding model (compute properties in route)
5. ✅ Add `refund_to_wallet()` function
6. ✅ Add ML error handling
7. ✅ Run system test

**Estimated Fix Time:** 30-45 minutes
**Lines Changed:** ~50 lines total
**Risk Level:** LOW (straightforward bugs)

---

## Severity Legend

- 🔴 **P0/CRITICAL** - System completely broken
- 🟠 **P1/MAJOR** - Features don't work
- 🟡 **P2/MODERATE** - Error handling poor
- 🟢 **P3/MINOR** - Code quality

