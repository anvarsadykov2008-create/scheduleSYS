
import os
import sys
# Add backend to path for imports
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine, Base
from app.models.models import User, UserRole
from app.auth import get_password_hash
from sqlalchemy import text

def restore_auth_and_admin():
    print("--- Verifying Database Schema ---")
    try:
        # Create all tables defined in SQLAlchemy models if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Schema verified (tables created if missing).")
    except Exception as e:
        print(f"Error creating schema: {e}")
        return

    print("\n--- Seeding Admin User ---")
    db = SessionLocal()
    try:
        username = "990101000001"
        password = "admin123"
        admin = db.query(User).filter(User.username == username).first()
        
        if admin:
            print(f"Found existing admin: {admin.username}. Updating password to {password}...")
            admin.password_hash = get_password_hash(password)
            db.commit()
            print("Password updated successfully!")
        else:
            print(f"Admin user {username} not found! Creating one...")
            admin = User(
                username=username,
                password_hash=get_password_hash(password),
                role=UserRole.ADMIN,
                full_name="Администратор",
            )
            db.add(admin)
            db.commit()
            print("Admin user created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during admin seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    restore_auth_and_admin()
