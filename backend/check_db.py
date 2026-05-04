import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Try default postgres/postgres first, then read from .env
try:
    from app.config import settings
    DATABASE_URL = settings.database_url
except Exception as e:
    print(f"Failed to load config: {e}")
    DATABASE_URL = "postgresql://postgres:87474981272@localhost:5432/raspis"

def check_connection():
    print(f"Testing connection to: {DATABASE_URL}")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"Successfully connected to database at {DATABASE_URL}!")
            return True
    except OperationalError as e:
        print(f"Connection failed: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    if check_connection():
        sys.exit(0)
    else:
        sys.exit(1)
