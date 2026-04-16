@echo off
REM STCOK Trading System - COMPLETE FIXED STARTUP
REM This script starts the backend with app_fixed.py and frontend with proper logging

echo.
echo ====================================================
echo  STCOK Trading System - COMPLETE FIXED STARTUP
echo ====================================================
echo.

REM Kill any existing processes
echo [1/6] Cleaning up existing processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

REM Start backend with app_fixed.py
echo.
echo [2/6] Starting backend on port 8000 with app_fixed.py...
echo.
cd /d c:\Users\Venkatachala V\STCOK
start "STCOK Backend" cmd /k "python -m uvicorn api.app_fixed:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 >nul

REM Start frontend
echo.
echo [3/6] Starting frontend on port 8080...
echo.
cd /d c:\Users\Venkatachala V\STCOK\frontend
start "STCOK Frontend" cmd /k "npm run dev"
timeout /t 3 >nul

echo.
echo ====================================================
echo  ✅ SYSTEM STARTUP COMPLETE
echo ====================================================
echo.
echo 📊 Backend: http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo    - Health: http://localhost:8000/health
echo.
echo 🌐 Frontend: http://localhost:8080
echo.
echo 🧪 Test CORS immediately by running:
echo    CORS_TEST.bat
echo.
echo 📝 Quick test:
echo    1. Open http://localhost:8080 in browser
echo    2. Click "Get Started"
echo    3. Sign up with: test@example.com / password123
echo.
echo ====================================================
echo.
pause
