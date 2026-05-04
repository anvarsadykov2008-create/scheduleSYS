
import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_and_import():
    db_params = {
        "host": "localhost",
        "user": "postgres",
        "password": "87474981272",
        "port": "5432"
    }
    
    new_db = "new_college"
    # Файлы находятся в корне папки scheduleSYS
    production_file = os.path.join("..", "new_college_schedule_production_schema.sql")
    auth_file = os.path.join("..", "add_auth_tables.sql")
    
    try:
        # 1. Create DB
        conn = psycopg2.connect(dbname="postgres", **db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{new_db}'")
        if cur.fetchone():
            print(f"Database {new_db} already exists. Dropping it first to ensure clean import...")
            cur.execute(f"DROP DATABASE {new_db}")
        
        print(f"Creating database {new_db}...")
        cur.execute(f"CREATE DATABASE {new_db}")
        cur.close()
        conn.close()
        
        # 2. Import Production Schema and Data
        print(f"Importing production data from {production_file}...")
        conn = psycopg2.connect(dbname=new_db, **db_params)
        cur = conn.cursor()
        
        with open(production_file, 'r', encoding='utf-8') as f:
            prod_content = f.read()
            cur.execute(prod_content)
        
        # 3. Import Auth Tables
        print(f"Importing auth tables from {auth_file}...")
        with open(auth_file, 'r', encoding='utf-8') as f:
            auth_content = f.read()
            cur.execute(auth_content)
            
        conn.commit()
        print("Import completed successfully!")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    create_and_import()
