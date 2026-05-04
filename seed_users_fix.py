import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.database import SessionLocal
from app.models.models import User, UserRole
from app.auth import get_password_hash

def seed():
    db = SessionLocal()
    try:
        print("Seeding users...")
        # Admin
        admin = db.query(User).filter(User.username == "990101000001").first()
        if not admin:
            db.add(User(
                username="990101000001",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                full_name="Администратор",
                is_not_student=True
            ))
            print("Admin created.")
        else:
            admin.password_hash = get_password_hash("admin123")
            print("Admin password reset.")

        # Student
        student = db.query(User).filter(User.username == "050515000123").first()
        if not student:
            db.add(User(
                username="050515000123",
                password_hash=get_password_hash("student123"),
                role=UserRole.STUDENT,
                full_name="Иванов Иван",
                group_id=1
            ))
            print("Student created.")
        
        db.commit()
        print("Seeding complete!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
