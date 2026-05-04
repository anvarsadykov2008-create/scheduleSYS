"""
Verify Supabase DB has all expected data.
"""
import psycopg2
import psycopg2.extras
import sys

SUPABASE_URL = "postgresql://postgres:87076394301@db.pheiouiosqolrcbbrcdu.supabase.co:5432/postgres"

TABLES = [
    "departments", "specialties", "academic_periods", "lesson_types",
    "room_types", "time_slots", "teachers", "subjects", "groups",
    "rooms", "teacher_subjects", "subject_lesson_types", "group_subject_load",
    "schedule_generation_runs", "schedule_conflicts_log", "schedule", "users",
]

conn = psycopg2.connect(SUPABASE_URL, connect_timeout=15)
print("Connected to Supabase!\n")
print("%-35s %s" % ("TABLE", "ROWS"))
print("-" * 45)
for tbl in TABLES:
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM "%s"' % tbl)
            count = cur.fetchone()[0]
        print("%-35s %d" % (tbl, count))
    except Exception as e:
        print("%-35s ERROR: %s" % (tbl, e))
conn.close()
