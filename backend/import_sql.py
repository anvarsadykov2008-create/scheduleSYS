"""
Импорт данных из обновлённого SQL-файла в базу scheduleSYS.
Парсит SQL, маппит на существующие SQLAlchemy-модели.
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, time
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.models import (
    Department, AcademicYear, Semester, Group, Teacher,
    Subject, Classroom, TimeSlot, ClassroomType, EmploymentType,
    LessonType, HourGrid, TeacherSubject, ClassroomAssignment,
    User, UserRole,
)
from app.auth import get_password_hash


SQL_FILE = os.path.join(os.path.dirname(__file__), "..", "Обновленная главная бдшка.sql")


def parse_teachers(sql_text):
    """Парсит INSERT INTO teachers ..."""
    pattern = r"INSERT INTO teachers \(last_name, first_name, middle_name, subjects\)\s*VALUES\s*(.*?);"
    m = re.search(pattern, sql_text, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    rows = re.findall(r"\(([^)]+)\)", block)
    teachers = []
    for row in rows:
        parts = [p.strip().strip("'") for p in row.split(",", 3)]
        last = parts[0]
        first = parts[1]
        middle = parts[2] if parts[2] != "NULL" else ""
        full = f"{last} {first}" + (f" {middle}" if middle else "")
        teachers.append(full.strip())
    return teachers


def parse_groups(sql_text):
    """Парсит INSERT INTO groups ..."""
    pattern = r"INSERT INTO groups \(name, course_id\)\s*VALUES\s*(.*?);"
    m = re.search(pattern, sql_text, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    rows = re.findall(r"\('([^']+)',\s*(\d+)\)", block)
    # Добавляем пробел перед цифрой курса если его нет: "БД 1-1" vs "БД1-1"
    groups = []
    for name, course in rows:
        # Нормализуем: "БУХ 1-1" или "БУХ1-1" → "БУХ 1-1"
        normalized = re.sub(r'([А-Яа-яЁёA-Za-z])(\d)', r'\1 \2', name)
        groups.append((normalized, int(course)))
    return groups


def parse_classrooms(sql_text):
    """Парсит INSERT INTO classrooms ..."""
    pattern = r"INSERT INTO classrooms \(room_number, floor, room_type\) VALUES\s*(.*?);"
    m = re.search(pattern, sql_text, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    rows = re.findall(r"\('([^']+)',\s*(\d+),\s*'([^']+)'\)", block)
    result = []
    for room, floor, rtype in rows:
        # Извлекаем номер из "101 кабинет" → "101"
        num = room.replace(" кабинет", "").strip()
        ct = ClassroomType.COMPUTER if rtype == "Компьютерный" else ClassroomType.REGULAR
        result.append((num, int(floor), ct))
    return result


def parse_subjects(sql_text):
    """Парсит INSERT INTO subjects ..."""
    pattern = r"INSERT INTO subjects \(name\) VALUES\s*(.*?);"
    m = re.search(pattern, sql_text, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    names = re.findall(r"\('([^']+)'\)", block)
    # Убираем дубли
    seen = set()
    result = []
    for n in names:
        n = n.strip()
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


def parse_curriculum(sql_text):
    """Парсит INSERT INTO curriculum ..."""
    pattern = r"INSERT INTO curriculum \(group_id, subject_id, theory_hours, practice_hours, semester\)\s*VALUES\s*(.*?);"
    m = re.search(pattern, sql_text, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    # Каждая запись — (SELECT ... , SELECT ..., hours, hours, sem)
    entries = re.findall(
        r"\(\s*\(SELECT id FROM groups WHERE name='([^']+)'\),\s*"
        r"\(SELECT id FROM subjects WHERE name='([^']+?)'\s*\),\s*"
        r"(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
        block
    )
    result = []
    for grp, subj, theory, practice, sem in entries:
        grp_norm = re.sub(r'([А-Яа-яЁёA-Za-z])(\d)', r'\1 \2', grp.strip())
        result.append((grp_norm, subj.strip(), int(theory), int(practice), int(sem)))
    return result


def run_import():
    print("Читаю SQL файл...")
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_text = f.read()

    teachers_data = parse_teachers(sql_text)
    groups_data = parse_groups(sql_text)
    classrooms_data = parse_classrooms(sql_text)
    subjects_data = parse_subjects(sql_text)
    curriculum_data = parse_curriculum(sql_text)

    print(f"  Преподаватели: {len(teachers_data)}")
    print(f"  Группы: {len(groups_data)}")
    print(f"  Аудитории: {len(classrooms_data)}")
    print(f"  Предметы: {len(subjects_data)}")
    print(f"  Учебный план: {len(curriculum_data)}")

    print("\nПересоздаю таблицы...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # 1. Departments
        dept_it = Department(name="Отделение информационных технологий")
        dept_tech = Department(name="Технологическое отделение")
        dept_acc = Department(name="Отделение учета и аудита")
        db.add_all([dept_it, dept_tech, dept_acc])
        db.flush()

        prefix_to_dept = {
            "WEB": dept_it, "РПО": dept_it, "ИС": dept_it,
            "БД": dept_acc, "БУХ": dept_acc,
            "ОП": dept_tech, "ТП": dept_tech, "ТК": dept_tech, "ТХ": dept_tech,
        }

        # 2. Teachers
        vacancy = Teacher(full_name="Вакансия", employment_type=EmploymentType.STAFF, max_hours_per_week=None)
        db.add(vacancy)
        db.flush()
        teacher_map = {"Вакансия": vacancy}

        for name in teachers_data:
            t = Teacher(full_name=name, employment_type=EmploymentType.STAFF, max_hours_per_week=36)
            db.add(t)
            db.flush()
            teacher_map[name] = t
        print(f"  + {len(teacher_map)} преподавателей")

        # 3. Classrooms from SQL + extras
        classroom_map = {}
        for num, floor, ct in classrooms_data:
            c = Classroom(name=num, type=ct, capacity=30)
            db.add(c)
            db.flush()
            classroom_map[num] = c

        # Добавляем спортзал и лаборатории
        for extra_name, extra_type, extra_cap in [
            ("Спортзал", ClassroomType.GYM, 60),
            ("Лаб. 1", ClassroomType.LABORATORY, 15),
            ("Лаб. 2", ClassroomType.LABORATORY, 15),
            ("Лаб. 3", ClassroomType.LABORATORY, 15),
            ("Лаб. 4", ClassroomType.LABORATORY, 15),
        ]:
            c = Classroom(name=extra_name, type=extra_type, capacity=extra_cap)
            db.add(c)
            db.flush()
            classroom_map[extra_name] = c
        print(f"  + {len(classroom_map)} аудиторий")

        # 4. Groups
        group_map = {}
        for name, course in groups_data:
            prefix = name.split()[0]
            dept = prefix_to_dept.get(prefix, dept_it)
            g = Group(name=name, course=course, department_id=dept.id, student_count=25)
            db.add(g)
            db.flush()
            group_map[name] = g
        print(f"  + {len(group_map)} групп")

        # 5. Academic year & semesters
        ay = AcademicYear(name="2025-2026", start_date=date(2025, 9, 1), end_date=date(2026, 6, 30))
        db.add(ay)
        db.flush()
        sem1 = Semester(academic_year_id=ay.id, number=1, start_date=date(2025, 9, 1), end_date=date(2025, 12, 31))
        sem2 = Semester(academic_year_id=ay.id, number=2, start_date=date(2026, 1, 13), end_date=date(2026, 6, 30))
        db.add_all([sem1, sem2])
        db.flush()

        # 6. Time slots
        slots = [
            (1, time(8, 0), time(9, 30)),
            (2, time(9, 40), time(11, 10)),
            (3, time(11, 20), time(12, 50)),
            (4, time(13, 10), time(14, 40)),
            (5, time(14, 50), time(16, 20)),
            (6, time(16, 30), time(18, 0)),
            (7, time(18, 10), time(19, 40)),
        ]
        for num, start, end in slots:
            db.add(TimeSlot(number=num, start_time=start, end_time=end))
        db.flush()

        # 7. Subjects
        subject_map = {}
        for name in subjects_data:
            s = Subject(name=name)
            db.add(s)
            db.flush()
            subject_map[name] = s
        print(f"  + {len(subject_map)} предметов")

        # 8. Curriculum → HourGrid
        added = 0
        skipped = 0
        for grp_name, subj_name, theory, practice, sem_num in curriculum_data:
            grp = group_map.get(grp_name)
            subj = subject_map.get(subj_name)
            
            # Автоматически добавляем предмет в базу, если его забыли указать в блоке subjects
            if not subj:
                subj = Subject(name=subj_name)
                db.add(subj)
                db.flush()
                subject_map[subj_name] = subj
            
            if not grp:
                skipped += 1
                continue
            
            sem = sem1 if sem_num == 1 else sem2
            if theory > 0:
                db.add(HourGrid(
                    group_id=grp.id, subject_id=subj.id, semester_id=sem.id,
                    lesson_type=LessonType.LECTURE, total_hours=theory,
                ))
                added += 1
            if practice > 0:
                db.add(HourGrid(
                    group_id=grp.id, subject_id=subj.id, semester_id=sem.id,
                    lesson_type=LessonType.PRACTICE, total_hours=practice,
                ))
                added += 1
        db.flush()
        print(f"  + {added} записей HourGrid (пропущено: {skipped})")

        # 9. Default users
        db.add(User(
            username="990101000001",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            full_name="Администратор",
        ))
        g1 = group_map.get("WEB 1-1") or group_map.get("WEB1-1")
        db.add(User(
            username="050515000123",
            password_hash=get_password_hash("student123"),
            role=UserRole.STUDENT,
            full_name="Иванов Иван",
            group_id=g1.id if g1 else 1,
        ))
        db.flush()

        db.commit()
        print("\n✅ Импорт завершён успешно!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    run_import()
