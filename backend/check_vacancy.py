from app.database import SessionLocal
from app.models.models import Teacher, TeacherSubject, HourGrid

db = SessionLocal()

# 1. Находим Вакансию
vac = db.query(Teacher).filter(Teacher.full_name.like("%Вакансия%")).first()
if not vac:
    print("❌ Преподаватель 'Вакансия' не найден!")
else:
    print(f"✅ Преподаватель: {vac.full_name} (id={vac.id})")

    # 2. Считаем нагрузку
    # Находим все назначения
    ts_assignments = db.query(TeacherSubject).filter(TeacherSubject.teacher_id == vac.id).all()
    print(f"📌 Назначено предметов: {len(ts_assignments)}")

    total_hours = 0
    total_pairs = 0
    
    for ts in ts_assignments:
        # Находим часы для этого назначения
        hg = db.query(HourGrid).filter(
            HourGrid.subject_id == ts.subject_id,
            HourGrid.group_id == ts.group_id
        ).all()
        for h in hg:
            total_hours += h.total_hours
            total_pairs += h.total_hours // 2

    print(f"📊 Общая нагрузка на 'Вакансия':")
    print(f"   Часов: {total_hours}")
    print(f"   Пар: {total_pairs}")
    
    max_slots = 7 * 5 # 35 слотов в неделю
    print(f"\n📉 Доступно слотов в неделю: {max_slots}")
    if total_pairs > max_slots:
        print(f"⚠️  ПЕРЕГРУЗКА! Требуется {total_pairs} слотов, а есть только {max_slots}.")
        print("   Нужно сделать 'Вакансия' бесконечным ресурсом.")
    else:
        print("   Нагрузка в пределах нормы (но могут быть коллизии).")

db.close()
