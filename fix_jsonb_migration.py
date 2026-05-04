"""
Fixes migration for tables with JSONB columns:
- schedule_generation_runs
- schedule_conflicts_log
- schedule (depends on generation_runs)
"""
import psycopg2
import psycopg2.extras
import json
import sys

LOCAL_URL = "postgresql://postgres:87474981272@localhost:5432/schedulesysss"
SUPABASE_URL = "postgresql://postgres:87076394301@db.pheiouiosqolrcbbrcdu.supabase.co:5432/postgres"

TABLES = [
    "schedule_generation_runs",
    "schedule_conflicts_log",
    "schedule",
]

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
    """Convert Python dict/list to JSON string for JSONB columns."""
    if dtype == 'jsonb' or dtype == 'json':
        if isinstance(val, (dict, list)):
            return psycopg2.extras.Json(val)
    return val

def migrate_table_jsonb(src_conn, dst_conn, table):
    src_col_info = get_columns(src_conn, table)
    dst_col_info = get_columns(dst_conn, table)
    dst_col_names = {c[0] for c in dst_col_info}
    dst_col_types = {c[0]: c[1] for c in dst_col_info}

    common = [(c, t) for c, t in src_col_info if c in dst_col_names]
    col_names = [c for c, _ in common]

    with src_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute('SELECT %s FROM "%s"' % (
            ", ".join('"%s"' % c for c in col_names), table
        ))
        rows = cur.fetchall()

    if not rows:
        print("  EMPTY: %s" % table)
        return 0

    cols_sql = ", ".join('"%s"' % c for c in col_names)
    placeholders = ", ".join(["%s"] * len(col_names))
    insert_sql = 'INSERT INTO "%s" (%s) VALUES (%s) ON CONFLICT DO NOTHING' % (
        table, cols_sql, placeholders
    )

    data = []
    for row in rows:
        serialized = tuple(
            serialize_value(row[c], dst_col_types.get(c, ''))
            for c in col_names
        )
        data.append(serialized)

    with dst_conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, insert_sql, data, page_size=200)
    dst_conn.commit()
    print("  Migrated: %s -> %d rows" % (table, len(rows)))
    return len(rows)

def fix_sequences(dst_conn):
    with dst_conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='BASE TABLE';
        """)
        tables = [r[0] for r in cur.fetchall()]
    for tbl in tables:
        try:
            with dst_conn.cursor() as cur:
                cur.execute("SELECT pg_get_serial_sequence('%s', 'id');" % tbl)
                seq = cur.fetchone()[0]
                if seq:
                    cur.execute("SELECT setval('%s', COALESCE(MAX(id),1)) FROM \"%s\";" % (seq, tbl))
            dst_conn.commit()
        except Exception:
            dst_conn.rollback()
    print("  Sequences reset OK")

def main():
    print("Connecting...")
    src = connect(LOCAL_URL, "local")
    dst = connect(SUPABASE_URL, "supabase")

    # Clear these tables first to avoid FK issues
    print("\nCleaning target tables...")
    with dst.cursor() as cur:
        cur.execute('DELETE FROM "schedule";')
        cur.execute('DELETE FROM "schedule_conflicts_log";')
        cur.execute('DELETE FROM "schedule_generation_runs";')
    dst.commit()
    print("  Cleaned OK")

    total = 0
    print("\n--- Migrating JSONB tables ---")
    for table in TABLES:
        try:
            total += migrate_table_jsonb(src, dst, table)
        except Exception as e:
            dst.rollback()
            print("  ERROR in %s: %s" % (table, e))

    print("\n--- Fixing sequences ---")
    fix_sequences(dst)

    src.close()
    dst.close()
    print("\nDone! Rows migrated: %d" % total)

if __name__ == "__main__":
    main()
