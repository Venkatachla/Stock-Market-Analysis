import sqlite3
import os

db_path = 'c:/Users/Asus/Documents/devops/Stock-Market-Analysis/db.sqlite3'

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS holdings")
        cursor.execute("DROP TABLE IF EXISTS wallets")
        cursor.execute("DROP TABLE IF EXISTS transactions")
        cursor.execute("DROP TABLE IF EXISTS users")
        conn.commit()
        conn.close()
        print("✅ Tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping tables: {str(e)}")
else:
    print("⚠️ DB file not found")
