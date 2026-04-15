# ✅ STOCKPULSE - COMPLETE STARTUP GUIDE

## Phase 1: Backend Setup

### Step 1.1: Install Dependencies
```bash
cd c:\Users\Venkatachala\ V\STCOK
pip install fastapi uvicorn pydantic python-jose passlib sqlalchemy
```

### Step 1.2: Create `.env` File
```bash
# Create .env in root directory with:
SECRET_KEY=your-secret-key-change-in-production-12345
DATABASE_URL=sqlite:///./db.sqlite3
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

### Step 1.3: Start Backend
```bash
python -m uvicorn api.production:app --host 0.0.0.0 --port 8000 --reload
```

✅ You should see:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete [on 0.0.0.0:8000]
```

### Step 1.4: Verify Backend
Open browser: http://localhost:8000/docs
- See Swagger API documentation
- Click "Try it out" on any endpoint

---

## Phase 2: Frontend Setup

### Step 2.1: Install Dependencies
```bash
cd c:\Users\Venkatachala\ V\STCOK\frontend
npm install
```

### Step 2.2: Start Frontend
```bash
npm run dev
```

✅ You should see:
```
VITE v5.4.21  ready in XXX ms

➜  Local:   http://localhost:8080/
```

### Step 2.3: Dashboard Loads
Open: http://localhost:8080/
- Should see StockPulse dashboard
- 8 stock signals displayed
- Real-time data visible

---

## Phase 3: Authentication Testing

### Test 3.1: Signup
1. Click "Sign Up" (if available) or navigate to auth page
2. Enter email: `test@example.com`
3. Enter password: `testpass123`
4. Click "Create Account"

✅ Expected: 
- Token saved in localStorage
- Redirect to Dashboard
- User profile shows in top-right

### Test 3.2: Login
1. Logout (clear localStorage via console)
2. Click "Log In"
3. Email: `test@example.com`
4. Password: `testpass123`
5. Click "Login"

✅ Expected:
- Same token returned
- Dashboard accessible
- Portfolio shows user data

### Test 3.3: Token Persistence
1. Refresh page (Ctrl+R)
2. Should remain logged in
3. Check localStorage: `auth_token` should exist

---

## Phase 4: Wallet & Trading Testing

### Test 4.1: View Wallet
1. Click "Portfolio" (sidebar)
2. See wallet balance (starts at ₹100,000)
3. See Holdings table

✅ Expected:
- Wallet section visible
- Balance: ₹100,000.00
- Available: ₹100,000.00

### Test 4.2: Add Funds (Demo)
1. Click "Add Funds" button
2. Enter amount: `10000`
3. Click "Add"

✅ Expected:
- Balance increases by ₹10,000
- "Funds added successfully" message
- Available balance updates

### Test 4.3: Buy Stock
1. Go to Dashboard
2. Find RELIANCE (BUY signal)
3. Click "Buy" or similar button
4. Enter quantity: `10`
5. Click "Confirm"

✅ Expected:
- "Order placed successfully"
- Wallet balance decreases
- RELIANCE appears in Portfolio → Holdings
- Transaction logged

### Test 4.4: Sell Stock
1. Go to Portfolio
2. Find "RELIANCE" in Holdings
3. Click "Sell" button
4. Enter quantity: `5`
5. Click "Confirm"

✅ Expected:
- "Order executed successfully"
- Wallet balance increases
- RELIANCE quantity reduced by 5
- Transaction logged

---

## Phase 5: Payment Integration Testing

### Test 5.1: Razorpay Setup (Production Only)
1. Get keys from: https://dashboard.razorpay.com/
2. Add to `.env`:
   ```
   RAZORPAY_KEY_ID=your_key_id
   RAZORPAY_KEY_SECRET=your_key_secret
   ```
3. Restart backend

### Test 5.2: Payment Flow (Demo)
1. Click "Add Money" (if available)
2. See payment modal
3. Enter amount: `5000`
4. Click "Pay Now"

✅ Expected (Demo):
- Razorpay checkout opens
- Use test card: `4111 1111 1111 1111`
- Verification succeeds
- Balance updates

---

## Phase 6: Market Data & Search Testing

### Test 6.1: View Stock Signals
1. Dashboard shows:
   - "Buy Signals: 5"
   - "Sell Signals: 3"
   - "Total Tracked: 8"

✅ Expected: All numbers correct

