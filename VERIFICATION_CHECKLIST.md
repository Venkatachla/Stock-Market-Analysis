# 🔍 POST-DEPLOYMENT VERIFICATION CHECKLIST

**Use this checklist to verify your Render deployment is working correctly.**

---

## ✅ IMMEDIATE CHECKS (Do these right after deployment)

### Backend Service Status
- [ ] Backend service shows "Live" in Render Dashboard
- [ ] No errors in service Logs tab
- [ ] Service has a URL (e.g., `https://stockpulse-api-xxxxx.onrender.com`)

### Frontend Service Status  
- [ ] Frontend service shows "Live" in Render Dashboard
- [ ] No errors in service Logs tab
- [ ] Service has a URL (e.g., `https://stockpulse-frontend-xxxxx.onrender.com`)

### Environment Variables Set
- [ ] Backend has `SECRET_KEY` variable
- [ ] Backend has `FRONTEND_URL` variable
- [ ] Frontend has `VITE_API_URL` variable

---

## 🌐 CONNECTIVITY TESTS

### Test Backend Health Endpoint
```bash
curl https://<backend-url>/health
```
Expected response:
```json
{"status":"ok"}
```
- [ ] Returns 200 status code
- [ ] Returns `{"status":"ok"}` JSON

### Test Backend API Docs
Visit: `https://<backend-url>/docs`
- [ ] Swagger UI loads
- [ ] All endpoints listed (auth, trading, portfolio)
- [ ] No 404 or 500 errors

### Test Frontend Loading
Visit: `https://<frontend-url>`
- [ ] Page loads (not blank)
- [ ] No JavaScript errors in console
- [ ] Navigation menu visible
- [ ] Can click "Sign Up" button

---

## 🔐 AUTHENTICATION TESTS

### Test User Registration
1. Go to frontend URL
2. Click "Sign Up"
3. Enter email and password
4. Click "Sign Up"
- [ ] Redirect to login page
- [ ] No "email already exists" error
- [ ] User created in database

### Test User Login
1. Go to frontend URL
2. Click "Log In"
3. Enter email and password
4. Click "Log In"
- [ ] Redirect to dashboard
- [ ] JWT token stored in localStorage
- [ ] User email displayed

### Test Logout
1. From dashboard, click "Logout"
2. Should redirect to home page
- [ ] Token removed from localStorage
- [ ] Can access login page again

---

## 💰 WALLET & TRADING TESTS

### Test View Wallet
1. After login, check wallet balance display
- [ ] Wallet section visible
- [ ] Balance shows ₹0.00 initially
- [ ] No errors accessing wallet endpoint

### Test Add Funds
1. Click "Add Funds" button
2. Choose amount (e.g., ₹10,000)
3. Click "Add Demo Funds"
- [ ] Balance updates immediately
- [ ] Shows ₹10,000.00
- [ ] Persists after page refresh

### Test Buy Stock
1. Select a stock (e.g., RELIANCE)
2. Enter quantity (e.g., 1)
3. Click "Buy"
- [ ] Trade confirmed with price
- [ ] Portfolio updates with holding
- [ ] Wallet balance decreases
- [ ] Transaction saved in history

### Test Portfolio View
1. Check portfolio page
- [ ] Shows purchased stocks
- [ ] Displays quantity and avg price
- [ ] Shows current price (live)
- [ ] P&L calculated correctly
- [ ] Total value correct

### Test Sell Stock
1. From portfolio, find purchased stock
2. Click "Sell"
3. Enter quantity
4. Click "Sell"
- [ ] Stock sold at current price
- [ ] Wallet balance increases
- [ ] Holding removed from portfolio
- [ ] Transaction recorded

---

## 📊 DATA PERSISTENCE TESTS

### Test Data Survives Service Restart
1. Add funds: ₹10,000
2. Buy 1 RELIANCE share
3. Check portfolio (note balance)
4. Restart backend service in Render Dashboard
5. Wait for service to restart
6. Refresh frontend page
- [ ] Still logged in
- [ ] Wallet balance unchanged
- [ ] RELIANCE holding still there
- [ ] Transactions preserved

### Test Multi-user Support
1. Use browser A to login as user1@example.com
2. Use browser B (incognito) to login as user2@example.com
3. User1: Add ₹10,000 funds
4. User2: Add ₹5,000 funds
5. Switch between browsers
- [ ] Each user sees their own balance
- [ ] User1 has ₹10,000
- [ ] User2 has ₹5,000
- [ ] No data mixing

---

## ⚡ PERFORMANCE TESTS

### Test API Response Times
```bash
time curl https://<backend-url>/health
```
- [ ] Response < 1000ms

