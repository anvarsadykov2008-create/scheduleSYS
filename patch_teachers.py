import psycopg2

def patch_db():
    conn_str = "dbname='schedulesys' user='postgres' password='raim100100' host='localhost' port='5432'"
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    # Check if columns exist
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='teachers'")
    cols = [r[0] for r in cur.fetchall()]
    
    queries = []
    if 'home_room_id' not in cols:
        queries.append("ALTER TABLE teachers ADD COLUMN home_room_id BIGINT REFERENCES rooms(id);")
    if 'is_head_of_department' not in cols:
        queries.append("ALTER TABLE teachers ADD COLUMN is_head_of_department BOOLEAN DEFAULT FALSE;")
    if 'department_id' not in cols:
        queries.append("ALTER TABLE teachers ADD COLUMN department_id BIGINT REFERENCES departments(id);")
        
    for q in queries:
        print("Running:", q)
        cur.execute(q)
        
    conn.commit()
    cur.close()
    conn.close()
    print("Patch complete.")

if __name__ == '__main__':
    patch_db()
