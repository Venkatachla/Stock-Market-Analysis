#!/usr/bin/env python3
"""Check password hash in database"""
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

cursor.execute("SELECT id, email, password_hash FROM users WHERE email = 'demo1776275409@test.com'")
row = cursor.fetchone()

if row:
    uid, email, pwhash = row
    print(f"User ID: {uid}")
    print(f"Email: {email}")
    print(f"Password Hash: {pwhash[:60]}...")
    print(f"Hash Length: {len(pwhash)}")
    print(f"Hash Type: {'bcrypt' if pwhash.startswith('$2') else 'unknown/plaintext'}")
    
    # Try to verify it
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    try:
        result = pwd_context.verify("TestPassword123!", pwhash)
        print(f"✅ Password verification result: {result}")
    except Exception as e:
        print(f"❌ Password verification error: {e}")
else:
    print("❌ User not found")

conn.close()
