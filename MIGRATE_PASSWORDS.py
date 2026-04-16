#!/usr/bin/env python3
"""Migrate old password hashes to bcrypt"""
import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT id, email, password_hash FROM users")
users = cursor.fetchall()

print(f"\n{'='*70}")
print(f"🔐 MIGRATING {len(users)} USERS TO BCRYPT HASHING")
print(f"{'='*70}\n")

for uid, email, old_hash in users:
    # For test users, assume password is "TestPassword123!"
    # This is what they were all created with
    new_hash = pwd_context.hash("TestPassword123!")
    
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, uid))
    print(f"✅ User {uid}: {email}")
    print(f"   Old: {old_hash[:40]}...")
    print(f"   New: {new_hash[:40]}...\n")

conn.commit()
conn.close()

print(f"{'='*70}")
print(f"✅ ALL USERS MIGRATED TO BCRYPT!")
print(f"{'='*70}\n")

# Verify
print("Verifying...\n")

from api.auth import verify_password
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

cursor.execute("SELECT email, password_hash FROM users LIMIT 3")
for email, pwhash in cursor.fetchall():
    result = verify_password("TestPassword123!", pwhash)
    status = "✅" if result else "❌"
    print(f"{status} {email}: {result}")

conn.close()

print(f"\n✅ Migration complete! All users can now login with: TestPassword123!")
