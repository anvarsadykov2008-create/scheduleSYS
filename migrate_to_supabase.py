"""
Migrates data from local PostgreSQL to Supabase.
Reads from local DB and inserts into Supabase.
"""
import psycopg2
import psycopg2.extras
import sys

LOCAL_URL = "postgresql://postgres:87474981272@localhost:5432/schedulesysss"
SUPABASE_URL = "postgresql://postgres:87076394301@db.pheiouiosqolrcbbrcdu.supabase.co:5432/postgres"

# Tables in dependency order (parents before children)
TABLES_ORDERED = [
    "departments",
    "specialties",
    "academic_periods",
    "lesson_types",
    "room_types",
    "time_slots",
    "teachers",
    "subjects",
    "groups",
    "group_subgroups",
    "rooms",
    "teacher_preferences",
    "teacher_load",
    "teacher_subjects",
    "subject_lesson_types",
    "subject_room_type",
    "teacher_unavailability",
    "group_unavailability",
    "room_unavailability",
    "group_subject_load",
    "schedule_generation_runs",
    "schedule_conflicts_log",
    "schedule",
    # auth tables
    "users",
]

def connect(url, label):
    try:
        conn = psycopg2.connect(url, connect_timeout=15)
        conn.autocommit = False
        print("  Connected to %s" % label)
        return conn
    except Exception as e:
        print("  ERROR connecting to %s: %s" % (label, e))
        sys.exit(1)

def table_exists(conn, table):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema='public' AND table_name=%s
            )
        """, (table,))
        return cur.fetchone()[0]

def get_columns(conn, table):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            ORDER BY ordinal_position
        """, (table,))
        return [row[0] for row in cur.fetchall()]

def migrate_table(src_conn, dst_conn, table):
    if not table_exists(src_conn, table):
        print("  SKIP (not in source): %s" % table)
        return 0
    if not table_exists(dst_conn, table):
        print("  SKIP (not in dest): %s" % table)
        return 0

    # Get columns that exist in BOTH source and destination
    src_cols = set(get_columns(src_conn, table))
    dst_cols = set(get_columns(dst_conn, table))
    common_cols = [c for c in get_columns(src_conn, table) if c in dst_cols]

    if not common_cols:
        print("  SKIP (no common columns): %s" % table)
        return 0

    with src_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as src_cur:
        src_cur.execute('SELECT %s FROM "%s"' % (
            ", ".join('"%s"' % c for c in common_cols), table
        ))
        rows = src_cur.fetchall()

    if not rows:
        print("  EMPTY: %s (0 rows)" % table)
        return 0

    cols_sql = ", ".join('"%s"' % c for c in common_cols)
    placeholders = ", ".join(["%s"] * len(common_cols))
    insert_sql = 'INSERT INTO "%s" (%s) VALUES (%s) ON CONFLICT DO NOTHING' % (
        table, cols_sql, placeholders
    )

    data = [tuple(row[c] for c in common_cols) for row in rows]

    with dst_conn.cursor() as dst_cur:
        psycopg2.extras.execute_batch(dst_cur, insert_sql, data, page_size=500)
    dst_conn.commit()
    print("  Migrated: %s -> %d rows" % (table, len(rows)))
    return len(rows)

def fix_sequences(dst_conn):
    """Reset sequences to max(id) so next inserts don't conflict."""
    with dst_conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='BASE TABLE';
        """)
        tables = [r[0] for r in cur.fetchall()]

    for tbl in tables:
        try:
            with dst_conn.cursor() as cur:
                cur.execute("""
                    SELECT pg_get_serial_sequence('%s', 'id');
                """ % tbl)
                seq = cur.fetchone()[0]
                if seq:
                    cur.execute("SELECT setval('%s', COALESCE(MAX(id),1)) FROM \"%s\";" % (seq, tbl))
            dst_conn.commit()
        except Exception:
            dst_conn.rollback()
    print("  Sequences reset OK")

def main():
    print("Connecting to LOCAL DB...")
    src = connect(LOCAL_URL, "local")
    print("Connecting to SUPABASE...")
    dst = connect(SUPABASE_URL, "supabase")

    total = 0
    print("\n--- Migrating tables ---")
    for table in TABLES_ORDERED:
        try:
            total += migrate_table(src, dst, table)
        except Exception as e:
            dst.rollback()
            print("  ERROR in table %s: %s" % (table, e))

    print("\n--- Fixing sequences ---")
    fix_sequences(dst)

    src.close()
    dst.close()
    print("\nMigration complete! Total rows migrated: %d" % total)

if __name__ == "__main__":
    main()
