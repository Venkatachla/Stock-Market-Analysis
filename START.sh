#!/bin/bash

# STOCK TRADING SYSTEM - STARTUP SCRIPT (LINUX/MAC)
# Starts backend (FastAPI) and frontend (React) servers

set -e

cd "$(dirname "$0")"

echo
echo "================================================================================"
echo "           STOCK TRADING SYSTEM - PRODUCTION STARTUP"
echo "================================================================================"
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo
    echo "ERROR: .env file not found!"
    echo
    echo "FIRST TIME SETUP:"
    echo "  1. Copy .env.example to .env"
    echo "     cp .env.example .env"
    echo
    echo "  2. Edit .env and set your values:"
    echo "     - RAZORPAY_KEY_ID (optional)"
    echo "     - RAZORPAY_SECRET (optional)"
    echo "     - SECRET_KEY (required for JWT)"
    echo
    echo "  3. Initialize database:"
    echo "     python3 -c \"from api.models import Base, engine; Base.metadata.create_all(engine)\""
    echo
    echo "  4. Then run this script again."
    echo
    exit 1
fi

echo "[1/5] Cleaning up old processes..."
pkill -f "uvicorn" || true
pkill -f "npm run dev" || true
sleep 2

echo "[2/5] Checking backend virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
fi

echo "[3/5] Starting Backend Server (FastAPI)..."
echo "  Port: 8000"
echo "  Docs: http://localhost:8000/docs"
source venv/bin/activate
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
deactivate
sleep 4

echo "[4/5] Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies (npm install)..."
    cd frontend
    npm install
    cd ..
fi

echo "[5/5] Starting Frontend Server (Vite)..."
echo "  Port: 5173"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo
echo "================================================================================"
echo
echo "✓ SERVERS STARTING..."
echo
echo "  Frontend:   http://localhost:5173"
echo "  Backend:    http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo
echo "FIRST TIME USER:"
echo "  1. Create account: Click 'Sign Up'"
echo "  2. Add demo funds: Click wallet icon"
echo "  3. Buy/Sell stocks: Use dashboard predictions"
echo
echo "TROUBLESHOOTING:"
echo "  - Port 8000 in use?  Export UVICORN_PORT=8001"
echo "  - Port 5173 in use?  Set VITE_PORT=5174"
echo "  - ML models missing? Place .pkl files in models/ directory"
echo "  - .env issues?       Check SETUP_GUIDE.md"
echo
echo "================================================================================"
echo
echo "To stop servers, press Ctrl+C"
echo
echo "Processes running:"
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo

# Keep script running
wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true

echo
echo "Servers stopped."
