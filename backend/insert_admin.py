from app.database import engine, SessionLocal
from app.models.models import User, UserRole
from app.auth import get_password_hash

def insert_admin():
    db = SessionLocal()
    try:
        # Check if user with IIN 990101000001 already exists
        admin = db.query(User).filter(User.username == "990101000001").first()
        if admin:
            db.delete(admin)
            db.commit()
            print("Cleaning existing admin...")

        new_admin = User(
            username="990101000001",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            full_name="Администратор",
            is_not_student=True
        )
        db.add(new_admin)
        db.commit()
        print("Inserted admin user (IIN: 990101000001, Pass: admin123) successfully")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    insert_admin()
