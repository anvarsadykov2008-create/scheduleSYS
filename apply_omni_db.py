# -*- coding: utf-8 -*-
"""
Применяет новую БД из omni/Обновленная главная бдшка.sql
"""

import psycopg2
import os
import sys

# Устанавливаем кодировку вывода
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "schedulesys",
    "user": "postgres",
    "password": "raim100100",
}

SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "омни", "Обновленная главная бдшка.sql")

USERS_SQL = """
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS app_settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS userrole CASCADE;

CREATE TYPE userrole AS ENUM ('ADMIN', 'DISPATCHER', 'TEACHER', 'STUDENT', 'MANAGEMENT');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'STUDENT',
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    full_name VARCHAR(200),
    is_not_student BOOLEAN DEFAULT FALSE
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE app_settings (
    key VARCHAR(50) PRIMARY KEY,
    value VARCHAR(255),
    description VARCHAR(200)
);
"""

ADMIN_SQL = """
INSERT INTO users (username, password_hash, role, full_name)
VALUES (
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'ADMIN',
    'Администратор'
)
ON CONFLICT (username) DO NOTHING;
"""


def split_sql(sql_text):
    """Разбивает SQL на отдельные команды, учитывая блоки $$ ... $$"""
    statements = []
    current = []
    in_dollar_quote = False

    for line in sql_text.splitlines():
        stripped = line.strip()

        # Считаем $$ в строке
        dollar_count = stripped.count('$$')
        if dollar_count % 2 != 0:
            in_dollar_quote = not in_dollar_quote

        current.append(line)

        if not in_dollar_quote and stripped.endswith(';'):
            stmt = '\n'.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []

    if current:
        stmt = '\n'.join(current).strip()
        if stmt:
            statements.append(stmt)

    return statements


def apply_sql_block(conn, sql_text, label="", stop_on_error=False):
    """Применяет SQL блок. Возвращает (success_count, error_count)."""
    statements = split_sql(sql_text)
    success = 0
    errors = 0

    for i, stmt in enumerate(statements):
        if not stmt.strip():
            continue

        # Краткое описание команды
        first_line = stmt.strip().split('\n')[0][:70]

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(stmt)
            success += 1
        except Exception as e:
            err = str(e).strip().replace('\n', ' ')
            
            # Пропускаемые ошибки
            skip_keywords = ["already exists", "duplicate", "relation", "does not exist"]
            should_skip = any(k in err.lower() for k in skip_keywords)
            
            if should_skip:
                print(f"  [пропуск #{i}] {err[:100]}")
            else:
                print(f"  [ошибка #{i}] {first_line}")
                print(f"    => {err[:150]}")
            errors += 1

            if stop_on_error:
                raise

    return success, errors


def main():
    print(f"Подключение: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    if not os.path.exists(SQL_FILE):
        print(f"ОШИБКА: Файл не найден: {SQL_FILE}")
        sys.exit(1)

    print(f"\nSQL файл: {SQL_FILE}")
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        main_sql = f.read()
    print(f"Размер: {len(main_sql)} байт, строк: {main_sql.count(chr(10))}")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True  # каждая команда — своя транзакция

    print("\n[1/3] Применяем схему из омни (пошагово)...")
    s, e = apply_sql_block(conn, main_sql, label="main")
    print(f"  Итого: {s} успешно, {e} ошибок")

    print("\n[2/3] Создаём таблицы users/audit_logs/app_settings...")
    s, e = apply_sql_block(conn, USERS_SQL, label="auth")
    print(f"  Итого: {s} успешно, {e} ошибок")

    print("\n[3/3] Создаём admin-пользователя...")
    s, e = apply_sql_block(conn, ADMIN_SQL, label="admin")
    print(f"  Итого: {s} успешно, {e} ошибок")

    print("\n--- Статистика таблиц ---")
    tables = [
        "days_of_week", "time_slots", "subjects", "teachers",
        "teacher_subjects", "courses", "groups", "classrooms",
        "curriculum", "schedule", "users"
    ]
    with conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count} строк")
            except Exception as e:
                print(f"  {table}: ошибка - {str(e).strip()[:60]}")

    conn.close()
    print("\nГотово! БД обновлена.")


if __name__ == "__main__":
    main()
