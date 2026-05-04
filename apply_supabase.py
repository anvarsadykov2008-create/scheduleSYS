"""
Applies MAIN.sql + add_auth_tables.sql to Supabase.
"""
import psycopg2
import sys
import os

DB_URL = "postgresql://postgres:87076394301@db.pheiouiosqolrcbbrcdu.supabase.co:5432/postgres"

SQL_FILES = [
    os.path.join(os.path.dirname(__file__), "MAIN.sql"),
    os.path.join(os.path.dirname(__file__), "add_auth_tables.sql"),
]

def apply_file(conn, path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("  OK: %s applied" % os.path.basename(path))

def main():
    print("Connecting to Supabase...")
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=15)
        conn.autocommit = False
        print("  Connection established!")
    except Exception as e:
        print("  ERROR connecting: %s" % e)
        sys.exit(1)

    for sql_file in SQL_FILES:
        if not os.path.exists(sql_file):
            print("  SKIP (not found): %s" % sql_file)
            continue
        print("Applying: %s" % os.path.basename(sql_file))
        try:
            apply_file(conn, sql_file)
        except Exception as e:
            conn.rollback()
            print("  ERROR in %s: %s" % (os.path.basename(sql_file), e))
            conn.close()
            sys.exit(1)

    # Check tables count
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        count = cur.fetchone()[0]
        print("\nDone! Tables in public schema: %d" % count)

    conn.close()

if __name__ == "__main__":
    main()
