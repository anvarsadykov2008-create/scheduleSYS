import sys
from app.database import SessionLocal
from app.models.models import Curriculum, AcademicPeriod, TimeSlot, Room, TeacherSubject

db = SessionLocal()

print("Curriculum count:", db.query(Curriculum).count())
print("AcademicPeriod count:", db.query(AcademicPeriod).count())
print("TimeSlot count:", db.query(TimeSlot).count())
print("Room count:", db.query(Room).count())
print("TeacherSubject count:", db.query(TeacherSubject).count())

periods = db.query(AcademicPeriod).all()
for p in periods:
    c = db.query(Curriculum).filter(Curriculum.academic_period_id == p.academic_period_id).count()
    print(f"Period {p.academic_period_id} ({p.name}) Curriculum Count: {c}")
