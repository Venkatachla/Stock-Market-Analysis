#!/usr/bin/env python3
"""Test backend connectivity"""
import requests
import sys

print("\n" + "="*70)
print("🔍 TESTING BACKEND CONNECTIVITY")
print("="*70 + "\n")

try:
    print("Testing: http://localhost:8000/health")
    resp = requests.get("http://localhost:8000/health", timeout=3)
    print(f"✅ Status: {resp.status_code}")
    print(f"Response: {resp.text[:200]}\n")
except Exception as e:
    print(f"❌ Connection failed: {e}\n")
    sys.exit(1)

print("="*70)
print("Testing auth signup endpoint:")
print("="*70 + "\n")

try:
    data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test"
    }
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:8080'
    }
    
    resp = requests.post(
        "http://localhost:8000/api/auth/signup",
        json=data,
        headers=headers,
        timeout=3
    )
    print(f"✅ Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}\n")
    
except Exception as e:
    print(f"❌ Request failed: {e}\n")
    sys.exit(1)

print("="*70)
print("✅ BACKEND IS RESPONDING")
print("="*70)
