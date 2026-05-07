# ⚡ STOCKPULSE RENDER DEPLOYMENT - QUICK REFERENCE CARD

**Print this or bookmark it!**

---

## 📋 FILES YOU NEED

```
Root Directory:
✅ Procfile - START COMMAND
✅ render.yaml - FULL CONFIG
✅ requirements.txt - DEPENDENCIES
✅ .env.production - ENV TEMPLATE

Frontend:
✅ frontend/package.json - BUILD CONFIG
✅ frontend/src/services/api.ts - USES ENV VAR
✅ frontend/src/contexts/AuthContext.tsx - USES ENV VAR

Backend:
✅ api/app.py - CORS FIXED
✅ requirements.txt - COMPLETE
```

---

## 🚀 DEPLOYMENT IN 5 STEPS

### Step 1: Connect GitHub to Render
```
render.com → New → Infrastructure as Code → Connect GitHub
```

### Step 2: Select render.yaml
```
Render auto-detects render.yaml → Deploy
```

### Step 3: Wait for Build
```
Monitor in Render Dashboard → Logs tab
(Typically 5-10 minutes)
```

### Step 4: Backend Environment Variables
```
Service: stockpulse-api
Add:
  SECRET_KEY = (auto-generated)
  FRONTEND_URL = https://stockpulse-frontend.onrender.com
  PYTHON_ENV = production
```

### Step 5: Frontend Environment Variables
```
Service: stockpulse-frontend
Add:
  VITE_API_URL = https://stockpulse-api.onrender.com
  (Use your actual backend service name)
```

---

## ✅ VERIFY IT WORKS

```bash
# Backend health
curl https://stockpulse-api-xxx.onrender.com/health

# Frontend
Visit https://stockpulse-frontend-xxx.onrender.com

# Trade flow
1. Sign up
2. Add funds (₹10,000)
3. Buy RELIANCE
4. Check portfolio
5. Sell RELIANCE
6. Verify wallet back to ₹10,000
```

---

## 🔐 KEY CREDENTIALS

| Item | Value | Status |
|------|-------|--------|
| `SECRET_KEY` | Generate secure random | ✅ In Render |
| `FRONTEND_URL` | https://stockpulse-frontend.onrender.com | ✅ Configured |
| `VITE_API_URL` | https://stockpulse-api.onrender.com | ✅ Configured |
| Database | SQLite (in repo) | ✅ Works |

---

## 🔗 YOUR FINAL URLS

```
Backend:  https://stockpulse-api-abc123.onrender.com
Frontend: https://stockpulse-frontend-abc123.onrender.com
API Docs: https://stockpulse-api-abc123.onrender.com/docs
```

---

## 🆘 IF IT FAILS

| Problem | Fix |
|---------|-----|
| Backend won't start | Check Render Logs tab |
| Can't reach API | Verify VITE_API_URL env var |
| Blank frontend page | Clear cache, hard refresh (Ctrl+Shift+R) |
| Database locked | Use PostgreSQL instead of SQLite |
| CORS error | Check FRONTEND_URL in backend env vars |

---

## 📚 DETAILED DOCS

For complete information, read:
- `RENDER_DEPLOYMENT_COMPLETE.md` - Full deployment guide (THIS PACKAGE)
- `DEPLOYMENT_GUIDE.md` - Step-by-step guide
- `DEPLOYMENT_QUICK_START.md` - 5-minute version
- `ENVIRONMENT_VARIABLES.md` - Env var reference
- `VERIFICATION_CHECKLIST.md` - Test everything

---

## ⏱️ TIMELINE

```
Total time: ~15 minutes

5 min  → Connect GitHub & deploy
5 min  → Set environment variables
3 min  → Wait for services to restart
2 min  → Test everything
```

---

## 🎯 SUCCESS CRITERIA

- [ ] Backend service shows "Live" in Render Dashboard
- [ ] Frontend service shows "Live" in Render Dashboard
- [ ] Backend health endpoint returns `{"status":"ok"}`
- [ ] Frontend page loads without errors
- [ ] Can sign up and log in
- [ ] Can buy and sell stocks
- [ ] Portfolio updates correctly

---

## 🚀 YOU'RE READY TO DEPLOY!

**No more changes needed. Deploy now following the 5 steps above.**

---

**Date:** April 29, 2026  
**Status:** Production Ready ✅  
**Questions?** See DEPLOYMENT_GUIDE.md for detailed instructions
