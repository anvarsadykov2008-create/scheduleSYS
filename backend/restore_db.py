import psycopg2
from app.seed import seed
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

def kill_connections():
    print("Killing connections to 'schedulesys'...")
    try:
        # Connect to 'postgres' database to manage connections
        conn = psycopg2.connect("postgresql://postgres:raim100100@localhost:5432/postgres")
        conn.autocommit = True
        cur = conn.cursor()
        
        # Terminate all connections to schedulesys except this one (which is to postgres anyway)
        cur.execute("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = 'schedulesys' 
            AND pid <> pg_backend_pid();
        """)
        
        print("Killed all active connections.")
        conn.close()
    except Exception as e:
        print(f"Error killing connections: {e}")

if __name__ == "__main__":
    print("Starting Database Restoration...")
    kill_connections()
    print("Running seed process (Drop All -> Create All -> Insert Data)...")
    try:
        seed()
        print("\nSUCCESS: Database restored and seeded with teachers!")
    except Exception as e:
        print(f"\nERROR during seed: {e}")
