# 🧹 PROJECT CLEANUP ANALYSIS

**Date:** April 15, 2026  
**Purpose:** Identify and safely remove unused/redundant files

---

## EXECUTIVE SUMMARY

**Total Files:** ~300+ (including node_modules, __pycache__)  
**Safe to Delete:** ~50-100K files (mostly dependencies)  
**Must Keep:** ~80 files (core system)  
**REVIEW REQUIRED:** ~15 files (deprecated or unclear)

---

## CRITICAL FILES TO KEEP

### ✅ MUST KEEP (Core System)

#### Backend Core
```
api/app.py                    # Main FastAPI application
api/auth.py                   # Authentication module
api/models.py                 # Database ORM models
api/db_utils.py              # Database operations
api/routes.py                # Trading API endpoints
api/razorpay_integration.py  # Payment gateway
api/server.py                # Inference server

api/core/config.py           # Configuration management
api/core/security.py         # Security utilities

api/services/model_loader.py # ML model loading
api/services/predictor.py    # Ensemble predictions

api/__init__.py              # Package initialization
```

#### Frontend Core
```
frontend/src/components/     # React components
  - TradingModal.tsx        # Buy/Sell modal
  - WalletModal.tsx         # Wallet recharge
  - ...existing components

frontend/src/contexts/       # Context providers
  - AuthContext.tsx         # Auth provider

frontend/src/pages/          # Page components
  - Login.tsx               # Login page
  - Signup.tsx              # Signup page
  - Portfolio.tsx           # Portfolio page (enhanced)
  - Dashboard.tsx           # Dashboard
  - ...

frontend/src/services/       # API services
  - api.ts                  # API client

frontend/index.html          # HTML entry point
frontend/package.json        # Dependencies
frontend/vite.config.ts      # Vite config
frontend/tsconfig.json       # TypeScript config
```

#### Configuration Files
```
.env.example                 # Environment template
.gitignore                   # Git ignore rules
requirements.txt             # Python dependencies
frontend/package.json        # Node dependencies

.github/copilot-instructions.md  # Project instructions
```

#### Documentation
```
README.md                    # Project overview
TRADING_SYSTEM.md           # Trading system docs
SETUP_GUIDE.md              # Setup instructions
PROJECT_STRUCTURE.md        # File structure
CLEANUP_ANALYSIS.md         # This file
```

#### Database & ML
```
db.sqlite3 (or data/platform.db)   # Database
models/                            # ML models directory
  - xgboost_model.pkl
  - lgbm_model.pkl
  - rf_model.pkl
  - lstm_model.pt
```

---

## FILES SAFE TO DELETE

### ❌ DELETE: Troubleshooting Scripts (Redundant with new system)

```
❌ debug_app.py              → Replaced by api/app.py
❌ debug_auth.py             → Replaced by api/auth.py
❌ debug_predict.py          → Replaced by api/routes.py
❌ check_users.py            → Use database directly
❌ add_demo_users.py         → Use API /auth/register
❌ add_routes.py             → Routes in api/routes.py
❌ inject_routes.py          → Routes in api/routes.py
❌ patch_app.py              → Not needed with new structure
```

### ❌ DELETE: Old Test Scripts

```
❌ test_missing.py           → Outdated test
❌ test_predict_api.py       → Outdated test
❌ test_prediction_detail.py → Outdated test
❌ integration_test.py       → Old integration test
```

### ❌ DELETE: Temporary/Demo Files

```
❌ A_Cover_in_Water.java     → Unrelated Java file
❌ update_ui.py              → Temp script
❌ cli.py                    → Old CLI tool
❌ SYSTEM_STATUS.txt         → Status file (regenerated)
```

### ❌ DELETE: Backup & Duplicate Folders

```
❌ frontend.backup/          → Old backup folder
❌ stockpulse-project/       → Duplicate frontend copy
❌ frontend/.workspace/      → Nested git repo
```

### ❌ DELETE: Build Artifacts

```
❌ dist/                     → Built frontend (regenerate with: npm run build)
❌ build/                    → Compiled output
❌ __pycache__/              → Python cache (auto-generated)
❌ *.pyc files               → Python bytecode (auto-generated)
❌ node_modules/             → npm packages (regenerate with: npm install)
```

### ❌ DELETE: Cache Folders

