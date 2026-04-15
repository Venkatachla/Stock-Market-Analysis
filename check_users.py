import sqlite3

conn = sqlite3.connect('db.sqlite3')
conn.row_factory = sqlite3.Row
cursor = conn.execute('SELECT email, tier FROM users')
users = cursor.fetchall()
print('Users in database:')
for user in users:
    print(f"  - {user['email']} ({user['tier']})")
conn.close()
