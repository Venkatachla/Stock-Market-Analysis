# 📚 QUICK REFERENCE - Stock Trading System

**Status:** ✅ Complete & Production-Ready  
**Version:** 1.0.0  
**Last Updated:** April 15, 2026

---

## 🚀 QUICK START (2 MINUTES)

### Windows
```batch
START.bat
```

### Linux/Mac
```bash
bash START.sh
```

**Then open:** http://localhost:5173

---

## 📋 WHAT'S INCLUDED

| Component | Status | Location |
|-----------|--------|----------|
| Backend (FastAPI) | ✅ Complete | `/api/` |
| Frontend (React) | ✅ Complete | `/frontend/` |
| ML Ensemble | ✅ Complete | `/models/` |
| Authentication | ✅ JWT + bcrypt | `api/auth.py` |
| Database | ✅ SQLite/PostgreSQL | `api/models.py` |
| Trading APIs | ✅ 12+ endpoints | `api/routes.py` |
| Razorpay | ✅ Integrated | `api/razorpay_integration.py` |
| Configuration | ✅ Environment vars | `api/core/config.py` |
| Documentation | ✅ 5 guides | `/` |

---

## 🎯 FIRST TIME SETUP

### Option 1: Automated (Recommended)

**Windows:**
```batch
START.bat
```

**Linux/Mac:**
```bash
bash START.sh
```

### Option 2: Manual Setup

#### Backend Setup
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate (Windows)
venv\Scripts\activate

# 3. Activate (Linux/Mac)
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
copy .env.example .env

# 6. Edit .env (set Razorpay keys if needed)

# 7. Initialize database
python -c "from api.models import Base, engine; Base.metadata.create_all(engine)"

# 8. Start backend
python -m uvicorn api.app:app --reload
```

#### Frontend Setup (New Terminal)
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev
```

---

## 🌐 ACCESS URLS

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Web dashboard |
| Backend API | http://localhost:8000 | API server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API Redoc | http://localhost:8000/redoc | OpenAPI docs |

---

## 🔐 TEST CREDENTIALS

**First Login:** User must signup  
**Demo Funds:** Available via "Add Money" button

**Example:**
```
Email: test@example.com
Password: SecurePass123
```

---

## 📚 DOCUMENTATION MAP

| Document | Purpose | Time |
|----------|---------|------|
| [README.md](README.md) | Project overview | 5 min |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | This guide | 2 min |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Detailed setup + troubleshooting | 30 min |
| [TRADING_SYSTEM.md](TRADING_SYSTEM.md) | Complete API documentation | 20 min |
| [CLEANUP_ANALYSIS.md](CLEANUP_ANALYSIS.md) | Code cleanup strategy | 10 min |
| [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) | Full system summary | 15 min |

---

## 🛠️ COMMON TASKS

### Create New User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "securepass123"
}

Response:
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

### Buy Stock
```http
POST /trading/buy
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "symbol": "AAPL",
  "quantity": 10,
  "price": 150.25
}
```

### Sell Stock
```http
POST /trading/sell
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "symbol": "AAPL",
  "quantity": 5,
  "price": 152.50
}
```

### Get Portfolio
```http
GET /portfolio
Authorization: Bearer <TOKEN>
```

### Create Payment Order
```http
POST /payment/create-order
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "amount": 5000
}
```

**For complete API reference:** See [TRADING_SYSTEM.md](TRADING_SYSTEM.md)

---

## 🐛 QUICK TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| **ModuleNotFoundError** | `pip install -r requirements.txt` |
| **Port 8000 in use** | Kill process: `taskkill /F /IM python.exe` (Windows) or `pkill -f uvicorn` (Linux) |
| **Port 5173 in use** | Kill process: `taskkill /F /IM node.exe` (Windows) or `pkill -f "npm run dev"` (Linux) |
| **.env not found** | `copy .env.example .env` (Windows) or `cp .env.example .env` (Linux) |
| **Database error** | `python -c "from api.models import Base, engine; Base.metadata.create_all(engine)"` |
| **ML models missing** | Place `.pkl` files in `models/` directory |
| **npm ERR!** | Delete `frontend/node_modules` and run `npm install` again |
| **CORS error** | Check CORS middleware in `api/app.py` |

