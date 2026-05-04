import os
import sys
from datetime import date

# Add the backend directory to sys.path to allow imports from 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models.models import AcademicYear, Semester, ScheduleVersion, DayOfWeek, TimeSlot

def init_db():
    print("Applying schema changes...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Academic Year
        if not db.query(AcademicYear).filter(AcademicYear.name == "2025-2026").first():
            print("Seeding Academic Year...")
            year = AcademicYear(
                name="2025-2026",
                start_date=date(2025, 9, 1),
                end_date=date(2026, 6, 30)
            )
            db.add(year)
            db.commit()
            db.refresh(year)
        else:
            year = db.query(AcademicYear).filter(AcademicYear.name == "2025-2026").first()

        # 2. Semesters
        if not db.query(Semester).filter(Semester.academic_year_id == year.id, Semester.number == 1).first():
            print("Seeding Semester 1...")
            sem1 = Semester(
                academic_year_id=year.id,
                number=1,
                start_date=date(2025, 9, 1),
                end_date=date(2025, 12, 30)
            )
            db.add(sem1)
        
        if not db.query(Semester).filter(Semester.academic_year_id == year.id, Semester.number == 2).first():
            print("Seeding Semester 2...")
            sem2 = Semester(
                academic_year_id=year.id,
                number=2,
                start_date=date(2026, 1, 15),
                end_date=date(2026, 6, 25)
            )
            db.add(sem2)
        db.commit()

        # 3. Schedule Version (for first semester)
        sem1 = db.query(Semester).filter(Semester.academic_year_id == year.id, Semester.number == 1).first()
        if sem1 and not db.query(ScheduleVersion).filter(ScheduleVersion.semester_id == sem1.id).first():
            print("Seeding Schedule Version...")
            version = ScheduleVersion(
                semester_id=sem1.id,
                status="published",
                description="Основное расписание (начальное)"
            )
            db.add(version)
            db.commit()

        # 4. Lookup tables (DayOfWeek, TimeSlot) if empty
        if db.query(DayOfWeek).count() == 0:
            print("Seeding Days of Week...")
            days = [
                DayOfWeek(id=1, name="Понедельник"),
                DayOfWeek(id=2, name="Вторник"),
                DayOfWeek(id=3, name="Среда"),
                DayOfWeek(id=4, name="Четверг"),
                DayOfWeek(id=5, name="Пятница"),
                DayOfWeek(id=6, name="Суббота"),
            ]
            db.add_all(days)
            db.commit()

        if db.query(TimeSlot).count() == 0:
            print("Seeding Time Slots...")
            slots = [
                TimeSlot(id=1, slot_number=1, start_time=None, end_time=None),
                TimeSlot(id=2, slot_number=2, start_time=None, end_time=None),
                TimeSlot(id=3, slot_number=3, start_time=None, end_time=None),
                TimeSlot(id=4, slot_number=4, start_time=None, end_time=None),
            ]
            db.add_all(slots)
            db.commit()

        print("Database initialization completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error during initialization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
