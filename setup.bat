@echo off
REM Setup script for STCOK Trading System on Windows

echo.
echo ==========================================
echo  STCOK Trading System - Setup Script
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/5] Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/5] Initializing database...
python -c "from api.models import Base, engine; Base.metadata.create_all(bind=engine)"
echo Database initialized: db.sqlite3

echo [4/5] Setting up frontend...
cd frontend
if exist node_modules (
    echo Node modules already exist, skipping npm install
) else (
    echo Installing npm dependencies...
    call npm install
)
cd ..

echo [5/5] Creating .env file...
if not exist .env (
    copy .env.example .env
    echo Created .env file - please update with your configuration
    echo.
    echo IMPORTANT: Add Razorpay credentials:
    echo - RAZORPAY_KEY_ID
    echo - RAZORPAY_KEY_SECRET
) else (
    echo .env file already exists
)

echo.
echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo To start the system:
echo.
echo Terminal 1 (Backend):
echo   venv\Scripts\activate
echo   python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Then open: http://localhost:8080
echo.
pause
