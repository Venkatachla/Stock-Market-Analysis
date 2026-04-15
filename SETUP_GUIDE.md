# 🚀 COMPLETE SETUP & RUN GUIDE

**Date:** April 15, 2026  
**System:** STCOK Trading System (FastAPI + React + ML)

---

## TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Database Initialization](#database-initialization)
5. [Environment Configuration](#environment-configuration)
6. [Running the System](#running-the-system)
7. [Verification Steps](#verification-steps)
8. [Debugging Guide](#debugging-guide)
9. [Security Check](#security-check)

---

## PREREQUISITES

### System Requirements

- **Python:** 3.8 or higher
- **Node.js:** 16 or higher  
- **npm:** 8 or higher
- **SQLite:** Usually pre-installed
- **RAM:** 2GB minimum (4GB recommended for ML models)
- **Disk:** 2GB free space

### Verify Installations

```bash
# Check Python
python --version

# Check Node.js
node --version
npm --version
```

---

## BACKEND SETUP

### Step 1: Create Virtual Environment

**Windows:**
```bash
cd c:\Users\Venkatachala V\STCOK
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
cd /path/to/STCOK
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed pandas numpy yfinance scikit-learn ...
```

### Step 4: Verify Installation

```bash
python -c "import fastapi; import sqlalchemy; import pydantic; print('✅ All dependencies installed')"
```

### Step 5: Create .env File

**Option A: Automatic (using example)**
```bash
cp .env.example .env
```

**Option B: Manual**
Create `backend/.env` with:

```env
# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=sqlite:///./db.sqlite3

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-this-in-production-12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Razorpay (Optional)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# ML Models
MODEL_DIR=models
MODEL_TYPE=ensemble

# Environment
PYTHON_ENV=development
DEBUG=true
```

### Step 6: Initialize Database

```bash
python -c "
from api.models import Base, engine
print('Creating database tables...')
Base.metadata.create_all(bind=engine)
print('✅ Database initialized at db.sqlite3')
"
```

---

## FRONTEND SETUP

### Step 1: Navigate to Frontend

```bash
cd frontend
```

### Step 2: Install Node Modules

```bash
npm install
```

**Expected output:**
```
added 500+ packages in X seconds
```

### Step 3: Create .env File

**Copy example:**
```bash
cp .env.example .env
```

Or manually create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_RAZORPAY_KEY_ID=
```

### Step 4: Verify Build

```bash
npm run build
```

Should complete without errors.

---

## DATABASE INITIALIZATION (ALTERNATIVE)

If automated database creation fails, use this:

**SQLite Shell Method:**
```bash
sqlite3 db.sqlite3 < schema.sql
```

**Python Method:**
```bash
python
>>> from api.models import Base, engine
>>> Base.metadata.create_all(bind=engine)
>>> exit()
```

---

## ENVIRONMENT CONFIGURATION

### Backend Configuration (config.py)

The `api/core/config.py` file loads settings from `.env`:

```python
from api.core.config import settings

# Access settings
print(settings.api_host)      # "0.0.0.0"
print(settings.api_port)      # 8000
print(settings.database_url)  # "sqlite:///./db.sqlite3"
```

### ML Models Configuration

```env
MODEL_DIR=models              # Path to trained models
MODEL_TYPE=ensemble           # ensemble, xgb, lgbm, rf, lstm
ENABLE_ML_PREDICTIONS=true    # Enable/disable predictions
```

Models loader will automatically:
- Scan `MODEL_DIR`
- Load `.pkl`, `.joblib`, `.pt` files
- Initialize feature scaler if available
- Fall back to dummy predictions if no models found

---

## RUNNING THE SYSTEM

### OPTION 1: SEPARATE TERMINALS (RECOMMENDED)

#### Terminal 1: Backend

```bash
cd c:\Users\Venkatachala V\STCOK

# Activate virtualenv (Windows)
venv\Scripts\activate
# OR (Linux/Mac)
source venv/bin/activate

# Run backend
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Terminal 2: Frontend

```bash
cd c:\Users\Venkatachala V\STCOK\frontend

# Run frontend
npm run dev
```

**Expected output:**
```
VITE v4.x.x  ready in XX ms

➜  Local:   http://localhost:5173/
```

(Note: Port might be 5173 or 8080, check terminal output)

### OPTION 2: SINGLE TERMINAL (Sequential)

```bash
# Start backend in background
cd c:\Users\Venkatachala V\STCOK
venv\Scripts\activate
start cmd /k "python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload"

# Wait 3-5 seconds for backend to start, then start frontend
cd frontend
npm run dev
```

---

## VERIFICATION STEPS

### 1. Backend Health Check

Open in browser or curl:

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status": "healthy"}
```

Or visit: http://localhost:8000/docs (Swagger UI)

### 2. API Endpoints Check

```bash
# List all stocks
curl http://localhost:8000/stocks?limit=5

# Test authentication
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'
```

### 3. Frontend Check

Open in browser:
```
http://localhost:5173
or
http://localhost:8080
```

Should see:
- ✅ Login page loads
- ✅ Dashboard accessible (after login)
- ✅ No console errors

### 4. Database Check

```bash
# Check if db.sqlite3 exists
ls -la db.sqlite3  # Linux/Mac
dir db.sqlite3     # Windows

# Check tables (SQLite)
sqlite3 db.sqlite3 ".tables"
```

Expected tables:
- users
- wallets
- holdings
- transactions

### 5. ML Models Check

```bash
# Check if models are loaded
python -c "
from api.services.model_loader import get_model_loader
from pathlib import Path
loader = get_model_loader(Path('models'), 'ensemble')
print('Available models:', loader.get_available_models())
"
```

---

## DEBUGGING GUIDE

### ISSUE 1: Port 8000 Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000           # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>           # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Or use different port
python -m uvicorn api.app:app --port 8001
```

---

### ISSUE 2: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
1. Verify venv is activated
2. Re-install requirements:
```bash
pip install -r requirements.txt --force-reinstall
```

---

### ISSUE 3: Database Error

**Error:**
```
sqlite3.OperationalError: unable to open database file
```

**Solution:**
```bash
# Ensure data directory exists
mkdir data
touch data/platform.db

# Re-initialize
python -c "from api.models import Base, engine; Base.metadata.create_all(bind=engine)"
```

---

### ISSUE 4: CORS Errors

**Error:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
Backend CORS is already configured in `api/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, use:
```python
allow_origins=[
    "http://localhost:8080",
    "https://yourdomain.com"
]
```

---

### ISSUE 5: .env Not Loading

**Error:**
```
No module named 'python_dotenv'
```

**Solution:**
```bash
pip install python-dotenv
```

Or ensure `.env` file exists and is readable:
```bash
ls -la .env  # Check permissions
```

---

### ISSUE 6: ML Models Not Loading

**Error:**
```
⚠️  No models loaded successfully
```

**Solution:**
1. Check `MODEL_DIR` path exists
2. Verify model files are present
3. Check permissions

```bash
# Check models directory
ls -la models/

# Expected files:
# - xgboost_model.pkl
# - lgbm_model.pkl
# - rf_model.pkl
# - lstm_model.pt
```

If models missing:
- Download / train models
- Place in `backend/models/`
- Restart backend

---

### ISSUE 7: npm install Fails

**Error:**
```
npm ERR! code EACCES
npm ERR! errno -13
```

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

---

### ISSUE 8: Razorpay Key Error

**Error:**
```
Razorpay not available
```

**Solution:**
- Razorpay is optional
- For demo: Use "Add Demo Funds" instead
- For production:
  - Get keys from https://dashboard.razorpay.com
  - Add to `.env`:
    ```
    RAZORPAY_KEY_ID=rzp_live_XXXXX
    RAZORPAY_KEY_SECRET=XXXXX
    ```

---

## SECURITY CHECK

### Before Production Deployment

```bash
# 1. Change SECRET_KEY
# In .env:
SECRET_KEY=<generate-32-char-random-key>

# 2. Change DEBUG to false
DEBUG=false

# 3. Use PostgreSQL instead of SQLite
DATABASE_URL=postgresql://user:password@localhost/stcok

# 4. Set environment
PYTHON_ENV=production

# 5. Add Razorpay keys (if using payments)
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...

# 6. Build optimized frontend
cd frontend
npm run build  # Creates dist/ folder
```

### Security Verification

```bash
# Check SECRET_KEY is not default
grep SECRET_KEY .env

# Verify .env is not committed
git status | grep .env

# Check .gitignore has .env
cat .gitignore | grep .env
```

---

## FINAL SYSTEM TEST

### Complete End-to-End Test

**1. Start backend:**
```bash
cd /path/to/STCOK
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn api.app:app --port 8000
```

**2. Start frontend (new terminal):**
```bash
cd /path/to/STCOK/frontend
npm run dev
```

**3. Test in browser:**
- Open http://localhost:5173 (or shown port)
- Signup: test@example.com / password123
- Login
- Add demo funds (₹1000)
- Buy a stock (RELIANCE.NS / TCS.NS)
- View portfolio
- Check transactions

**4. API Test:**
```bash
# Get portfolio
curl -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer YOUR_TOKEN"

# Buy stock
curl -X POST http://localhost:8000/trading/buy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"RELIANCE.NS","quantity":1}'
```

---

## SUCCESS INDICATORS

✅ Backend running on port 8000  
✅ Frontend running on port 5173/8080  
✅ Database file created (db.sqlite3)  
✅ ML models loaded (check logs)  
✅ Login/signup works  
✅ Can add funds and buy stocks  
✅ Swagger docs at http://localhost:8000/docs  

---

## NEXT STEPS

1. **Add ML Models:**
   - Place trained models in `backend/models/`
   - Restart backend

2. **Configure Razorpay:**
   - Add API keys to `.env`
   - Test payment flow

3. **Deploy to Production:**
   - Use PostgreSQL
   - Setup HTTPS
   - Configure domains
   - Use environment-specific .env files

4. **Monitor System:**
   - Check logs regularly
   - Monitor model performance
   - Track user activity

---

**Questions?** Check [TRADING_SYSTEM.md](TRADING_SYSTEM.md) for detailed API documentation.
