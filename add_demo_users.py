"""
Script to create demo users for authentication testing
"""
import sqlite3
import hashlib
import secrets
from datetime import datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db(conn):
    """Initialize database tables"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT 'free',
            token TEXT,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

def add_demo_users():
    # Use the same database path as the backend
    db_path = "data/platform.db"
    
    # Ensure data directory exists
    import os
    from pathlib import Path
    Path("data").mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Using database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Initialize database tables
    init_db(conn)
    print("✓ Database tables initialized")
    
    demo_users = [
        {
            "email": "admin@example.com",
            "password": "password123",
            "tier": "premium",
            "is_admin": 1
        },
        {
            "email": "trader@example.com", 
            "password": "password123",
            "tier": "free",
            "is_admin": 0
        },
        {
            "email": "investor@example.com",
            "password": "password123",
            "tier": "pro",
            "is_admin": 0
        }
    ]
    
    for user in demo_users:
        try:
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO users (email, password_hash, tier, token, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user["email"],
                    hash_password(user["password"]),
                    user["tier"],
                    token,
                    user["is_admin"],
                    datetime.now().isoformat()
                )
            )
            print(f"✓ Created user: {user['email']} (tier: {user['tier']})")
        except sqlite3.IntegrityError:
            print(f"⚠ User {user['email']} already exists, skipping...")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Demo users created successfully!")
    print("\nYou can now login with:")
    for user in demo_users:
        print(f"  Email: {user['email']}")
        print(f"  Password: {user['password']}")
        print()

if __name__ == "__main__":
    add_demo_users()
