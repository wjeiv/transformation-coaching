import sqlite3

conn = sqlite3.connect('/app/data/app.db')
cursor = conn.cursor()

# Update admin email
cursor.execute('UPDATE users SET email = ? WHERE email = ?', ('admin@transformationcoaching.com', 'admin'))
conn.commit()

# Verify update
cursor.execute('SELECT id, email, full_name, role, is_active FROM users WHERE role = "ADMIN"')
admin = cursor.fetchone()
print(f'Updated admin: ID: {admin[0]}, Email: {admin[1]}, Name: {admin[2]}, Role: {admin[3]}, Active: {admin[4]}')

conn.close()
