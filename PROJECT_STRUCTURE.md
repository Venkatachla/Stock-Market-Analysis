PROJECT STRUCTURE - STCOK Trading System
==========================================

root/
│
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                 # Updated with routes
│   │   ├── auth.py                # Authentication module
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── db_utils.py            # Database operations
│   │   ├── routes.py              # All API endpoints
│   │   ├── razorpay_integration.py # Payment gateway
│   │   └── server.py              # Inference server
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_loader.py        # Load trained ML models
│   │   └── predictor.py           # Ensemble predictions
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Environment config
│   │   └── security.py            # Security utilities
│   │
│   ├── models/                    # Trained ML models directory
│   │   ├── xgboost_model.pkl
│   │   ├── lgbm_model.pkl
│   │   ├── rf_model.pkl
│   │   └── lstm_model.pt
│   │
│   ├── .env                       # Environment variables (DO NOT COMMIT)
│   ├── .env.example               # Example config
│   ├── requirements.txt           # Python dependencies
│   └── startup.py                 # Startup script
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TradingModal.tsx      # Buy/Sell modal
│   │   │   ├── WalletModal.tsx       # Wallet recharge
│   │   │   └── ...
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx       # Auth provider
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Signup.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Portfolio.tsx         # Enhanced with trading
│   │   │   └── ...
│   │   ├── services/
│   │   │   └── api.ts               # API client
│   │   └── main.tsx
│   │
│   ├── .env                       # Frontend config (DO NOT COMMIT)
│   ├── .env.example               # Example config
│   ├── package.json
│   └── index.html
│
├── .env                           # Root .env (optional)
├── .gitignore                     # Git ignore rules
├── .gitattributes                 # Git LFS (if using large models)
├── requirements.txt               # Python deps
├── setup.bat / setup.sh           # Setup script
├── TRADING_SYSTEM.md              # Complete documentation
├── README.md
└── .github/
    └── copilot-instructions.md
