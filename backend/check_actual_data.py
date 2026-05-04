
from app.database import SessionLocal
from app.models.models import AcademicYear

db = SessionLocal()
years = db.query(AcademicYear).all()
for y in years:
    print(f"ID: {y.id}, Name: {y.name}, Start: {y.start_date}, End: {y.end_date}")
db.close()
