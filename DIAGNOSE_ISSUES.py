#!/usr/bin/env python3
"""
DEEP DIAGNOSTIC - Find exact error messages 
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000"
CORS_ORIGIN = "http://localhost:8080"

def test_signup_error():
    """Capture exact signup error"""
    print("\n" + "="*70)
    print("🔍 TESTING SIGNUP ENDPOINT - Capturing Error Details")
    print("="*70 + "\n")
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': CORS_ORIGIN,
    }
    
    data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/signup",
            json=data,
            headers=headers,
            timeout=5
        )
        
        print(f"Status Code: {resp.status_code}")
        print(f"\nResponse Headers:")
        for key, value in resp.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nResponse Body:")
        try:
            resp_json = resp.json()
            print(json.dumps(resp_json, indent=2))
        except:
            print(resp.text[:500])
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def check_available_endpoints():
    """Check what endpoints are available"""
    print("\n" + "="*70)
    print("🔍 CHECKING AVAILABLE ENDPOINTS")
    print("="*70 + "\n")
    
    headers = {
        'Origin': CORS_ORIGIN,
    }
    
    endpoints = [
        "/health",
        "/api/auth/signup",
        "/api/auth/login", 
        "/api/users",
        "/api/wallet",
        "/api/stocks",
        "/api/signals",
        "/api/predictions",
        "/docs"
    ]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(
                f"{API_BASE}{endpoint}",
                headers=headers,
                timeout=2
            )
            status = f"✅ {resp.status_code}"
        except requests.Timeout:
            status = "⏱️ TIMEOUT"
        except requests.ConnectionError:
            status = "❌ CONNECTION ERROR"
        except Exception as e:
            status = f"❌ {str(e)[:30]}"
        
        print(f"{endpoint:<30} {status}")

def check_database():
    """Check database setup"""
    print("\n" + "="*70)
    print("🔍 CHECKING DATABASE")
    print("="*70 + "\n")
    
    import os
    db_path = "db.sqlite3"
    
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ Database exists: {db_path} ({size:,} bytes)")
        
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"\n✅ Database tables ({len(tables)}):")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"   • {table[0]:<20} ({count:,} rows)")
            conn.close()
        except Exception as e:
            print(f"❌ Error reading database: {e}")
    else:
        print(f"❌ Database NOT FOUND: {db_path}")

def check_imports():
    """Check if critical modules import properly"""
    print("\n" + "="*70)
    print("🔍 CHECKING PYTHON IMPORTS")
    print("="*70 + "\n")
    
    modules = [
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "passlib",
        "jwt",
        "requests",
        "pandas",
        "numpy",
        "torch",
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module:<20} OK")
        except ImportError as e:
            print(f"❌ {module:<20} MISSING - {e}")

def main():
    print("\n╔" + "="*68 + "╗")
    print("║ 🔍 SYSTEM DIAGNOSTIC - Detailed Error Analysis              ║")
    print("╚" + "="*68 + "╝")
    
    print(f"\nBackend: {API_BASE}")
    print(f"Frontend: {CORS_ORIGIN}\n")
    
    check_imports()
    check_database()
    check_available_endpoints()
    test_signup_error()
    
    print("\n" + "="*70)
    print("✅ DIAGNOSTIC COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
