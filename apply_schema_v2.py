"""
apply_schema_v2.py
Полностью пересоздаёт БД new_college:
1. Дропает всё с CASCADE
2. Применяет production schema
3. Создаёт auth-таблицы
4. Создаёт admin-пользователя
"""
import psycopg2
import os
import sys

DB_URL = "postgresql://postgres:87474981272@localhost:5432/new_college"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "new_college_schedule_production_schema.sql")

# ----------------------------------------------------------------
# Полный сброс всех объектов в public schema
# ----------------------------------------------------------------
DROP_ALL_SQL = """
DO $$ DECLARE
    r RECORD;
BEGIN
    -- drop all tables with CASCADE
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;

    -- drop all sequences
    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS public.' || quote_ident(r.sequence_name) || ' CASCADE';
    END LOOP;

    -- drop all views
    FOR r IN (SELECT table_name FROM information_schema.views WHERE table_schema = 'public') LOOP
        EXECUTE 'DROP VIEW IF EXISTS public.' || quote_ident(r.table_name) || ' CASCADE';
    END LOOP;

    -- drop all functions
    FOR r IN (SELECT routine_name, specific_name FROM information_schema.routines WHERE routine_schema = 'public') LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS public.' || quote_ident(r.routine_name) || ' CASCADE';
    END LOOP;

    -- drop all types
    FOR r IN (SELECT typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE n.nspname = 'public' AND t.typtype = 'e') LOOP
        EXECUTE 'DROP TYPE IF EXISTS public.' || quote_ident(r.typname) || ' CASCADE';
    END LOOP;
END $$;
"""

AUTH_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'STUDENT',
    teacher_id BIGINT REFERENCES teachers(teacher_id) ON DELETE SET NULL,
    group_id BIGINT REFERENCES groups(group_id) ON DELETE SET NULL,
    full_name VARCHAR(200),
    is_not_student BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(50) PRIMARY KEY,
    value VARCHAR(255),
    description VARCHAR(200)
);

-- Создаём пользователя admin (пароль: admin123)
INSERT INTO users (username, password_hash, role, full_name, is_not_student)
VALUES (
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'ADMIN',
    'Администратор',
    TRUE
)
ON CONFLICT (username) DO UPDATE
    SET password_hash = EXCLUDED.password_hash,
        role = EXCLUDED.role,
        full_name = EXCLUDED.full_name,
        is_not_student = EXCLUDED.is_not_student;
"""

def run():
    print("=" * 60)
    print("  Полное пересоздание БД new_college")
    print("=" * 60)

    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True   # autocommit for DDL operations
        cur = conn.cursor()
        print("[OK] Подключение к БД установлено")
    except Exception as e:
        print(f"[ERROR] Не удалось подключиться: {e}")
        sys.exit(1)

    # Step 1: Drop everything
    print("\n[1/4] Удаляю все объекты в public schema...")
    try:
        cur.execute(DROP_ALL_SQL)
        print("[OK] Все таблицы, функции и типы удалены")
    except Exception as e:
        print(f"[ERROR] Drop all: {e}")
        sys.exit(1)

    # Step 2: Apply production schema (it uses BEGIN/COMMIT internally)
    print(f"\n[2/4] Читаю production schema...")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print("[2/4] Применяю production schema (60+ таблиц, данные, триггеры)...")
    try:
        cur.execute(schema_sql)
        print("[OK] Production schema применена!")
    except Exception as e:
        print(f"[ERROR] Schema error: {e}")
        sys.exit(1)

    # Step 3: Apply auth tables
    print("\n[3/4] Создаю auth-таблицы и пользователя admin...")
    try:
        cur.execute(AUTH_SQL)
        print("[OK] users, audit_logs, app_settings созданы")
        print("[OK] Пользователь admin создан (пароль: admin123)")
    except Exception as e:
        print(f"[ERROR] Auth: {e}")

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("  ИТОГ — строк в ключевых таблицах:")
    print("=" * 60)
    checks = [
        ("departments",         "SELECT COUNT(*) FROM departments"),
        ("specialties",         "SELECT COUNT(*) FROM specialties"),
        ("academic_periods",    "SELECT COUNT(*) FROM academic_periods"),
        ("teachers",            "SELECT COUNT(*) FROM teachers"),
        ("subjects",            "SELECT COUNT(*) FROM subjects"),
        ("groups",              "SELECT COUNT(*) FROM groups"),
        ("rooms",               "SELECT COUNT(*) FROM rooms"),
        ("time_slots",          "SELECT COUNT(*) FROM time_slots"),
        ("lesson_types",        "SELECT COUNT(*) FROM lesson_types"),
        ("room_types",          "SELECT COUNT(*) FROM room_types"),
        ("teacher_subjects",    "SELECT COUNT(*) FROM teacher_subjects"),
        ("group_subject_load",  "SELECT COUNT(*) FROM group_subject_load"),
        ("users",               "SELECT COUNT(*) FROM users"),
    ]
    for name, query in checks:
        try:
            cur.execute(query)
            count = cur.fetchone()[0]
            status = "✓" if count > 0 else "⚠"
            print(f"  {status} {name:<25} {count:>6} строк")
        except Exception as e:
            print(f"  ✗ {name:<25} ERROR: {e}")

    cur.close()
    conn.close()
    print("\n[ГОТОВО] База данных new_college полностью настроена!")
    print("  Логин: admin")
    print("  Пароль: admin123")

if __name__ == "__main__":
    run()
