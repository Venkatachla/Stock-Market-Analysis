# 🌍 STOCKPULSE RENDER DEPLOYMENT - QUICK START

**Skip the long guide? Use this 5-minute checklist instead.**

---

## ✅ 5-MINUTE DEPLOYMENT CHECKLIST

### 1. GitHub Setup (1 min)
- [ ] Push code to GitHub with all files
- [ ] Verify `requirements.txt` is in root
- [ ] Verify `Procfile` exists in root
- [ ] Verify `render.yaml` exists in root

### 2. Render Backend Setup (2 min)

1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Fill in:
   - **Name:** `stockpulse-api`
   - **Region:** Pick closest to you
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api.app:app --host 0.0.0.0 --port $PORT`

### 3. Add Backend Environment Variables (1 min)

In the Web Service form, scroll to **Environment** and add:

```
SECRET_KEY=use-any-random-32-char-string-here!
FRONTEND_URL=https://stockpulse-frontend.onrender.com
DATABASE_URL=sqlite:///./db.sqlite3
PYTHON_ENV=production
```

Click **"Create Web Service"** and wait 5-10 minutes for deployment.

### 4. Get Backend URL

After deployment, you'll see: `https://stockpulse-api-xxxx.onrender.com`

Save this URL!

### 5. Render Frontend Setup (1 min)

1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repo
3. Fill in:
   - **Name:** `stockpulse-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/dist`

### 6. Add Frontend Environment Variables (0.5 min)

In the Static Site form, add:

```
VITE_API_URL=https://stockpulse-api-xxxx.onrender.com
```

(Replace `xxxx` with your actual backend service name)

Click **"Create Static Site"** and wait 5-10 minutes.

### 7. Test Your App (0.5 min)

After frontend deploys:

1. Visit frontend URL: `https://stockpulse-frontend-xxxx.onrender.com`
2. Sign up with email/password
3. Try buying a stock
4. Check portfolio
5. Try selling a stock

✅ If all works, you're done!

---

## 🔗 YOUR DEPLOYMENT URLS

After deployment, replace these in your notes:

```
Backend API:  https://stockpulse-api-YOUR-ID.onrender.com
Frontend:     https://stockpulse-frontend-YOUR-ID.onrender.com
```

---

## 🆘 If Something Fails

### Backend won't deploy?
- Check logs: Go to service → **Logs** tab
- Common issue: Missing `SECRET_KEY` environment variable
- Fix: Add `SECRET_KEY=random-string-here` to environment

### Frontend won't load?
- Check browser console (F12 → Console tab)
- Common issue: Wrong `VITE_API_URL`
- Fix: Update environment variable to match backend URL

### Can't log in?
- Check backend is running: Visit `/health` endpoint
- Check frontend can reach backend: Open browser DevTools → Network tab
- Try hard refresh: `Ctrl+Shift+R`

---

## 📊 VERIFY DEPLOYMENT

### Backend Health Check
```bash
curl https://your-backend-url/health
# Should return: {"status":"ok"}
```

### Frontend Check
Visit: `https://your-frontend-url`
Should see StockPulse home page

### API Docs
Visit: `https://your-backend-url/docs`
Should see Swagger UI

---

## 🚀 YOU'RE LIVE!

Your StockPulse app is deployed to production. Share the frontend URL with users!

---

**Need more details?** Read `DEPLOYMENT_GUIDE.md` for complete instructions.
