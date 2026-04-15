"""
Complete startup script - runs Backend, Frontend, and displays status
"""
import subprocess
import time
import sys
import os
from pathlib import Path

print("\n" + "=" * 80)
print("STOCKPULSE - COMPLETE STARTUP")
print("=" * 80 + "\n")

# 1. Verify Database
print("1. Checking Database...")
db_path = Path("data/platform.db")
if db_path.exists():
    print(f"   ✓ Database exists: {db_path} ({db_path.stat().st_size / 1024:.0f} KB)")
else:
    print("   ✗ Database not found - initializing...")
    subprocess.run([sys.executable, "add_demo_users.py"], capture_output=True)

# 2. Check if backend is running
print("\n2. Checking Backend...")
try:
    import requests
    response = requests.get("http://127.0.0.1:8000/docs", timeout=2)
    print("   ✗ Backend already running on port 8000")
    print("   Please run: Kill any other Python processes and restart")
except:
    print("   Starting Backend Server...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    print("   ✓ Backend started (PID: {})".format(backend_process.pid))

# 3. Check if frontend is running
print("\n3. Checking Frontend...")
try:
    import requests
    response = requests.get("http://localhost:8080", timeout=2)
    print("   ✓ Frontend already running on port 8080")
except:
    print("   Starting Frontend Server...")
    os.chdir("frontend")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    os.chdir("..")
    time.sleep(3)
    print("   ✓ Frontend started (PID: {})".format(frontend_process.pid))

# 4. Display credentials
print("\n" + "=" * 80)
print("SYSTEM READY")
print("=" * 80)
print("\nAccess URLs:")
print("  Frontend:  http://localhost:8080")
print("  Backend:   http://127.0.0.1:8000")
print("  API Docs:  http://127.0.0.1:8000/docs")
print("\nDemo Credentials:")
print("  Email:    admin@example.com")
print("  Password: password123")
print("\n" + "=" * 80 + "\n")
