# 🚀 STOCKPULSE - COMPLETE INTEGRATION GUIDE

## System Overview

```
Frontend (React 18)          Backend (FastAPI 3.0)         Database (SQLite)
├── Auth Pages              ├── Auth Routes               ├── Users
├── Dashboard               ├── Trading Routes            ├── Wallets  
├── Portfolio               ├── Payment Routes            ├── Holdings
├── Risk Analysis           ├── Portfolio Routes          ├── Transactions
└── Settings                ├── Signal Routes             └── ML Predictions
                            └── Health Check
```

---

## Backend Setup (Production.py)

### ✅ Features Implemented

1. **Authentication**
   - JWT token-based auth
   - Password hashing (PBKDF2)
   - Session management

2. **Portfolio Management**
   - Real wallet balance
   - Holdings tracking
   - Transaction history
   - P&L calculations

3. **Trading**
   - Buy/Sell with balance validation
   - Transaction recording
   - Position tracking

4. **Payments**
   - Razorpay integration
   - Order creation & verification
   - Wallet top-up via payments

5. **Dashboard Data**
   - 8 active stock signals
   - Buy/Sell recommendations
   - Portfolio analytics

6. **AI Features**
   - Stock search
   - Prompt-based queries
   - Signal filtering

---

## Frontend Integration

### 1. Update Auth Context (AuthContext.tsx)

```typescript
// Change /auth/register to /auth/signup
// Change /auth/login endpoint URL
// Keep token storage same
```

### 2. Update API Client (api.ts)

```typescript
// Update endpoints:
- /auth/register → /auth/signup
- /portfolio/add-demo-funds → /wallet/add-funds
- Add setAuthToken() function for axios headers
```

### 3. Wire Trading Buttons

Components to update:
- `Dashboard.tsx` - Add Buy/Sell buttons
- `Portfolio.tsx` - Add trading modal
- `StockDetail.tsx` - Add order form

### 4. Connect Razorpay

- `WalletModal.tsx` - Integrate payment flow
- Call `/payment/create-order`
- Verify with `/payment/verify`

---

## Running the System

### Backend
```bash
cd c:\Users\Venkatachala\ V\STCOK
python -m uvicorn api.production:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm run dev
# Opens at http://localhost:8080
```

### Database
- Auto-initialized on first run
- SQLite at `db.sqlite3`
- Schema: Users → Wallets → Holdings → Transactions

---

## API Endpoints Reference

### Authentication
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login
- `GET /auth/me` - Current user

### Wallet & Payments
- `GET /wallet` - Balance info
- `POST /wallet/add-funds` - Add funds (demo)
- `POST /payment/create-order` - Razorpay order
- `POST /payment/verify` - Verify payment

### Portfolio & Trading
- `GET /portfolio` - User holdings
- `GET /portfolio/transactions` - History
- `POST /trading/buy` - Buy stock
- `POST /trading/sell` - Sell stock

### Market Data
- `GET /api/signals/active` - All signals
- `GET /stocks/top-bulls` - Best buys
- `GET /stocks/top-bears` - Best sells
- `POST /api/search` - Search stocks
- `POST /api/prompt` - AI query

### Health
- `GET /health` - Server status
- `GET /` - Welcome info

---

## Key Integration Points

### 1. Token Management
```typescript
// Save after login/signup
localStorage.setItem('auth_token', token);

// Send with requests
headers: { Authorization: `Bearer ${token}` }
```

### 2. Error Handling
```typescript
// All endpoints return errors as { detail: "message" }
// Frontend should catch and display
```

### 3. Balance Validation
```typescript
// Trading endpoints check wallet balance
// Returns 400 if insufficient funds
```

### 4. Transaction Logging
```typescript
// Every trade logged in database
// Can view history via /portfolio/transactions
```

---

## Testing Checklist

- [ ] Signup creates user & wallet
- [ ] Login returns valid token
- [ ] Portfolio shows wallet balance
- [ ] Buy stock deducts from wallet
- [ ] Sell stock adds to wallet
- [ ] Signals display correctly
- [ ] Search/Prompt work
- [ ] Add funds updates balance
- [ ] Payment flow works (Razorpay)
- [ ] Transaction history shows trades

---

## Data Flow

### Login Flow
```
1. User enters email/password
2. Frontend POST /auth/login
3. Backend verifies & creates JWT
4. Returns token + user data
5. Frontend stores token in localStorage
6. Add token to all future requests
```

### Buy Stock Flow
```
1. User clicks Buy button
2. Opens trading modal
3. Enters quantity & confirms
4. Frontend POST /trading/buy with token
5. Backend checks balance
6. Deducts from wallet
7. Adds holding (or updates existing)
8. Records transaction
9. Returns success + new balance
```

### Payment Flow
```
1. User clicks "Add Funds"
2. Opens payment modal
3. Enters amount
4. Frontend POST /payment/create-order
5. Backend creates Razorpay order
6. Frontend opens checkout
7. User completes payment
8. Frontend POST /payment/verify
9. Backend verifies signature
10. Adds funds to wallet
```

---

## Environment Setup

Create `.env` file in root:
```
SECRET_KEY=your-secret-key-change-in-production-12345
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-key-secret
DATABASE_URL=sqlite:///./db.sqlite3
```

---

## Production Checklist

- [ ] Change SECRET_KEY
- [ ] Configure Razorpay credentials
- [ ] Update CORS origins
- [ ] Set up real database (PostgreSQL)
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Add rate limiting
- [ ] Implement API versioning

---

## Troubleshooting

### Backend won't start
- Check Python version (3.8+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 available

### Frontend auth fails
- Check backend is running on 8000
- Check token is saved in localStorage
- Check Authorization header format: `Bearer {token}`

### Trading shows "Insufficient balance"
- Check wallet balance > trade amount
- Add funds first via payment

### Database errors
- Delete db.sqlite3 and restart
- Check database path is writable

---

## Support

Issues? Check:
1. Backend logs for errors
2. Browser console for frontend errors
3. Network tab for API calls
4. Database integrity