### Test 6.2: Search Stocks
1. Use search input on Dashboard
2. Type "RELIANCE"
3. Should filter results

✅ Expected: RELIANCE stock highlighted or shown

### Test 6.3: AI Prompt
1. Type query: "Show me buy signals"
2. Press Enter or click search

✅ Expected: 
- 5 BUY signals displayed
- Query processed correctly

### Test 6.4: Signal Details
1. Click on any stock (e.g., RELIANCE)
2. See:
   - Current signal (BUY/SELL)
   - Confidence %
   - Reason for signal

✅ Expected: All details displayed

---

## Phase 7: Complete Flow Testing

### Full Scenario: New User Trades
```
1. Signup with new email
2. View portfolio (starts with ₹100k)
3. Add ₹25k funds
4. Buy 20 shares of RELIANCE
5. Sell 10 shares of RELIANCE
6. Verify portfolio P&L
7. View transaction history
8. Logout and login again
9. Data persists ✅
```

---

## Troubleshooting Guide

### Backend won't start
```bash
# Error: "Address already in use"
# Solution: Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID [PID] /F

# Error: "ModuleNotFoundError"
# Solution: Install missing dependency
pip install -r requirements.txt
```

### Frontend can't connect to backend
```bash
# Check backend is running on 8000:
curl http://localhost:8000/health

# Check CORS in browser console:
# Should see successful data loads

# Fix: Ensure both running and ports correct
Backend: http://localhost:8000
Frontend: http://localhost:8080
```

### Authentication fails
```bash
# Clear browser storage:
// In browser console:
localStorage.clear()
sessionStorage.clear()
// Then refresh page

# Check token in localStorage:
// In console:
console.log(localStorage.getItem('auth_token'))
```

### Trading shows "Insufficient balance"
```
# Add funds first using "Add Funds" button
# Default balance: ₹100,000
# Add ₹10,000+ before trading
```

### Database errors
```bash
# Delete and reinitialize:
del db.sqlite3
# Restart backend - will auto-create

# View database:
sqlite3 db.sqlite3
sqlite> SELECT * FROM users;
sqlite> SELECT * FROM transactions;
```

---

## API Testing with CURL

### Test Signup
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123","name":"Test User"}'
```

### Test Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

### Test Get Signals
```bash
curl http://localhost:8000/api/signals/active
```

### Test Buy Stock
```bash
curl -X POST http://localhost:8000/trading/buy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"RELIANCE","quantity":10,"price":2850}'
```

---

## Production Deployment Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Add Razorpay credentials
- [ ] Update CORS_ORIGINS (remove *)
- [ ] Switch to PostgreSQL database
- [ ] Enable HTTPS
- [ ] Set up monitoring (Sentry, etc)
- [ ] Backup database regularly
- [ ] Rate limit APIs
- [ ] Implement refresh tokens
- [ ] Add logging
- [ ] Deploy frontend to CDN (Vercel/Netlify)
- [ ] Deploy backend to server (Heroku/AWS/DO)

---

## Running in Production

### Backend
```bash
# With gunicorn + nginx (Linux/Mac)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.production:app

# Windows: Use waitress
pip install waitress
waitress-serve --port=8000 api.production:app
```

### Frontend
```bash
# Build
npm run build

# Serve (use web server like nginx/apache)
# Or deploy to Vercel/Netlify:
vercel deploy
```

---

## Support & Debugging

### Enable Debug Logs
```python
# In api/production.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database
```bash
# View all tables:
sqlite3 db.sqlite3 ".tables"

# View schema:
sqlite3 db.sqlite3 ".schema users"

# Query data:
sqlite3 db.sqlite3 "SELECT * FROM users LIMIT 5;"
```

### Monitor Requests
```
# Frontend: Open DevTools (F12)
# Network tab: Watch all API calls
# Console tab: Check for errors

# Backend: Terminal shows all requests
# Look for 200 OK, 400, 401, 500 status codes
```

---

## Next Steps

1. ✅ Start backend & frontend
2. ✅ Test signup/login
3. ✅ Test wallet & trading
4. ✅ Test payments (if configured)
5. ✅ Test market data
6. 📊 Monitor performance
7. 🚀 Deploy to production

---

**System is ready for testing! 🚀**

If issues occur, check:
1. Both services running
2. Correct ports (8000 backend, 8080 frontend)
3. No errors in console/terminal
4. Database readable/writable
5. .env has correct values

