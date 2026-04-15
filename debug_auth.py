import sqlite3
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# Check what the hash would be
test_password = "password123"
hashed = hash_password(test_password)
print(f"Password: {test_password}")
print(f"Hashed: {hashed}")

# Check what's in the database
conn = sqlite3.connect('db.sqlite3')
conn.row_factory = sqlite3.Row
cursor = conn.execute('SELECT email, password_hash FROM users WHERE email = ?', ('admin@example.com',))
user = cursor.fetchone()

if user:
    print(f"\nUser found in DB:")
    print(f"Email: {user['email']}")
    print(f"Password hash in DB: {user['password_hash']}")
    print(f"Match: {user['password_hash'] == hashed}")
else:
    print("User not found")
    
conn.close()
