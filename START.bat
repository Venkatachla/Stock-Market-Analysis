@echo off
REM Start STCOK Trading System - Windows Batch Script

cd /d "%~dp0"

echo.
echo ================================================================================
echo           STOCKPULSE - AI Trading Dashboard
echo ================================================================================
echo.

REM Kill any running Python processes on port 8000
echo Cleaning up old processes...
taskkill /F /IM python.exe /T 2>nul

timeout /t 2 /nobreak

REM Start Backend
echo.
echo Starting Backend Server...
start "StockPulse Backend" cmd /k "python -m uvicorn api.app:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak

REM Start Frontend
echo Starting Frontend Server...
cd frontend
start "StockPulse Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ================================================================================
echo.
echo Web Application starting:
echo   Frontend:  http://localhost:8080
echo   Backend:   http://127.0.0.1:8000
echo.
echo Demo Login:
echo   Email:     admin@example.com
echo   Password:  password123
echo.
echo ================================================================================
echo.

timeout /t 5

REM Open browser
start http://localhost:8080

pause
