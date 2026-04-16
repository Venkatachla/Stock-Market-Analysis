#!/usr/bin/env python3
"""Debug login issue"""
import sqlite3
import requests

# Check if user exists
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Try to get the database schema and user
cursor.execute("SELECT id, email FROM users WHERE email = 'demo1776275409@test.com'")
user = cursor.fetchone()

if user:
    print(f"✅ User found in DB: ID={user[0]}, Email={user[1]}")
else:
    print("❌ User NOT found in DB")

conn.close()

# Test the API
print("\nTesting API login...")
try:
    r = requests.post(
        'http://localhost:8000/api/auth/login',
        json={
            'email': 'demo1776275409@test.com',
            'password': 'TestPassword123!'
        },
        headers={'Origin': 'http://localhost:8080'},
        timeout=5
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
