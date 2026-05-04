
import os
import sys
# Add backend to path for imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.database import SessionLocal
from app.models.models import User, UserRole

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Total users in DB: {len(users)}")
        for u in users:
            print(f"ID: {u.id}, Username: '{u.username}', Role: {u.role}, Full Name: {u.full_name}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
