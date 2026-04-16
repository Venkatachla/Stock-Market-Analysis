#!/usr/bin/env python3
"""Show available user credentials"""
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT id, email FROM users LIMIT 15")
users = cursor.fetchall()

print("\n" + "="*70)
print("📋 AVAILABLE TEST USER CREDENTIALS")
print("="*70 + "\n")

print(f"Total users in database: {len(users)}\n")
print(f"{'ID':<3} {'EMAIL':<35} {'PASSWORD':<20}")
print("-"*70)

for uid, email in users:
    print(f"{uid:<3} {email:<35} TestPassword123!")

print("\n" + "="*70)
print("✅ HOW TO USE:")
print("="*70)
print("""
Option 1: Login with existing user
  1. Go to: http://localhost:8080/login
  2. Email: (pick any email from list above)
  3. Password: TestPassword123!
  4. Click "Sign In"

Option 2: Create new user (signup)
  1. Go to: http://localhost:8080/signup
  2. Email: newtester@example.com
  3. Password: TestPassword123!
  4. Confirm: TestPassword123!
  5. Click "Create Account"
""")

conn.close()
