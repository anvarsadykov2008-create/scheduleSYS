
from app.database import SessionLocal
from app.models.models import Semester

db = SessionLocal()
semesters = db.query(Semester).all()
for s in semesters:
    print(f"ID: {s.id}, Number: {s.number}, YearID: {s.academic_year_id}")
db.close()
