# 🔧 ENVIRONMENT VARIABLES - COMPLETE REFERENCE

**All environment variables used in StockPulse for development and production.**

---

## 📋 BACKEND ENVIRONMENT VARIABLES

### Required for All Environments

| Variable | Value | Purpose | Example |
|----------|-------|---------|---------|
| `DATABASE_URL` | SQLite or PostgreSQL connection string | Database connectivity | `sqlite:///./db.sqlite3` or `postgresql://user:pass@host/db` |
| `SECRET_KEY` | 32+ character random string | JWT token signing | `use-a-secure-random-string-here` |
| `ALGORITHM` | Encryption algorithm for JWT | Token algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Number of minutes | JWT expiration | `1440` |

### Production Only (Render)

| Variable | Value | Purpose | Example |
|----------|-------|---------|---------|
| `FRONTEND_URL` | Frontend deployment URL | CORS allowed origin | `https://stockpulse-frontend.onrender.com` |
| `VITE_API_URL` | API deployment URL | Frontend API endpoint | `https://stockpulse-api.onrender.com` |
| `PYTHON_ENV` | Environment type | Runtime environment | `production` |
| `NODE_ENV` | Environment type | Runtime environment | `production` |

### Optional (If using Razorpay)

| Variable | Value | Purpose | Example |
|----------|-------|---------|---------|
| `RAZORPAY_KEY_ID` | Razorpay API key | Payment processing | `rzp_live_1234567890abcd` |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret | Payment processing | `abcd1234567890xyz` |

### Optional (Debugging)

| Variable | Value | Purpose | Example |
|----------|-------|---------|---------|
| `DEBUG` | true/false | Debug mode | `false` (production) |
| `LOG_LEVEL` | Logging level | Log verbosity | `info` or `debug` |

---

## 📋 FRONTEND ENVIRONMENT VARIABLES

### Required for All Environments

| Variable | Value | Purpose | Example |
|----------|-------|---------|---------|
| `VITE_API_URL` | Backend API URL | API endpoint | `http://localhost:8000` (dev) or `https://stockpulse-api.onrender.com` (prod) |

### Optional

| Variable | Value | Purpose | Example |
|----------|-------|---------|---------|
| `VITE_APP_NAME` | Application name | App title | `StockPulse` |
| `VITE_APP_VERSION` | Version string | App version | `2.0.0` |

---

## 🔄 ENVIRONMENT CONFIGURATIONS

### Development (.env)

Used for local development on your machine.

```
# FastAPI Server
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=sqlite:///./db.sqlite3

# JWT Authentication
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Razorpay (Leave empty if not configured)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Frontend
VITE_API_URL=http://localhost:8000

# Environment
NODE_ENV=development
PYTHON_ENV=development
```

