import psycopg2

def check():
    conn = psycopg2.connect('postgresql://postgres:87474981272@localhost:5432/new_college')
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Total tables: {len(tables)}")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"{t}: {count} rows")
    cur.close()
    conn.close()

if __name__ == '__main__':
    check()