**For detailed troubleshooting:** See [SETUP_GUIDE.md](SETUP_GUIDE.md#debugging)

---

## 🏗️ PROJECT STRUCTURE

```
STCOK/
├── api/                              # Backend package
│   ├── app.py                       # FastAPI main app
│   ├── auth.py                      # Authentication (JWT, bcrypt)
│   ├── models.py                    # Database models
│   ├── routes.py                    # Trading APIs (12+ endpoints)
│   ├── razorpay_integration.py      # Payment gateway
│   ├── db_utils.py                  # Database operations
│   ├── core/
│   │   ├── config.py                # Environment configuration
│   │   └── security.py              # Security utilities
│   ├── services/
│   │   ├── model_loader.py          # ML model loader
│   │   └── predictor.py             # Ensemble predictor
│   └── __init__.py
│
├── frontend/                         # React app
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Signup.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── Portfolio.tsx
│   │   ├── components/
│   │   │   ├── TradingModal.tsx
│   │   │   └── WalletModal.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── models/                           # ML models
│   ├── xgboost_model.pkl
│   ├── lgbm_model.pkl
│   ├── rf_model.pkl
│   └── lstm_model.pt
│
├── db.sqlite3                        # Database
├── .env.example                      # Environment template
├── requirements.txt                  # Python dependencies
├── START.bat                         # Windows startup
├── START.sh                          # Linux/Mac startup
│
└── [Documentation]
    ├── README.md
    ├── SETUP_GUIDE.md
    ├── TRADING_SYSTEM.md
    ├── CLEANUP_ANALYSIS.md
    └── COMPLETION_SUMMARY.md
```

---

## 📊 ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                  React Frontend (5173)                  │
│  (Login, Signup, Dashboard, Portfolio, Modals)          │
└────────────────┬────────────────────────────────────────┘
                 │ HTTPS/REST API
                 │
┌────────────────▼────────────────────────────────────────┐
│              FastAPI Backend (8000)                     │
│  ├─ Authentication (JWT + bcrypt)                      │
│  ├─ Trading APIs (Buy/Sell/Portfolio)                  │
│  ├─ Razorpay Integration                               │
│  └─ ML Ensemble Predictions                            │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐ ┌─────────┐ ┌─────────────┐
│SQLite/ │ │YFinance │ │ML Ensemble  │
│Postgres│ │(Stocks) │ │(Prediction) │
└────────┘ └─────────┘ └─────────────┘
```

---

## 🔒 SECURITY

| Feature | Implementation |
|---------|-----------------|
| Password | bcrypt (12 rounds) |
| Auth | JWT HS256, 24h expiry |
| Database | Foreign keys, cascade delete |
| Input | Pydantic validation |
| CORS | Configurable middleware |
| Secrets | Environment variables (.env) |
| Config | Production checks (SECRET_KEY, DEBUG) |

---

## 🤖 ML SYSTEM

**Ensemble:** 4-model weighted voting

| Model | Type | Weight |
|-------|------|--------|
| XGBoost | Tree | 40% |
| LightGBM | Tree | 30% |
| RF | Tree | 20% |
| LSTM | DL | 10% |

**Output:**
- **BUY**: confidence ≥ 65%
- **SELL**: confidence ≤ 35%
- **NEUTRAL**: 35% - 65%

---

## 📦 DEPENDENCIES

### Backend
```
FastAPI 0.104+
SQLAlchemy 2.0+
Pydantic 2.0+
passlib[bcrypt]
python-jose
razorpay
xgboost
lightgbm
torch
```

### Frontend
```
React 18+
TypeScript
Vite
Axios
Tailwind CSS
Lucide Icons
```

---

## 🚀 DEPLOYMENT

### Production Setup
```bash
# 1. Set environment
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=<strong-256-char-key>

# 2. Initialize DB
python -c "from api.models import Base, engine; Base.metadata.create_all(engine)"

# 3. Build frontend
cd frontend && npm run build

# 4. Start with production server
gunicorn api.app:app --workers 4 --bind 0.0.0.0:8000

# 5. Serve frontend from dist/
# Use nginx or similar web server
```

**For more details:** See [SETUP_GUIDE.md](SETUP_GUIDE.md#deployment)

---

## ✅ VERIFICATION CHECKLIST

After setup, verify:

- [ ] POST /auth/register works
- [ ] POST /auth/login works
- [ ] GET /portfolio returns holdings
- [ ] POST /trading/buy executes
- [ ] ML predictions load
- [ ] Frontend dashboard displays data
- [ ] Razorpay modal opens
- [ ] Cleanup script runs without errors

**Run verification script:**
```bash
python verify_cleanup.py
```

---

## 🆘 NEED HELP?

1. **Setup issues?** → [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. **API questions?** → [TRADING_SYSTEM.md](TRADING_SYSTEM.md)
3. **Project structure?** → [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
4. **Cleanup help?** → [CLEANUP_ANALYSIS.md](CLEANUP_ANALYSIS.md)
5. **Full overview?** → [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)

---

## 🎓 LEARNING PATHS

**Beginner:**  
README.md → QUICK_REFERENCE.md → SETUP_GUIDE.md

**Developer:**  
SETUP_GUIDE.md → TRADING_SYSTEM.md → API Docs

**DevOps:**  
PROJECT_STRUCTURE.md → CLEANUP_ANALYSIS.md → Deployment section

**ML Engineer:**  
`api/services/model_loader.py` → `api/services/predictor.py` → `/models/`

---

## 📊 QUICK STATS

| Metric | Value |
|--------|-------|
| Backend Endpoints | 12+ |
| Frontend Components | 20+ |
| Database Tables | 4 |
| ML Models | 4 (ensemble) |
| API Response Time | <500ms |
| Prediction Accuracy | Depends on training |
| Total Code | ~3500 lines |

---

## 🔄 COMMON WORKFLOWS

### Workflow 1: User Trading
```
1. Create account (Signup)
2. Add funds (Razorpay or demo)
3. View predictions (ML ensemble)
4. Buy stock (POST /trading/buy)
5. View portfolio (GET /portfolio)
```

### Workflow 2: Adding ML Model
```
1. Train new model
2. Save to models/ directory
3. Restart backend
4. Model auto-loads
5. Adjust weights in predictor.py if needed
```

### Workflow 3: Production Deploy
```
1. Run verification script
2. Set ENVIRONMENT=production in .env
3. Build frontend: npm run build
4. Start backend with gunicorn
5. Serve frontend/dist/ with nginx
```

---

## 🎉 SUCCESS INDICATORS

You'll know everything works when:

✅ Frontend loads at http://localhost:5173  
✅ API Docs accessible at http://localhost:8000/docs  
✅ Can signup and login  
✅ Portfolio shows holdings  
✅ Buy/Sell buttons work  
✅ Razorpay modal opens  
✅ No console errors  

---

## 💡 TIPS

- Use `http://localhost:8000/docs` to test APIs interactively
- Add demo funds to wallet before trading
- ML predictions auto-load on startup
- Check `.env` for all configurations
- Database auto-creates on first run
- Frontend uses Vite for fast dev reload

---

**Happy Trading! 🚀**

For detailed setup: See [SETUP_GUIDE.md](SETUP_GUIDE.md)  
For API reference: See [TRADING_SYSTEM.md](TRADING_SYSTEM.md)  
For project overview: See [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)
