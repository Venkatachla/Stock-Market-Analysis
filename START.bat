@echo off
REM STOCK TRADING SYSTEM - STARTUP SCRIPT (WINDOWS)
REM Starts backend (FastAPI) and frontend (React) servers

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ================================================================================
echo              STOCK TRADING SYSTEM - PRODUCTION STARTUP
echo ================================================================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo.
    echo FIRST TIME SETUP:
    echo   1. Copy .env.example to .env
    echo      copy .env.example .env
    echo.
    echo   2. Edit .env and set your values:
    echo      - RAZORPAY_KEY_ID (optional)
    echo      - RAZORPAY_SECRET (optional)
    echo      - SECRET_KEY (required for JWT)
    echo.
    echo   3. Initialize database:
    echo      python -c "from api.models import Base, engine; Base.metadata.create_all(engine)"
    echo.
    echo   4. Then run this script again.
    echo.
    pause
    exit /b 1
)

echo [1/5] Cleaning up old processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak

echo [2/5] Checking backend virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo WARNING: Python virtual environment not found.
    echo Creating venv...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Installing Python dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    exit /b 0
)

echo [3/5] Starting Backend Server (FastAPI)...
echo   Port: 8000
echo   Docs: http://localhost:8000/docs
start "STOCK_BACKEND" cmd /k "venv\Scripts\activate.bat & python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 4 /nobreak

echo [4/5] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies (npm install)...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install npm packages
        pause
        exit /b 1
    )
    cd ..
)

echo [5/5] Starting Frontend Server (Vite)...
echo   Port: 5173
cd frontend
start "STOCK_FRONTEND" cmd /k "npm run dev"
cd ..

echo.
echo ================================================================================
echo.
echo ✓ SERVERS STARTING...
echo.
echo   Frontend:   http://localhost:5173
echo   Backend:    http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo.
echo FIRST TIME USER:
echo   1. Create account: Click "Sign Up"
echo   2. Add demo funds: Click wallet icon
echo   3. Buy/Sell stocks: Use dashboard predictions
echo.
echo TROUBLESHOOTING:
echo   - Port 8000 in use?  Set UVICORN_PORT environment variable
echo   - Port 5173 in use?  Set VITE_PORT environment variable
echo   - ML models missing? Place .pkl files in models/ directory
echo   - .env issues?       Check SETUP_GUIDE.md
echo.
echo ================================================================================
echo.
echo Press any key to open http://localhost:5173 in browser...
pause

REM Open browser
start http://localhost:5173

echo.
echo Type 'exit' in either terminal window to stop the server.
echo.
pause
