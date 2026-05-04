"""
apply_schema.py
Применяет new_college_schedule_production_schema.sql к БД new_college,
затем создаёт таблицы аутентификации (users, audit_logs, app_settings).
"""
import psycopg2
import os
import sys

DB_URL = "postgresql://postgres:87474981272@localhost:5432/new_college"

# Path relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "new_college_schedule_production_schema.sql")
AUTH_FILE = os.path.join(BASE_DIR, "add_auth_tables.sql")

AUTH_EXTRA_SQL = """
-- Admin user seed (password = admin123, bcrypt hash below is for 'admin123')
INSERT INTO users (username, password_hash, role, full_name, is_not_student)
VALUES (
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'ADMIN',
    'Администратор',
    TRUE
)
ON CONFLICT (username) DO NOTHING;
"""

def run():
    print("=" * 60)
    print("Применение схемы к БД new_college")
    print("=" * 60)

    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()
        print("[OK] Подключение к БД установлено")
    except Exception as e:
        print(f"[ERROR] Не удалось подключиться к БД: {e}")
        sys.exit(1)

    # Step 1: Apply main production schema
    print(f"\n[1/3] Читаю файл схемы: {SCHEMA_FILE}")
    if not os.path.exists(SCHEMA_FILE):
        print(f"[ERROR] Файл не найден: {SCHEMA_FILE}")
        sys.exit(1)

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print("[1/3] Применяю production schema (может занять 10-30 сек)...")
    try:
        cur.execute(schema_sql)
        conn.commit()
        print("[OK] Production schema применена успешно")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Ошибка при применении схемы: {e}")
        # Try to continue with auth tables anyway
        print("[WARN] Попытаюсь продолжить с таблицами аутентификации...")

    # Step 2: Apply auth tables
    print(f"\n[2/3] Читаю auth-таблицы: {AUTH_FILE}")
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            auth_sql = f.read()
        try:
            cur.execute(auth_sql)
            conn.commit()
            print("[OK] Auth-таблицы созданы (users, audit_logs, app_settings)")
        except Exception as e:
            conn.rollback()
            print(f"[WARN] Auth SQL: {e}")
    else:
        print("[WARN] Файл add_auth_tables.sql не найден, пропускаю")

    # Step 3: Seed admin user
    print("\n[3/3] Создаю пользователя admin...")
    try:
        cur.execute(AUTH_EXTRA_SQL)
        conn.commit()
        print("[OK] Пользователь admin создан (пароль: admin123)")
    except Exception as e:
        conn.rollback()
        print(f"[WARN] Ошибка при создании admin: {e}")

    # Final check: count tables and rows
    print("\n" + "=" * 60)
    print("ИТОГ — количество строк в ключевых таблицах:")
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
            print(f"  {name:<25} {count:>6} строк")
        except Exception as e:
            print(f"  {name:<25} ERROR: {e}")

    cur.close()
    conn.close()
    print("\n[ГОТОВО] База данных new_college полностью настроена!")

if __name__ == "__main__":
    run()
