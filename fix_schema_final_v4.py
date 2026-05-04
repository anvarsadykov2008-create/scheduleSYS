import re

tables = [
    "departments", "specialties", "academic_periods", "lesson_types", "room_types",
    "time_slots", "teachers", "subjects", "groups", "group_subgroups", "rooms",
    "teacher_preferences", "teacher_load", "teacher_subjects", "subject_lesson_types",
    "subject_room_type", "teacher_unavailability", "group_unavailability",
    "room_unavailability", "group_subject_load", "schedule_generation_runs",
    "schedule_conflicts_log", "schedule"
]

with open('college_schedule_production_schema.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# 1. Заменяем первичные ключи в CREATE TABLE и INSERT
for table in tables:
    # Имя столбца PK в оригинале
    pk_name = f"{table.rstrip('s')}_id" if not table.endswith('_log') and not table.endswith('_runs') else f"{table.rstrip('s')}_id"
    
    # Чтобы не гадать, просто возьмем из оригинала (в скрипте они почти всегда [singular]_id)
    # Но некоторые таблицы имеют сложные имена. Проверим точные имена из grep ранее:
    # department_id, specialty_id, academic_period_id, lesson_type_id, room_type_id, 
    # time_slot_id, teacher_id, subject_id, group_id, subgroup_id, room_id, ...
    
    # Список из grep:
    singular_map = {
        "departments": "department",
        "specialties": "specialty",
        "academic_periods": "academic_period",
        "lesson_types": "lesson_type",
        "room_types": "room_type",
        "time_slots": "time_slot",
        "teachers": "teacher",
        "subjects": "subject",
        "groups": "group",
        "group_subgroups": "subgroup",
        "rooms": "room",
        "teacher_preferences": "teacher_preference",
        "teacher_load": "teacher_load",
        "teacher_subjects": "teacher_subject",
        "subject_lesson_types": "subject_lesson_type",
        "subject_room_type": "subject_room_type",
        "teacher_unavailability": "teacher_unavailability",
        "group_unavailability": "group_unavailability",
        "room_unavailability": "room_unavailability",
        "group_subject_load": "group_subject_load",
        "schedule_generation_runs": "generation_run",
        "schedule_conflicts_log": "schedule_conflict",
        "schedule": "schedule"
    }
    
    singular = singular_map.get(table, table.rstrip('s'))
    pk_original = f"{singular}_id"
    
    print(f"Processing table {table}: {pk_original} -> id")
    
    # Переименование PK в определении таблицы
    sql = re.sub(rf'(\s+){pk_original}(\s+BIGINT\s+GENERATED)', r'\1id\2', sql)
    
    # Переименование в REFERENCES (когда другие таблицы ссылаются на эту)
    sql = re.sub(rf'REFERENCES\s+{table}\s*\(\s*{pk_original}\s*\)', f'REFERENCES {table}(id)', sql)
    
    # Переименование в INSERT для этой таблицы
    sql = re.sub(rf'INSERT INTO {table}\s*\(\s*{pk_original}\s*,', f'INSERT INTO {table} (id,', sql)
    
    # Переименование в триггерах/функциях/индексах (когда используется префикс таблицы или псевдоним)
    # Например: gs.subgroup_id -> gs.id, NEW.subgroup_id -> NEW.id (только для этой таблицы)
    # Это сложно сделать универсально, но попробуем для NEW/OLD и алиасов
    sql = re.sub(rf'\b(NEW|OLD|{table})\.{pk_original}\b', r'\1.id', sql)
    
    # Специальный случай для алиасов из триггеров ( gs.subgroup_id -> gs.id )
    if table == "group_subgroups":
        sql = sql.replace("gs.subgroup_id", "gs.id")

# Дополнительные исправления для триггеров, которые я видел
sql = sql.replace("NEW.academic_period_id", "NEW.id") # если это триггер на academic_periods
sql = sql.replace("NEW.group_id", "NEW.id") # если это триггер на groups (не на subgroups!)

with open('college_schedule_production_schema_fixed.sql', 'w', encoding='utf-8') as f:
    f.write(sql)
