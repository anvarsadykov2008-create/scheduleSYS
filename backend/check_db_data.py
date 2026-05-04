"""
Проверка данных: выводит всех преподавателей, предметы и группы из базы.
Сравни с реальными данными из notebooklm.rxt.
"""
from app.database import SessionLocal
from app.models.models import Teacher, Subject, Group

db = SessionLocal()

teachers = db.query(Teacher).order_by(Teacher.full_name).all()
subjects = db.query(Subject).order_by(Subject.name).all()
groups   = db.query(Group).order_by(Group.name).all()

print(f"\n{'='*60}")
print(f"  ПРЕПОДАВАТЕЛИ ({len(teachers)})")
print(f"{'='*60}")
for i, t in enumerate(teachers, 1):
    print(f"  {i:3}. {t.full_name:<40} [{t.employment_type}]")

print(f"\n{'='*60}")
print(f"  ПРЕДМЕТЫ ({len(subjects)})")
print(f"{'='*60}")
for i, s in enumerate(subjects, 1):
    print(f"  {i:3}. {s.name}")

print(f"\n{'='*60}")
print(f"  ГРУППЫ ({len(groups)})")
print(f"{'='*60}")
for i, g in enumerate(groups, 1):
    print(f"  {i:3}. {g.name:<20} курс={g.course}")

db.close()