```
❌ .cache_yf/                → YFinance cache (auto-generated)
❌ .pytest_cache/            → Pytest cache
❌ logs/                     → Log files (auto-generated)
❌ tmp/                      → Temporary files
❌ tmp_report_format/        → Temp folder
```

### ❌ DELETE: Report/Output Files

```
❌ train_output.log          → Training log (old)
❌ DEPLOYMENT_COMPLETE.md    → Status file (archived)
❌ INTEGRATION_COMPLETE.md   → Status file (archived)
❌ INTEGRATION_SUMMARY.md    → Summary (archived)
❌ LIVE_SYSTEM_STATUS.md     → Status file (archived)
❌ FINAL_STATUS_REPORT.md    → Status file (archived)
```

### ❌ DELETE: CSV/JSON Output (Regeneratable)

```
❌ backtest/*.csv            → Backtest outputs (regenerate)
❌ backtest/*.json           → Backtest reports (regenerate)
❌ data/trending_picks.json  → Trending log (auto-generated)
```

### ❌ DELETE: Old Model Files

```
❌ models/multi_strategy.py  → Move to api/services/
❌ btlogic/                  → Old backtest logic (unused)
❌ backtest/                 → Old backtest engine (unused with new system)
```

---

## FILES TO REVIEW

### ⚠️ REVIEW REQUIRED (Unclear Usage)

```
⚠️ main.py                   → UNCERTAIN
   Decision: Check if used by startup scripts. If not, DELETE.

⚠️ startup.py                → UNCERTAIN
   Decision: If just runs api.app, DELETE. If custom, KEEP.

⚠️ quant_system.py           → POSSIBLY USED
   Decision: Check if imported in api/app.py. If not, DELETE.

⚠️ data/downloader.py        → POSSIBLY USED
   Decision: Check if called by any API endpoint. If not, DELETE.

⚠️ data/ticker_fetcher.py    → POSSIBLY USED
   Decision: Check if called by any API endpoint. If not, DELETE.

⚠️ features/engineer.py      → POSSIBLY USED
   Decision: Check if imported in api/server.py. If yes, KEEP.

⚠️ features/multi_strategy.py → POSSIBLY USED
   Decision: Check if imported anywhere. If not, DELETE.

⚠️ training/lstm_model.py    → POSSIBLY USED
   Decision: Check if needed for model loading. If yes, KEEP in utils/.

⚠️ training/dataset.py       → POSSIBLY USED
   Decision: Check if needed for inference. If not, DELETE.

⚠️ trading/engine.py         → POSSIBLY USED
   Decision: Check if imported in routes.py. If not, DELETE.

⚠️ trading/decision_engine.py → POSSIBLY USED
   Decision: Check if imported in routes.py. If not, DELETE.

⚠️ trading/risk.py           → POSSIBLY USED
   Decision: Check if imported in routes.py. If not, DELETE.

⚠️ docs/.*                   → UNCERTAIN
   Decision: If documentation needed, KEEP. Otherwise, DELETE.

⚠️ docs/blockchain_research_gap_plan.md → UNRELATED
   Decision: Seems unrelated to trading system. DELETE.

⚠️ strategy/                 → UNCERTAIN
   Decision: Check if used by any API. If not, DELETE.
```

---

## DELETE SAFE COMMANDS

### Batch Delete (Windows)

```batch
REM Delete old test scripts
del debug_app.py
del debug_auth.py
del debug_predict.py
del check_users.py
del add_demo_users.py
del add_routes.py
del patch_app.py
del test_*.py
del integration_test.py
del update_ui.py
del cli.py
del main.py
del startup.py
del A_Cover_in_Water.java
del SYSTEM_STATUS.txt

REM Delete backup folders
rmdir /s /q frontend.backup
rmdir /s /q stockpulse-project
rmdir /s /q tmp_report_format

REM Delete build artifacts
rmdir /s /q dist
rmdir /s /q build
rmdir /s /q __pycache__

REM Delete cache
rmdir /s /q .cache_yf
rmdir /s /q .pytest_cache
rmdir /s /q logs
rmdir /s /q tmp
```

### Batch Delete (Linux/Mac)

