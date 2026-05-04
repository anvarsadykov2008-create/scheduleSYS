import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.database import SessionLocal
from app.models import models
from app.auth import verify_password, get_password_hash

def check_db():
    db = SessionLocal()
    try:
        target_username = '990101000001'
        print(f"Checking user: {target_username}")
        user = db.query(models.User).filter(models.User.username == target_username).first()
        
        if user:
            print(f"Found: {user.username}, Role: {getattr(user, 'role', 'Unknown')}")
                
            valid = verify_password('admin123', user.password_hash)
            print(f"Password 'admin123' valid? {valid}")
            
            if not valid:
                print(f"Stored hash: {user.password_hash}")
                print(f"New hash for 'admin123': {get_password_hash('admin123')}")
                
                # Update password
                print("Updating password to 'admin123'...")
                user.password_hash = get_password_hash('admin123')
                db.commit()
                print("Password successfully updated! Try logging in now.")
        else:
            print(f"User {target_username} NOT FOUND in database.")
            users = db.query(models.User).limit(10).all()
            print("\nHere are some users that DO exist in the DB:")
            for u in users:
                print(f"- {u.username}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
