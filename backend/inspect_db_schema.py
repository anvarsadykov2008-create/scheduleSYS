
import psycopg2

def inspect_tables():
    db_params = {
        "host": "localhost",
        "user": "postgres",
        "password": "87474981272",
        "port": "5432",
        "dbname": "new_college"
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        tables = ['groups', 'subjects', 'teachers', 'classrooms']
        for table in tables:
            print(f"\n--- Columns in {table} ---")
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            for row in cur.fetchall():
                print(f" {row[0]} ({row[1]})")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_tables()