```bash
# Delete old test scripts
rm -f debug_*.py test_*.py add_*.py check_*.py cli.py main.py
rm -f update_ui.py patch_app.py integration_test.py
rm -f A_Cover_in_Water.java SYSTEM_STATUS.txt

# Delete backup folders
rm -rf frontend.backup stockpulse-project tmp_report_format

# Delete build artifacts
rm -rf dist build __pycache__

# Delete cache
rm -rf .cache_yf .pytest_cache logs tmp
```

### Git Clean (Recommended)

```bash
# Dry run (shows what will be deleted)
git clean -fd --dry-run

# Actually delete
git clean -fd
```

---

## CAUTIOUS DELETE (Review First)

These files import patterns - review dependencies before deleting:

```bash
# Check if quant_system.py is imported
grep -r "import quant_system" backend/

# Check if used by APIs
grep -r "from quant_system" backend/api/

# Check if training modules are imported
grep -r "from training" backend/

# Check if trading modules are imported
grep -r "from trading" backend/api/

# Only delete if no import found
```

---

## RECOMMENDED CLEANUP STRATEGY

### Phase 1: Safe Deletions (No Risk)

```bash
# Delete old troubleshooting scripts
rm debug_app.py debug_auth.py debug_predict.py
rm check_users.py add_demo_users.py
rm A_Cover_in_Water.java SYSTEM_STATUS.txt

# Delete backup folders
rm -rf frontend.backup stockpulse-project tmp_report_format

# Delete build artifacts
rm -rf dist build logs tmp
```

### Phase 2: Build Artifacts (Safe to Regenerate)

```bash
# Delete and regenerate Python cache
rm -rf __pycache__ *.pyc
python -m py_compile api/*.py  # Regenerate

# Delete and regenerate node_modules
rm -rf frontend/node_modules
cd frontend && npm install

# Delete and regenerate build
rm -rf frontend/dist
cd frontend && npm run build
```

### Phase 3: Conditional Deletions (Check Dependencies First)

For each file below, run `grep -r "filename" backend/` first:

```
- main.py
- startup.py
- quant_system.py
- strategy/ folder
- btlogic/ folder
- training/ (except models that might be referenced)
```

Only delete if not imported anywhere.

### Phase 4: Archive Old Reports

```bash
# Archive but don't delete yet
mkdir archive
mv DEPLOYMENT_COMPLETE.md INTEGRATION_*.md FINAL_STATUS.md archive/
```

---

## AFTER CLEANUP

### Verify System Still Works

```bash
# Backend
cd backend
python -m api.app --test  # Should not error

# Frontend
cd frontend
npm run build  # Should complete successfully

# Git
git status
git diff  # Review changes before commit
```

### Commit Changes

```bash
git add -A
git commit -m "chore: cleanup obsolete files and build artifacts"
git push
```

---

## SUMMARY TABLE

| Category | Action | Reason |
|----------|--------|--------|
| Old test scripts | ❌ DELETE | Redundant with new system |
| Build artifacts | ❌ DELETE | Auto-regenerated |
| Cache folders | ❌ DELETE | Auto-generated |
| Backup folders | ❌ DELETE | Duplicates of active code |
| Reports (old) | ⚠️ ARCHIVE | Historical reference |
| API/Core files | ✅ KEEP | Critical functionality |
| Frontend components | ✅ KEEP | Active UI |
| Config files | ✅ KEEP | System configuration |
| ML models | ✅ KEEP | Trained models |
| Documentation | ✅ KEEP | Project reference |

---

## PROJECT SIZE BEFORE/AFTER

**Before cleanup:**
- Total size: ~500MB+ (mostly node_modules + models)
- Build artifacts: ~100MB
- Cache files: ~50MB

**After cleanup:**
- Total size: ~50-100MB (without node_modules)
- Build artifacts: (~100MB generated on demand)
- Cache files: (~50MB generated on demand)

**Savings:** 300-400MB with node_modules/dist in .gitignore

---

## NEXT STEPS

1. Run Phase 1 deletions (safe)
2. Verify system starts without errors
3. Run Phase 2 (build artifacts) - these are auto-generated
4. Carefully review Phase 3 files before deleting
5. Archive Phase 4 files
6. Commit changes
7. Run full test suite

---

**Note:** This analysis is conservative. If unsure, keep the file. Disk space is cheap; fixing broken deployments is expensive.