**How to use:**
1. Copy `.env` content
2. Create `.env` file in project root
3. Keep it local (don't commit)

---

### Production (.env.production)

Used when deploying to Render.

```
# FastAPI Server
API_HOST=0.0.0.0
API_PORT=10000

# Database
DATABASE_URL=sqlite:///./db.sqlite3

# JWT Authentication
SECRET_KEY=<your-production-secret-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Frontend URL (Update after deploying frontend)
FRONTEND_URL=https://stockpulse-frontend.onrender.com
VITE_API_URL=https://stockpulse-api.onrender.com

# Razorpay (Optional)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Environment
NODE_ENV=production
PYTHON_ENV=production

# Logging
DEBUG=false
LOG_LEVEL=info
```

**How to use:**
1. In Render Dashboard, navigate to each service
2. Go to Environment tab
3. Add variables listed above
4. Keep Production environment variables secure

---

## 🛠️ HOW TO GENERATE SECURE SECRET_KEY

### Option 1: Python (Recommended)

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example output:
```
xB3kL9mP_q2rZ5vF8tY1uW4sJ6hG7nD0
```

### Option 2: OpenSSL

```bash
openssl rand -base64 32
```

### Option 3: Online Generator

Visit [https://randomkeygen.com/](https://randomkeygen.com/) and copy a strong key.

**Important:** Use the same `SECRET_KEY` for all instances of your backend. If you change it, all JWT tokens become invalid.

---

## 🌍 CORS CONFIGURATION

The backend automatically allows:

**Development Mode:**
- `http://localhost:5173` (Vite frontend)
- `http://localhost:3000` (React dev)
- `http://localhost:8080` (Alternative dev)
- `http://localhost:8000` (Backend dev)
- Any URL in `FRONTEND_URL` env variable

**Production Mode:**
- URLs specified in `FRONTEND_URL` env variable
- URLs specified in `ALLOWED_ORIGINS` env variable (comma-separated)

---

## 📝 STEP-BY-STEP: SET UP ENVIRONMENT IN RENDER

### For Backend Service

1. In Render Dashboard, select your backend service
2. Go to **Environment** tab
3. Click **"Add Environment Variable"**
4. Enter each variable:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite:///./db.sqlite3` |
| `SECRET_KEY` | `<generate-a-secure-key>` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
| `FRONTEND_URL` | `https://stockpulse-frontend.onrender.com` |
| `PYTHON_ENV` | `production` |
| `NODE_ENV` | `production` |

5. If using Razorpay:
   - Add `RAZORPAY_KEY_ID`
   - Add `RAZORPAY_KEY_SECRET`

6. Click **"Save Changes"**
7. Service will restart with new variables

### For Frontend Service

1. In Render Dashboard, select your frontend service
2. Go to **Environment** tab
3. Click **"Add Environment Variable"**
4. Add this variable:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://stockpulse-api.onrender.com` |

5. Click **"Save Changes"**
6. Service will rebuild and deploy

---

## ✅ VERIFY ENVIRONMENT VARIABLES

### Verify Backend Variables

After setting in Render, check they're loaded:

```bash
# In Render logs, you should see
INFO:     Uvicorn running on http://0.0.0.0:$PORT
# If not, check Environment tab for missing variables
```

### Verify Frontend Variables

After setting in Render, check by visiting:
```
https://stockpulse-frontend.onrender.com/
# Open browser DevTools → Console
# API calls should show backend URL
```

---

## 🔐 SECURITY BEST PRACTICES

### Do's ✅
- [ ] Use strong, random `SECRET_KEY` (32+ characters)
- [ ] Store secrets in environment variables only
- [ ] Never commit `.env` files
- [ ] Use different `SECRET_KEY` for dev and prod
- [ ] Rotate secrets periodically
- [ ] Use HTTPS only (Render provides free SSL)
- [ ] Restrict CORS to known domains

### Don'ts ❌
- [ ] Never hardcode secrets in code
- [ ] Never share `SECRET_KEY` in messages
- [ ] Never use same secret for dev and prod
- [ ] Never commit `.env` files to Git
- [ ] Never allow CORS `["*"]` in production
- [ ] Never expose secrets in logs

---

## 🆘 TROUBLESHOOTING ENVIRONMENT VARIABLES

### Issue: "KeyError: SECRET_KEY"

**Cause:** Environment variable not set

**Solution:**
1. Go to Render Dashboard → Service → Environment
2. Verify `SECRET_KEY` is listed
3. Click Save Changes to restart service

### Issue: Frontend can't reach API

**Cause:** `VITE_API_URL` not set correctly

**Solution:**
1. Check frontend Environment has `VITE_API_URL`
2. Verify it matches backend URL exactly
3. Rebuild frontend (trigger new deployment)

### Issue: CORS error when accessing API

**Cause:** Frontend URL not in CORS allowed list

**Solution:**
1. Add `FRONTEND_URL` env variable to backend
2. Restart backend service
3. Clear browser cache and try again

---

## 📚 ENVIRONMENT VARIABLE REFERENCE BY FILE

### api/app.py
```python
import os
os.getenv("DATABASE_URL")  # Uses env variable
os.getenv("SECRET_KEY")     # Uses env variable
os.getenv("ALGORITHM")      # Uses env variable
os.getenv("FRONTEND_URL")   # Uses env variable
```

### frontend/.env.production
```bash
VITE_API_URL=https://stockpulse-api.onrender.com
```

### Procfile
```
web: uvicorn api.app:app --host 0.0.0.0 --port $PORT
# Note: $PORT is automatically provided by Render
```

---

**Last Updated:** April 29, 2026  
**Environment:** Production Ready ✅
