from app.auth import get_password_hash
import psycopg2

def fix_admin_password():
    password = 'admin'
    hashed = get_password_hash(password)
    
    conn = psycopg2.connect('postgresql://postgres:87474981272@localhost:5432/new_college')
    cur = conn.cursor()
    
    cur.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (hashed,))
    if cur.rowcount == 0:
        print("Admin user not found! Inserting just in case...")
        cur.execute("""
            INSERT INTO users (username, password_hash, role, full_name, is_not_student)
            VALUES ('admin', %s, 'ADMIN', 'Администратор', TRUE)
        """, (hashed,))
        
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Password reset to '{password}' for username 'admin'")
    print(f"Hash generated: {hashed}")

if __name__ == '__main__':
    fix_admin_password()
