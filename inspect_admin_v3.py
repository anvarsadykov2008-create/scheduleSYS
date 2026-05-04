
import os
import sys
# Add backend to path for imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.database import SessionLocal
from app.models.models import User, UserRole
from app.auth import verify_password, get_password_hash

def inspect_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "990101000001").first()
        if not user:
            print("User 990101000001 NOT FOUND in database")
            return
        
        print(f"User: {user.username}")
        print(f"Role: {user.role} (type: {type(user.role)})")
        print(f"Hash in DB: {user.password_hash}")
        
        test_pass = "admin123"
        is_valid = verify_password(test_pass, user.password_hash)
        print(f"Verify '{test_pass}'? {is_valid}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_admin()
