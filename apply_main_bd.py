import psycopg2
import os

DB_URL = "postgresql://postgres:raim100100@localhost:5432/schedulesys"
SCHEMA_FILE = "MAIN.sql"
AUTH_FILE = "add_auth_tables.sql"
AUTH_EXTRA_SQL = """
INSERT INTO users (username, password_hash, role, full_name, is_not_student)
VALUES (
    'admin',
    '$argon2id$v=19$m=65536,t=3,p=4$sPbemxPCWCuFEELoXas1xg$9LDtGsaCu0o5urniKAyBiNXob5b13YQx7UoZLRPhIEU',
    'ADMIN',
    'Администратор',
    TRUE
)
ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash;
"""

def run():
    print(f"Подключение к базе данных 'schedulesys'...")
    try:
        conn = psycopg2.connect(DB_URL)
    except psycopg2.OperationalError as e:
        print(f"Не удалось подключиться к базе данных. Проверьте, запущен ли PostgreSQL и существует ли БД hahihi.\n{e}")
        return
        
    conn.autocommit = False
    cur = conn.cursor()
    
    # Отбрасываем зависимые таблицы, чтобы не было ошибки при удалении groups
    try:
        cur.execute("DROP TABLE IF EXISTS audit_logs, users, app_settings CASCADE;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        pass
    
    # 1. Применяем главную схему
    print(f"Применяю схему из файла {SCHEMA_FILE}...")
    try:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            cur.execute(f.read())
            conn.commit()
            print("Успешно: MAIN.sql")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при применении MAIN.sql: {e}")
        return

    # 2. Применяем схему аутентификации
    print(f"Применяю таблицы аутентификации ({AUTH_FILE})...")
    try:
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                cur.execute(f.read())
                conn.commit()
            print("Успешно: add_auth_tables.sql")

            # 3. Добавляем админа
            print("Добавляю пользователя admin (пароль: admin123)...")
            cur.execute(AUTH_EXTRA_SQL)
            conn.commit()
            print("Успешно: Пользователь admin добавлен/обновлен.")
        else:
            print(f"Файл {AUTH_FILE} не найден. Пропуск создания таблиц логина.")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании таблиц логина: {e}")

    print("Инициализация успешно завершена!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    run()
