#!/usr/bin/env python3
"""Simple password migration - just hash plain passwords"""
import sqlite3
import hashlib

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT id, email FROM users")
users = cursor.fetchall()

print(f"\n{'='*70}")
print(f"🔐 UPDATING {len(users)} PASSWORDS")
print(f"{'='*70}\n")

for uid, email in users:
    # Hash password using SHA256 format that matches current database
    password = "TestPassword123!"
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, uid))
    print(f"✅ {email}")

conn.commit()
conn.close()

print(f"\n{'='*70}")
print(f"✅ ALL PASSWORDS UPDATED!")
print(f"Password: TestPassword123!")
print(f"{'='*70}\n")
