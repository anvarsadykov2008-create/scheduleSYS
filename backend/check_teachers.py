from app.database import SessionLocal
from app.models.models import Teacher, TeacherSubject, HourGrid, Subject

db = SessionLocal()

teachers_to_check = ["Рахан", "Юнусова"]

print("📊 Проверка нагрузки преподавателей:")

for t_name in teachers_to_check:
    teacher = db.query(Teacher).filter(Teacher.full_name.like(f"%{t_name}%")).first()
    if not teacher:
        print(f"❌ {t_name} не найден")
        continue

    print(f"\n👤 {teacher.full_name}")
    
    assignments = db.query(TeacherSubject).filter(TeacherSubject.teacher_id == teacher.id).all()
    total_pairs = 0
    
    print(f"   Назначенные группы:")
    for ts in assignments:
        s = db.query(Subject).get(ts.subject_id)
        hg = db.query(HourGrid).filter(
            HourGrid.subject_id == ts.subject_id, 
            HourGrid.group_id == ts.group_id
        ).first()
        
        hours = hg.total_hours if hg else 0
        pairs = hours // 2
        total_pairs += pairs
        
        print(f"   - {ts.group.name}: {s.name[:40]}... ({pairs} пар)")

    print(f"   Σ ИТОГО: {total_pairs} пар (макс 35 в неделю)")
    if total_pairs > 35:
        print(f"   ⚠️  ПЕРЕГРУЗКА! ({total_pairs} > 35)")

db.close()