### Test Trading Endpoint Speed
```bash
time curl -X POST https://<backend-url>/api/trading/buy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"symbol":"RELIANCE","quantity":1}'
```
- [ ] Response < 2000ms

### Test Frontend Performance
Visit frontend URL and open DevTools (F12):
1. Go to Network tab
2. Reload page
3. Check total load time
- [ ] Page loads < 5 seconds
- [ ] No failed resources (404s)
- [ ] CSS and JS load properly

---

## 🐛 ERROR HANDLING TESTS

### Test Invalid Login
1. Try login with wrong password
- [ ] Shows error message
- [ ] Does not create session

### Test Insufficient Funds
1. Add ₹1,000 funds
2. Try to buy stock worth ₹2,000
- [ ] Shows "Insufficient balance" error
- [ ] Wallet not charged

### Test Invalid Stock Symbol
1. Try to search invalid stock (e.g., "XXXXX")
- [ ] No infinite loading
- [ ] Shows error or empty results

### Test Network Errors
1. Unplug internet (or use offline mode)
2. Try to perform any action
- [ ] Shows network error message
- [ ] Graceful degradation

---

## 🔒 SECURITY TESTS

### Test JWT Token Validation
1. Copy JWT token from localStorage
2. Modify one character
3. Try to use modified token
- [ ] API returns 401 Unauthorized
- [ ] Cannot access protected endpoints

### Test CORS Protection
Try API from different domain:
```bash
curl -H "Origin: https://example.com" https://<backend-url>/health
```
- [ ] Should be allowed (CORS configured)
- [ ] No CORS errors

### Test Password Hashing
1. Check database file (if accessible)
- [ ] Passwords are hashed (not plain text)
- [ ] Uses bcrypt hashing

---

## 📱 MOBILE RESPONSIVENESS

### Test on Mobile (or use browser dev tools)
1. Set viewport to 375x667 (iPhone)
2. Load frontend
- [ ] Layout adjusts properly
- [ ] Buttons are clickable
- [ ] No horizontal scroll
- [ ] Forms are usable

### Test on Tablet (768x1024)
- [ ] Layout still works
- [ ] Charts readable (if present)
- [ ] Buttons easy to tap

---

## 📧 OPTIONAL: EMAIL & NOTIFICATIONS

If email integration exists:
- [ ] Check email on signup confirmation
- [ ] Verify email contains correct details
- [ ] Links in email are clickable

---

## 📊 FINAL VERIFICATION RESULTS

Use this template to document results:

```
BACKEND DEPLOYMENT
✓ Service Status: Live / URL: https://stockpulse-api-xxxxx.onrender.com
✓ Health Check: Passing
✓ API Docs: Accessible at /docs
✓ Uptime: [X]%

FRONTEND DEPLOYMENT
✓ Service Status: Live / URL: https://stockpulse-frontend-xxxxx.onrender.com  
✓ Page Loading: Success
✓ Assets Loading: Complete
✓ Performance: < 5 seconds

AUTHENTICATION
✓ Registration: Working
✓ Login: Working
✓ Logout: Working
✓ Token Management: Working

TRADING FUNCTIONALITY
✓ Add Funds: Working
✓ Buy Stock: Working
✓ View Portfolio: Working
✓ Sell Stock: Working
✓ Transaction History: Working

DATA PERSISTENCE
✓ Wallet Balance: Persists
✓ Holdings: Persist
✓ Transactions: Recorded
✓ User Data: Isolated

PRODUCTION READINESS
✓ All Tests Passed: YES/NO
✓ No Critical Errors: YES/NO
✓ Performance Acceptable: YES/NO
✓ Ready for Users: YES/NO
```

---

## 🎯 SIGN-OFF CHECKLIST

- [ ] All connectivity tests passed
- [ ] All authentication tests passed
- [ ] All trading tests passed
- [ ] All persistence tests passed
- [ ] Performance acceptable
- [ ] Security tests passed
- [ ] Mobile responsive
- [ ] Ready for production

---

## ❌ IF TESTS FAIL

1. **Check Render Logs:**
   - Service → Logs tab
   - Look for error messages
   - Check build output for issues

2. **Check Environment Variables:**
   - Service → Environment tab
   - Verify all required variables are set
   - No typos or missing values

3. **Test Locally First:**
   - Run `python test_endpoints.py`
   - Run `python test_trading_flow.py`
   - Verify everything works locally before Render

4. **Common Issues:**
   - Missing `SECRET_KEY` → Add to environment
   - Wrong API URL → Update VITE_API_URL
   - Database locked → Check SQLite permissions
   - CORS errors → Check `FRONTEND_URL` setting

---

**Deployment Date:** April 29, 2026  
**Status:** Ready for Verification ✅
