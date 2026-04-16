#!/usr/bin/env python3
"""Check database schema and fix token column issue"""
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()

print("\n📊 USERS TABLE SCHEMA:")
print("="*70)
for col in columns:
    print(f"  • {col[1]:<20} {col[2]:<15}")

print("\n✅ FIXING: Adding missing token column...")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN token TEXT")
    conn.commit()
    print("✅ Token column added successfully!")
except sqlite3.OperationalError as e:
    if "already exists" in str(e):
        print("✅ Token column already exists")
    else:
        print(f"❌ Error: {e}")

# Verify fix
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("\n📊 UPDATED SCHEMA:")
print("="*70)
for col in columns:
    print(f"  • {col[1]:<20} {col[2]:<15}")

conn.close()
