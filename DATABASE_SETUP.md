# STOCKPULSE - Complete Setup Guide

## System Overview

Your StockPulse trading system is now fully operational with:
- ✅ Local SQLite Database (data/platform.db) - 484 KB
- ✅ FastAPI Backend Server (127.0.0.1:8000)
- ✅ React Frontend (localhost:8080)
- ✅ Authentication System (Login/Signup with JWT tokens)
- ✅ User Database with 13 active accounts

## Database Information

**Location:** `data/platform.db`
**Type:** SQLite3 (Local File)
**Size:** 484 KB
**Status:** ✅ ACTIVE

**Current Users:**
```
13 accounts stored including:
- admin@example.com (Premium, Admin)
- trader@example.com (Free)
- investor@example.com (Pro)
- Plus 10 test accounts
```

## Quick Start

### Option 1: Automatic (Recommended)
Windows users - double-click: `START.bat`

### Option 2: Manual

**Terminal 1 - Backend:**
```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Performance Metrics

| Operation | Time | Status |
|-----------|------|--------|
| Login | 388ms | ✅ Fast |
| Signup | ~400ms | ✅ Fast |
| Backend Auth | 10-40ms | ⚡ Lightning |
| Database Query | <5ms | ⚡ Instant |

## Demo Credentials

```
Email:    admin@example.com
Password: password123
Tier:     Premium (Admin)
```

## Useful Commands

**View all users in database:**
```bash
python db_viewer.py
```

**Clear all users (be careful!):**
```bash
python db_viewer.py clear
```

**Delete specific user:**
```bash
python db_viewer.py delete email@example.com
```

**Check backend health:**
```
curl http://127.0.0.1:8000/health
```

**API Documentation:**
```
http://127.0.0.1:8000/docs
```

## System Architecture

```
┌─────────────────────┐
│  Frontend (React)    │
│  localhost:8080      │
└──────────┬───────────┘
           │
    HTTP/Axios
           │
┌──────────▼───────────┐
│  FastAPI Backend     │
│  127.0.0.1:8000      │
└──────────┬───────────┘
           │
         SQL
           │
┌──────────▼───────────┐
│  SQLite Database     │
│  data/platform.db    │
└─────────────────────┘
```

## Features Implemented

✅ User Authentication
  - Login with email/password
  - Signup with validation
  - JWT-like token generation
  - Session persistence (localStorage)

✅ Protected Routes
  - Dashboard, Discovery, Portfolio, Risk-OS
  - Redirect to login if not authenticated
  - User menu with logout

✅ Password Security
  - SHA256 hashing
  - Unique email validation
  - Tier-based access (free/pro/premium)

✅ Real-time User Display
  - Header shows logged-in user
  - Logout functionality
  - Session management

## Troubleshooting

**Backend Port Already in Use:**
```powershell
Get-Process python | Stop-Process -Force
```

**Frontend Not Starting:**
```bash
cd frontend
npm install
npm run dev
```

**Database Issues:**
```bash
python db_viewer.py  # Check status
python add_demo_users.py  # Reinitialize
```

**Clear Browser Cache:**
- DevTools → Application → Local Storage → Clear All

## Files Reference

| File | Purpose |
|------|---------|
| `api/app.py` | Backend API server |
| `frontend/src/` | React frontend code |
| `data/platform.db` | SQLite database |
| `db_viewer.py` | Database management tool |
| `add_demo_users.py` | User initialization |
| `START.bat` | Windows startup script |

## Next Steps

1. ✅ Authentication Working
2. 🔄 Test Dashboard Features
3. 🔄 Configure Trading Signals
4. 🔄 Set Portfolio Positions
5. 🔄 Deploy to Production

---

**System Status:** 🟢 READY
**Last Update:** 2026-04-15
**Version:** 2.0.0
