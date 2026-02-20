import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.getcwd(), 'backend', 'data', 'app.db')
print(f"Checking database at: {db_path}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check all users
    cursor.execute("SELECT id, email, full_name, role, is_active FROM users")
    users = cursor.fetchall()
    
    print("\nUsers in database:")
    for user in users:
        print(f"ID: {user[0]}, Email: {user[1]}, Name: {user[2]}, Role: {user[3]}, Active: {user[4]}")
    
    conn.close()
else:
    print("Database file not found")
