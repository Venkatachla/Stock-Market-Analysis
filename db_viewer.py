"""
Simple database viewer and manager for SQLite
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "data/platform.db"

def init_db():
    """Initialize and verify database"""
    Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Create users table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT 'free',
            token TEXT,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")

def view_all_users():
    """View all users in database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    users = conn.execute(
        "SELECT id, email, tier, is_admin, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    
    print("\n" + "=" * 80)
    print(f"Total Users: {len(users)}")
    print("=" * 80)
    
    if not users:
        print("No users found")
        return
    
    for user in users:
        print(f"\n{user['id']:3} | {user['email']:40} | {user['tier']:7} | Admin: {bool(user['is_admin'])}")
        print(f"     Created: {user['created_at']}")
    
    print("\n" + "=" * 80)
    conn.close()

def delete_user(email):
    """Delete a user by email"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    rows = conn.total_changes
    conn.close()
    
    if rows > 0:
        print(f"✓ Deleted user: {email}")
    else:
        print(f"✗ User not found: {email}")

def clear_all_users():
    """Clear all users from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM users")
    conn.commit()
    print("✓ All users deleted")
    conn.close()

def get_db_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    user_count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    db_size = Path(DB_PATH).stat().st_size if Path(DB_PATH).exists() else 0
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)
    print(f"Database File: {DB_PATH}")
    print(f"File Size: {db_size / 1024:.1f} KB")
    print(f"Total Users: {user_count}")
    print(f"Status: {'✓ ACTIVE' if Path(DB_PATH).exists() else '✗ NOT FOUND'}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    import sys
    
    # Initialize database first
    init_db()
    
    # Show stats
    get_db_stats()
    
    # Show all users
    view_all_users()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clear":
            confirm = input("\nAre you sure you want to delete ALL users? Type 'yes' to confirm: ")
            if confirm == "yes":
                clear_all_users()
                get_db_stats()
        
        elif command == "delete" and len(sys.argv) > 2:
            delete_user(sys.argv[2])
