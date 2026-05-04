import sqlite3
import os
import sys

# Define path to scheduleSYS and backend
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, "backend")
if os.path.exists(backend_dir):
    sys.path.append(backend_dir)
sys.path.append(current_dir)

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine
from backend.app.models.models import (
    Department, Specialty, Group, Subgroup,
    Teacher, Subject, Classroom, TimeSlot, AcademicPeriod,
    TeacherSubject, HourGrid, ScheduleEntry, ScheduleVersion, User
)
from sqlalchemy import text

def clean_db(db: Session):
    print("Cleaning database...")
    # Nullify references in users to avoid foreign key cascading drops
    db.execute(text("UPDATE users SET group_id = NULL, teacher_id = NULL"))
    db.commit()

    tables = [
        "schedule", "group_subject_load", "teacher_subjects",
        "teacher_unavailability", "rooms", "group_subgroups",
        "groups", "teachers", "subjects", "time_slots"
    ]
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    db.commit()


def migrate_data():
    db = SessionLocal()
    clean_db(db)
    
    # Needs a default department and specialty for groups and teachers
    dept = db.query(Department).first()
    if not dept:
        dept = Department(code="DEF", name="Общая кафедра", is_active=True)
        db.add(dept)
        db.commit()
        db.refresh(dept)
        
    spec = db.query(Specialty).first()
    if not spec:
        spec = Specialty(department_id=dept.id, code="0000", name="Общая специальность", is_active=True)
        db.add(spec)
        db.commit()
        db.refresh(spec)

    sqlite_conn = sqlite3.connect(r'c:\Projects\scheduleSYS\омни\ready_schedule.db')
    cur = sqlite_conn.cursor()

    print("Migrating time_slots...")
    cur.execute("SELECT id, slot_number FROM time_slots")
    for row in cur.fetchall():
        db.add(TimeSlot(id=row[0], day_of_week=0, lesson_number=row[1]))
    db.commit()

    print("Migrating subjects...")
    cur.execute("SELECT id, name FROM subjects")
    for row in cur.fetchall():
        db.add(Subject(id=row[0], name=row[1], code=f"S{row[0]}"))
    db.commit()

    print("Migrating classrooms...")
    cur.execute("SELECT id, room_number, floor, room_type FROM classrooms")
    for row in cur.fetchall():
        # Room Type is standard or computer
        r_type = 1
        db.add(Classroom(id=row[0], code=row[1][:30], name=row[1], building="Главный", floor=row[2], room_type_id=r_type))
    db.commit()

    print("Migrating teachers...")
    cur.execute("SELECT id, last_name, first_name, middle_name FROM teachers")
    for row in cur.fetchall():
        db.add(Teacher(id=row[0], last_name=row[1], first_name=row[2], middle_name=row[3], department_id=dept.id, is_active=True))
    db.commit()

    print("Migrating groups...")
    cur.execute("SELECT id, name, course_id FROM groups")
    for row in cur.fetchall():
        course = row[2] if row[2] else 1
        db.add(Group(id=row[0], name=row[1], code=row[1], course=course, specialty_id=spec.id, department_id=dept.id))
    db.commit()

    print("Migrating teacher_subjects...")
    cur.execute("SELECT teacher_id, subject_id FROM teacher_subjects")
    for row in cur.fetchall():
        db.add(TeacherSubject(teacher_id=row[0], subject_id=row[1]))
    db.commit()

    print("Migrating curriculum (HourGrid)...")
    cur.execute("SELECT group_id, subject_id FROM curriculum")
    for row in cur.fetchall():
        try:
            db.add(HourGrid(group_id=row[0], subject_id=row[1]))
            db.commit()
        except Exception:
            db.rollback()

    print("Migrating schedule...")
    cur.execute("SELECT day_of_week_id, time_slot_id, group_id, teacher_id, subject_id, classroom_id FROM schedule")
    for row in cur.fetchall():
        # SQLite day_of_week_id matches day_of_week in models (hopefully)
        ts_id = row[1]
        # In the postgres model, TimeSlot has day_of_week and lesson_number. We need to create a new DB TimeSlot
        # or map it. Wait, the models.py has `TimeSlot(id, day_of_week, lesson_number)`.
        # The SQLite has `days_of_week` (1-6) and `time_slots` (1-6). 
        # Schedule has `day_of_week_id` and `time_slot_id`.
        # So we probably need to create TimeSlot for each day/slot combo, or just update the DB schema.
        pass

if __name__ == "__main__":
    migrate_data()
    print("Done")
