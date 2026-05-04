"""Полная проверка базы данных после seed."""
from app.database import SessionLocal
from app.models.models import *

db = SessionLocal()

print("=" * 60)
print("  ПОЛНАЯ ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 60)

# 1. Отделения
depts = db.query(Department).all()
print(f"\n✅ ОТДЕЛЕНИЯ: {len(depts)}")
for d in depts:
    gc = db.query(Group).filter(Group.department_id == d.id).count()
    print(f"   {d.id}. {d.name} — {gc} групп")

# 2. Преподаватели
teachers = db.query(Teacher).all()
print(f"\n✅ ПРЕПОДАВАТЕЛИ: {len(teachers)}")
staff = sum(1 for t in teachers if t.employment_type == EmploymentType.STAFF)
print(f"   Штатных: {staff}")
vac = [t for t in teachers if t.full_name == "Вакансия"]
print(f"   Вакансий: {len(vac)}")

# 3. Аудитории
classrooms = db.query(Classroom).all()
print(f"\n✅ АУДИТОРИИ: {len(classrooms)}")
by_type = {}
for c in classrooms:
    by_type.setdefault(str(c.type.value), []).append(c.name)
for t, names in by_type.items():
    print(f"   {t}: {len(names)} — [{', '.join(names[:5])}{'...' if len(names) > 5 else ''}]")

# 4. Группы
groups = db.query(Group).all()
print(f"\n✅ ГРУППЫ: {len(groups)}")
by_course = {}
for g in groups:
    by_course.setdefault(g.course, []).append(g.name)
for course in sorted(by_course):
    print(f"   {course} курс: {len(by_course[course])} групп — {', '.join(by_course[course])}")

# 5. Подгруппы
subgroups = db.query(Subgroup).all()
print(f"\n✅ ПОДГРУППЫ: {len(subgroups)}")

# 6. Предметы
subjects = db.query(Subject).all()
print(f"\n✅ ПРЕДМЕТЫ: {len(subjects)}")

# 7. Временные слоты
slots = db.query(TimeSlot).all()
print(f"\n✅ ВРЕМЕННЫЕ СЛОТЫ: {len(slots)}")
for s in slots:
    print(f"   Пара {s.number}: {s.start_time} — {s.end_time}")

# 8. Учебный год и семестры
years = db.query(AcademicYear).all()
sems = db.query(Semester).all()
print(f"\n✅ УЧЕБНЫЕ ГОДЫ: {len(years)}")
for y in years:
    print(f"   {y.name}: {y.start_date} — {y.end_date}")
print(f"✅ СЕМЕСТРЫ: {len(sems)}")
for s in sems:
    print(f"   Семестр {s.number}: {s.start_date} — {s.end_date}")

# 9. Сетка часов
hg = db.query(HourGrid).all()
print(f"\n✅ СЕТКА ЧАСОВ (hour_grids): {len(hg)}")
by_sem = {}
by_lt = {}
for h in hg:
    by_sem.setdefault(h.semester_id, 0)
    by_sem[h.semester_id] += 1
    by_lt.setdefault(str(h.lesson_type.value), 0)
    by_lt[str(h.lesson_type.value)] += 1
for sid, cnt in by_sem.items():
    print(f"   Семестр {sid}: {cnt} записей")
for lt, cnt in by_lt.items():
    print(f"   Тип '{lt}': {cnt}")

# С делением на подгруппы
with_sub = [h for h in hg if h.subgroup_hours]
print(f"   С делением на подгруппы: {with_sub.__len__()}")

# 10. Назначения преподавателей
ts = db.query(TeacherSubject).all()
print(f"\n✅ НАЗНАЧЕНИЯ ПРЕПОДАВАТЕЛЕЙ (teacher_subjects): {len(ts)}")
# Сколько уникальных преподавателей задействовано
unique_teachers = set(t.teacher_id for t in ts)
print(f"   Уникальных преподавателей: {len(unique_teachers)}")
unique_groups = set(t.group_id for t in ts)
print(f"   Уникальных групп: {len(unique_groups)}")

# 11. Закрепления аудиторий
ca = db.query(ClassroomAssignment).all()
print(f"\n✅ ЗАКРЕПЛЕНИЯ АУДИТОРИЙ (classroom_assignments): {len(ca)}")
for a in ca:
    cr = db.query(Classroom).get(a.classroom_id)
    t = db.query(Teacher).get(a.teacher_id)
    print(f"   Каб. {cr.name} → {t.full_name}")

# 12. Версии расписания
versions = db.query(ScheduleVersion).all()
print(f"\n✅ ВЕРСИИ РАСПИСАНИЯ: {len(versions)}")

# 13. Записи расписания
entries = db.query(ScheduleEntry).count()
print(f"✅ ЗАПИСИ РАСПИСАНИЯ (schedule_entries): {entries}")

# 14. Проверки целостности
print("\n" + "=" * 60)
print("  ПРОВЕРКИ ЦЕЛОСТНОСТИ")
print("=" * 60)

# Группы без нагрузки
groups_with_hg = set(h.group_id for h in hg)
groups_without = [g for g in groups if g.id not in groups_with_hg]
if groups_without:
    print(f"\n⚠️  Группы БЕЗ сетки часов ({len(groups_without)}):")
    for g in groups_without:
        print(f"   - {g.name}")
else:
    print("\n✅ Все группы имеют сетку часов")

# Сетка часов без назначения преподавателя
ts_pairs = set((t.subject_id, t.group_id) for t in ts)
hg_without_teacher = []
for h in hg:
    if (h.subject_id, h.group_id) not in ts_pairs:
        g = db.query(Group).get(h.group_id)
        s = db.query(Subject).get(h.subject_id)
        hg_without_teacher.append((g.name, s.name))
if hg_without_teacher:
    print(f"\n⚠️  Записи сетки часов БЕЗ преподавателя ({len(hg_without_teacher)}):")
    for gn, sn in hg_without_teacher:
        print(f"   - {gn}: {sn}")
else:
    print("✅ Все записи сетки часов имеют назначенного преподавателя")

print("\n" + "=" * 60)
print("  ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 60)

db.close()
