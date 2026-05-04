from sqlalchemy import text
import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())
# Also add backend to path if running from root
if os.path.exists("backend"):
    sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.database import engine

def migrate():
    print("Connecting to database...")
    with engine.connect() as conn:
        try:
            # Check if column exists
            # Postgres specific check, or just try-catch
            conn.execute(text("ALTER TABLE teachers ADD COLUMN department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL"))
            conn.commit()
            print("Successfully added department_id to teachers table.")
        except Exception as e:
            if "duplicate column" in str(e) or "already exists" in str(e):
                print("Column department_id already exists (or other error).")
                print(e)
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
