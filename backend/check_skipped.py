import os
import sys

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(__file__))

from import_sql import parse_groups, parse_subjects, parse_curriculum, SQL_FILE

def check():
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_text = f.read()

    groups_data = parse_groups(sql_text)
    subjects_data = parse_subjects(sql_text)
    curriculum_data = parse_curriculum(sql_text)

    group_names = {name for name, _ in groups_data}
    subject_names = set(subjects_data)

    missing = []
    for grp_name, subj_name, _, _, _ in curriculum_data:
        if grp_name not in group_names or subj_name not in subject_names:
            reason = []
            if grp_name not in group_names:
                reason.append(f"Группа '{grp_name}' не найдена")
            if subj_name not in subject_names:
                reason.append(f"Предмет '{subj_name}' не найден")
            
            missing.append(f"{grp_name} -> {subj_name} ({', '.join(reason)})")

    print(f"Всего пропущено: {len(missing)}\n")
    for m in missing:
        print(m)

if __name__ == "__main__":
    check()
