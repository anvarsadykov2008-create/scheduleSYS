"""
Привязка преподавателей к предметам и группам через TeacherSubject.
Сопоставляет teachers.subjects (текст из SQL) с записями HourGrid.
"""
import re, os, sys
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Teacher, Subject, Group, HourGrid, TeacherSubject


SQL_FILE = os.path.join(os.path.dirname(__file__), "..", "Обновленная главная бдшка.sql")


def parse_teacher_subjects_from_sql():
    """Парсит поле subjects из INSERT INTO teachers."""
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql = f.read()
    pattern = r"INSERT INTO teachers \(last_name, first_name, middle_name, subjects\)\s*VALUES\s*(.*?);"
    m = re.search(pattern, sql, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)

    result = {}
    # Разбиваем на строки вида ('Фамилия', 'Имя', 'Отчество', 'Предмет1, Предмет2')
    for row in re.finditer(r"\('([^']*)',\s*'([^']*)',\s*(?:'([^']*)'|NULL),\s*(?:'([^']*)'|NULL)\)", block):
        last, first, middle, subjects_str = row.groups()
        full = f"{last} {first}" + (f" {middle}" if middle else "")
        subj_list = []
        if subjects_str:
            subj_list = [s.strip() for s in subjects_str.split(",") if s.strip()]
        result[full.strip()] = subj_list
    return result


def run():
    teacher_subj_map = parse_teacher_subjects_from_sql()
    print(f"Из SQL: {len(teacher_subj_map)} преподавателей с предметами")

    db: Session = SessionLocal()
    try:
        teachers = {t.full_name: t for t in db.query(Teacher).all()}
        subjects = {s.name: s for s in db.query(Subject).all()}
        # Все записи HourGrid для получения связей group-subject
        hour_grids = db.query(HourGrid).all()

        # Построим маппинг subject_id → list of group_ids из HourGrid
        subj_to_groups = {}
        for hg in hour_grids:
            subj_to_groups.setdefault(hg.subject_id, set()).add(hg.group_id)

        # Для нечёткого поиска предметов
        def find_subject(keyword):
            """Ищет предмет по ключевому слову."""
            kw = keyword.lower().strip()
            # Сначала точное совпадение
            for name, s in subjects.items():
                if name.lower() == kw:
                    return s
            # Потом поиск по вхождению
            matches = []
            for name, s in subjects.items():
                if kw in name.lower():
                    matches.append(s)
            if len(matches) == 1:
                return matches[0]
            # Если много совпадений — берём самое короткое (наиболее точное)
            if matches:
                return min(matches, key=lambda s: len(s.name))
            return None

        def find_teacher(full_name):
            """Ищет учителя по имени."""
            if full_name in teachers:
                return teachers[full_name]
            # Поиск по фамилии
            surname = full_name.split()[0]
            for name, t in teachers.items():
                if name.startswith(surname):
                    return t
            return None

        added = 0
        not_found_subjects = set()
        existing = set()

        for teacher_name, subj_keywords in teacher_subj_map.items():
            teacher = find_teacher(teacher_name)
            if not teacher:
                continue
            if not subj_keywords:
                continue

            for kw in subj_keywords:
                subj = find_subject(kw)
                if not subj:
                    not_found_subjects.add(kw)
                    continue

                # Получаем группы, у которых этот предмет в HourGrid
                group_ids = subj_to_groups.get(subj.id, set())
                if not group_ids:
                    # Если нет в HourGrid — всё равно создаём без группы? 
                    # Нет, TeacherSubject требует group_id. Пропускаем.
                    continue

                for gid in group_ids:
                    key = (teacher.id, subj.id, gid)
                    if key not in existing:
                        existing.add(key)
                        db.add(TeacherSubject(
                            teacher_id=teacher.id,
                            subject_id=subj.id,
                            group_id=gid,
                        ))
                        added += 1

        db.commit()
        print(f"\n✅ Добавлено {added} записей TeacherSubject")
        if not_found_subjects:
            print(f"⚠️  Не найдены предметы ({len(not_found_subjects)}):")
            for s in sorted(not_found_subjects):
                print(f"   - {s}")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    run()
