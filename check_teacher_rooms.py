import psycopg2
SUPABASE_URL = "postgresql://postgres.pheiouiosqolrcbbrcdu:87076394301@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
conn = psycopg2.connect(SUPABASE_URL, connect_timeout=15)
cur = conn.cursor()

# Check teacher_rooms
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='teacher_rooms' ORDER BY ordinal_position")
print("teacher_rooms:", [r[0] for r in cur.fetchall()])

# Add teacher_rooms table if missing
cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='teacher_rooms')")
exists = cur.fetchone()[0]
print("teacher_rooms exists:", exists)

if not exists:
    cur.execute("""
        CREATE TABLE teacher_rooms (
            id BIGSERIAL PRIMARY KEY,
            teacher_id BIGINT NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
            room_id BIGINT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT uq_teacher_room UNIQUE (teacher_id, room_id)
        )
    """)
    conn.commit()
    print("teacher_rooms created!")

conn.close()
