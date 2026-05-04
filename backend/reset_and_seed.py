import psycopg2
import os
import sys
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

db_params = {
    "host": "localhost",
    "user": "postgres",
    "password": "87474981272",
    "port": "5432"
}

target_db = "hahihi"
schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "college_schedule_production_schema_fixed.sql")

def reset_db():
    print(f"Resetting database {target_db}...")
    conn = psycopg2.connect(dbname="postgres", **db_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    # Terminate other connections
    cur.execute(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{target_db}' AND pid <> pg_backend_pid();")
    cur.execute(f"DROP DATABASE IF EXISTS {target_db}")
    cur.execute(f"CREATE DATABASE {target_db}")
    cur.close()
    conn.close()
    print("Database reset successfully.")

def apply_schema():
    print("Applying scheme...")
    conn = psycopg2.connect(dbname=target_db, **db_params)
    cur = conn.cursor()
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("Schema applied successfully.")

if __name__ == "__main__":
    reset_db()
    apply_schema()
    print("Running seed_all()...")
    
    # Import here to avoid early engine creation before DB is recreated
    from app.database import SessionLocal
    from init_db import seed_all
    
    db = SessionLocal()
    try:
        seed_all(db)
        print("Database successfully seeded with data!")
    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        db.close()
