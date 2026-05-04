import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.database import SessionLocal
from app.models.models import User
from app.auth import verify_password, create_access_token

def debug_login():
    db = SessionLocal()
    try:
        username = "990101000001"
        password = "admin123"
        print(f"Debugging login for {username}...")
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print("User not found in DB")
            return
            
        print(f"User found: {user.username}")
        print(f"Stored hash: {user.password_hash}")
        
        print("Verifying password...")
        try:
            valid = verify_password(password, user.password_hash)
            print(f"Password valid: {valid}")
        except Exception as e:
            print(f"Password verification CRASHED: {e}")
            import traceback
            traceback.print_exc()
            return

        if valid:
            print("Creating token...")
            try:
                token = create_access_token(data={"sub": user.username})
                print(f"Token created: {token[:20]}...")
            except Exception as e:
                print(f"Token creation CRASHED: {e}")
                import traceback
                traceback.print_exc()
                return
        
        print("Debug logic complete without crash.")
        
    except Exception as e:
        print(f"General CRASH: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_login()
