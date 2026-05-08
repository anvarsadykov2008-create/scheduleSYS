import psycopg2
SUPABASE_URL = "postgresql://postgres.pheiouiosqolrcbbrcdu:87076394301@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
conn = psycopg2.connect(SUPABASE_URL, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

fixes = [
    # teachers: add home_room_id (FK to rooms.id, not room_id)
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS home_room_id BIGINT REFERENCES rooms(id) ON DELETE SET NULL",
    # Also remove the bad reference we added earlier
    "ALTER TABLE teachers DROP COLUMN IF EXISTS is_head_of_department",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_head_of_department BOOLEAN DEFAULT FALSE",
]

for sql in fixes:
    try:
        cur.execute(sql)
        print(f"OK: {sql[:80]}")
    except Exception as e:
        print(f"SKIP: {str(e)[:120]}")

# Verify
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='teachers' ORDER BY ordinal_position")
print("\nteachers columns:", [r[0] for r in cur.fetchall()])

conn.close()
print("\nDone!")
