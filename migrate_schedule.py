"""
Migrates schedule table with triggers disabled temporarily.
"""
import psycopg2
import psycopg2.extras
import sys

LOCAL_URL = "postgresql://postgres:87474981272@localhost:5432/schedulesysss"
SUPABASE_URL = "postgresql://postgres:87076394301@db.pheiouiosqolrcbbrcdu.supabase.co:5432/postgres"

def connect(url, label):
    try:
        conn = psycopg2.connect(url, connect_timeout=15)
        conn.autocommit = False
        print("  Connected to %s" % label)
        return conn
    except Exception as e:
        print("  ERROR: %s" % e)
        sys.exit(1)

def get_columns(conn, table):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            ORDER BY ordinal_position
        """, (table,))
        return cur.fetchall()

def serialize_value(val, dtype):
    if dtype in ('jsonb', 'json') and isinstance(val, (dict, list)):
        return psycopg2.extras.Json(val)
    return val

def main():
    print("Connecting...")
    src = connect(LOCAL_URL, "local")
    dst = connect(SUPABASE_URL, "supabase")

    # Get column info
    src_col_info = get_columns(src, "schedule")
    dst_col_info = get_columns(dst, "schedule")
    dst_col_names = {c[0] for c in dst_col_info}
    dst_col_types = {c[0]: c[1] for c in dst_col_info}

    common = [(c, t) for c, t in src_col_info if c in dst_col_names]
    col_names = [c for c, _ in common]

    # Fetch source data
    print("Fetching schedule rows from local DB...")
    with src.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute('SELECT %s FROM "schedule"' % ", ".join('"%s"' % c for c in col_names))
        rows = cur.fetchall()
    print("  Found %d rows" % len(rows))

    if not rows:
        print("  Nothing to migrate.")
        src.close()
        dst.close()
        return

    # Prepare insert
    cols_sql = ", ".join('"%s"' % c for c in col_names)
    placeholders = ", ".join(["%s"] * len(col_names))
    insert_sql = 'INSERT INTO "schedule" (%s) VALUES (%s) ON CONFLICT DO NOTHING' % (cols_sql, placeholders)

    data = []
    for row in rows:
        serialized = tuple(serialize_value(row[c], dst_col_types.get(c, '')) for c in col_names)
        data.append(serialized)

    # Disable triggers, insert, re-enable
    print("Disabling user triggers on schedule...")
    with dst.cursor() as cur:
        cur.execute('ALTER TABLE "schedule" DISABLE TRIGGER USER;')
    dst.commit()

    print("Inserting rows...")
    try:
        with dst.cursor() as cur:
            psycopg2.extras.execute_batch(cur, insert_sql, data, page_size=500)
        dst.commit()
        print("  Inserted %d rows OK" % len(rows))
    except Exception as e:
        dst.rollback()
        print("  ERROR inserting: %s" % e)

    print("Re-enabling user triggers...")
    with dst.cursor() as cur:
        cur.execute('ALTER TABLE "schedule" ENABLE TRIGGER USER;')
    dst.commit()

    # Fix sequence
    print("Fixing sequence...")
    with dst.cursor() as cur:
        cur.execute("SELECT setval(pg_get_serial_sequence('schedule','id'), COALESCE(MAX(id),1)) FROM schedule;")
    dst.commit()

    src.close()
    dst.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
