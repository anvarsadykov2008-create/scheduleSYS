"""
Check Supabase schema and add missing columns to match SQLAlchemy models.
"""
import psycopg2

SUPABASE_URL = "postgresql://postgres.pheiouiosqolrcbbrcdu:87076394301@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

# ALTER TABLE statements to add missing columns
ALTER_STATEMENTS = [
    # teachers table
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS employee_code VARCHAR(50)",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS home_room_id INTEGER REFERENCES rooms(room_id) ON DELETE SET NULL",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_head_of_department BOOLEAN DEFAULT FALSE",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",

    # rooms table - check if 'id' or 'room_id' is primary key
    "ALTER TABLE rooms ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE rooms ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    "ALTER TABLE rooms ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",

    # groups table
    "ALTER TABLE groups ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE groups ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    "ALTER TABLE groups ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",

    # subjects table
    "ALTER TABLE subjects ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE subjects ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    "ALTER TABLE subjects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",
]

def main():
    conn = psycopg2.connect(SUPABASE_URL, connect_timeout=15)
    conn.autocommit = True
    cur = conn.cursor()

    # Show current tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables in Supabase:", tables)
    print()

    # Show teachers columns
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='teachers' ORDER BY ordinal_position")
    cols = cur.fetchall()
    print("teachers columns:", [r[0] for r in cols])
    print()

    # Apply fixes
    print("Applying schema fixes...")
    for sql in ALTER_STATEMENTS:
        try:
            cur.execute(sql)
            print(f"  OK: {sql[:70]}...")
        except Exception as e:
            print(f"  SKIP: {str(e)[:100]}")

    # Show teachers columns after fix
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='teachers' ORDER BY ordinal_position")
    cols = [r[0] for r in cur.fetchall()]
    print("\nteachers columns after fix:", cols)

    cur.close()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
