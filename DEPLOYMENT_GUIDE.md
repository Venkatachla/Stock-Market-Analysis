# 🚀 STOCKPULSE DEPLOYMENT TO RENDER - COMPLETE GUIDE

**Status:** Ready for Production  
**Target Platform:** Render.com  
**Estimated Deployment Time:** 15 minutes

---

## ✅ PRE-DEPLOYMENT CHECKLIST

Before deploying, verify these items are complete:

### Backend Configuration ✅
- [x] All hardcoded URLs replaced with environment variables
- [x] CORS configured for production domains
- [x] `requirements.txt` complete with all dependencies
- [x] `Procfile` created with correct entry point
- [x] Database configuration ready (SQLite for free tier)
- [x] Secret keys using environment variables

### Frontend Configuration ✅
- [x] `VITE_API_URL` using environment variables
- [x] `npm run build` tested locally
- [x] All API calls use dynamic URLs
- [x] Environment variables configured

### Files Created ✅
- [x] `Procfile` - Uvicorn start command
- [x] `render.yaml` - Full deployment configuration
- [x] `.env.production` - Production environment template
- [x] `DEPLOYMENT_GUIDE.md` - This file

---

## 📋 STEP-BY-STEP DEPLOYMENT

### Step 1: Prepare Render Account

1. Go to [https://render.com](https://render.com)
2. Sign up or log in with GitHub account
3. Create a new project or use existing one
4. Generate an API token (Settings → API Tokens)

---

### Step 2: Connect GitHub Repository

1. In Render Dashboard, click **"New +"**
2. Select **"Web Service"**
3. Click **"Connect Repository"**
4. Select your GitHub account and repository
5. Click **"Connect"**

---

### Step 3: Deploy Backend (API)

#### Option A: Using Web Service UI

1. **Service Name:** `stockpulse-api`
2. **Environment:** Python
3. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start Command:**
   ```bash
   uvicorn api.app:app --host 0.0.0.0 --port $PORT
   ```
5. **Plan:** Free (recommended for testing)
6. **Region:** Choose closest to your location

#### Option B: Using render.yaml

1. Push `render.yaml` to your repository
2. In Render Dashboard, click **"New +"**
3. Select **"Infrastructure as Code"**
4. Point to your GitHub repo with `render.yaml`
5. Click **"Deploy"**

---

### Step 4: Configure Environment Variables (Backend)

In Render Dashboard for your API service:

1. Go to **Environment** tab
2. Add these variables:

```
DATABASE_URL=sqlite:///./db.sqlite3
SECRET_KEY=<generate-secure-32-char-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_URL=https://stockpulse-frontend.onrender.com
RAZORPAY_KEY_ID=<your-key-if-available>
RAZORPAY_KEY_SECRET=<your-secret-if-available>
PYTHON_ENV=production
NODE_ENV=production
```

**Important:** Generate a secure `SECRET_KEY`:
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

### Step 5: Deploy Frontend (React)

#### Option A: Separate Static Site

1. In Render Dashboard, click **"New +"**
2. Select **"Static Site"**
3. Click **"Connect Repository"**
4. **Service Name:** `stockpulse-frontend`
5. **Build Command:**
   ```bash
   npm install && npm run build
   ```
6. **Publish Directory:** `frontend/dist`
7. Click **"Create Static Site"**

#### Option B: Using render.yaml (Already configured)

The `render.yaml` file includes both API and Frontend. Deploy once and both will be created.

---

### Step 6: Configure Frontend Environment Variables

In Render Dashboard for your Frontend service:

1. Go to **Environment** tab
2. Add this variable:

```
VITE_API_URL=https://stockpulse-api.onrender.com
```

Replace `stockpulse-api` with your actual backend service name.

---

### Step 7: Get Your Service URLs

After deployment completes:

**Backend URL:** `https://<your-backend-name>.onrender.com`
**Frontend URL:** `https://<your-frontend-name>.onrender.com`

Copy these URLs for testing.

---

## 🔧 POST-DEPLOYMENT VERIFICATION

### Test Backend Health

```bash
# Should return status: ok
curl https://<your-backend-name>.onrender.com/health
```

### Test API Documentation

Visit: `https://<your-backend-name>.onrender.com/docs`

You should see Swagger UI with all API endpoints.

### Test Frontend

Visit: `https://<your-frontend-name>.onrender.com`

You should see the StockPulse home page loading.

### Test Trading Flow

1. **Signup:** Create a new account
2. **Login:** Use the credentials you just created
3. **Buy Stock:** Try buying a stock
4. **Check Portfolio:** Verify your holdings appear
5. **Sell Stock:** Try selling the stock
6. **Check Portfolio:** Verify your portfolio is now empty

---

## 🐛 TROUBLESHOOTING

### Backend won't start

**Error:** `ModuleNotFoundError`

**Solution:**
1. Check `requirements.txt` has all dependencies
2. Verify Render build logs for missing packages
3. In Render Dashboard → Logs tab, check build output

### API returns 502 Bad Gateway

**Error:** `502 Bad Gateway`

**Solution:**
1. Check backend service logs in Render Dashboard
2. Verify `Procfile` has correct start command
3. Make sure `SECRET_KEY` is set in environment variables

### Frontend can't connect to API

**Error:** CORS errors or `fetch failed`

**Solution:**
1. Check `VITE_API_URL` is set correctly
2. Verify backend URL in frontend environment variables
3. Check backend CORS configuration allows frontend domain
4. Clear browser cache and do hard refresh (Ctrl+Shift+R)

### Database errors

**Error:** `database is locked` or `disk I/O error`

**Solution:**
1. For production, consider upgrading to PostgreSQL
2. Check Render storage limits
3. Verify database file permissions

---

## 📊 ENVIRONMENT VARIABLES REFERENCE

### Backend (.env or Render Dashboard)

| Variable | Value | Required |
|----------|-------|----------|
| `DATABASE_URL` | `sqlite:///./db.sqlite3` | Yes |
| `SECRET_KEY` | 32+ character random string | Yes |
| `ALGORITHM` | `HS256` | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Yes |
| `FRONTEND_URL` | `https://your-frontend.onrender.com` | Yes |
| `RAZORPAY_KEY_ID` | Your Razorpay key | No |
| `RAZORPAY_KEY_SECRET` | Your Razorpay secret | No |
| `PYTHON_ENV` | `production` | Yes |

### Frontend (Render Dashboard or .env.production)

| Variable | Value | Required |
|----------|-------|----------|
| `VITE_API_URL` | `https://your-backend.onrender.com` | Yes |

---

## ⚡ OPTIMIZATION TIPS

### For Free Tier (Limited Resources)

1. **Database:** Use SQLite for now, migrate to PostgreSQL later
2. **Services:** Render allows multiple free services
3. **Auto-shutdown:** Free tier shuts down after 15 min inactivity - this is normal
4. **Cold starts:** First request after shutdown takes 10-30 seconds

### For Production (Paid Tier)

1. **Database:** Use Render PostgreSQL instead of SQLite
2. **Plan:** Upgrade to paid for always-on services
3. **Monitoring:** Enable health checks in Render Dashboard
4. **Auto-scaling:** Configure for expected traffic

---

## 🔐 SECURITY CHECKLIST

- [x] Never commit `.env` files with secrets
- [x] All secrets use environment variables
- [x] `SECRET_KEY` is unique and secure
- [x] CORS restricted to known domains (not `*`)
- [x] Password hashing enabled (bcrypt)
- [x] JWT tokens have expiration
- [x] HTTPS enforced (Render provides free SSL)
- [x] Database backups configured

---

## 📱 MONITORING & LOGS

### Access Logs in Render Dashboard

1. Go to your service
2. Click **"Logs"** tab
3. View real-time logs:
   - Build logs
   - Deployment logs
   - Runtime logs

### Set Up Alerts (Optional)

1. Go to **Settings** → **Notifications**
2. Enable alerts for:
   - Deployment failures
   - Service crashes
   - Performance issues

---

## 🆘 SUPPORT

### Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| App crashes on startup | Check `SECRET_KEY` is set, verify dependencies in requirements.txt |
| Can't connect to API | Verify `VITE_API_URL` is correct, check CORS settings |
| Blank frontend page | Clear cache, check browser console for errors |
| Slow responses | Free tier may be sleeping, upgrade plan if needed |
| Database locked | SQLite limitation, upgrade to PostgreSQL for production |

### Debug Mode

To enable debug logging (for troubleshooting only):

1. Add to environment variables:
   ```
   DEBUG=true
   LOG_LEVEL=debug
   ```
2. Restart the service
3. Check logs for detailed output

---

## 🎉 DEPLOYMENT COMPLETE!

Your StockPulse app is now live on Render! 

**Next Steps:**
1. Test all features thoroughly
2. Monitor logs for errors
3. Set up backups if needed
4. Share with users
5. Plan scaling strategy

---

## 📞 NEED HELP?

- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Vite Docs:** https://vitejs.dev/guide/
- **GitHub Issues:** Check your repo for issues

---

**Deployed:** April 29, 2026  
**Platform:** Render.com  
**Status:** Production Ready ✅
