import json
import random

last_names = ["Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков", "Фёдоров", "Морозов", "Волков", "Алексеев", "Лебедев", "Семенов", "Егоров", "Павлов", "Козлов", "Степанов", "Николаев", "Орлов", "Андреев", "Макаров", "Никитин", "Захаров"]
initials = ["А.А.", "В.В.", "И.И.", "П.П.", "С.С.", "Е.Е.", "Д.Д.", "М.М.", "Н.Н.", "О.О."]

subjects_data = [
    {"id": "s1", "name": "Высшая математика", "type": "lecture"},
    {"id": "s2", "name": "Физика", "type": "lecture"},
    {"id": "s3", "name": "Основы алгоритмизации", "type": "practice"},
    {"id": "s4", "name": "Базы данных (SQL)", "type": "practice"},
    {"id": "s5", "name": "Веб-разработка", "type": "practice"},
    {"id": "s6", "name": "История", "type": "lecture"},
    {"id": "s7", "name": "Английский язык", "type": "practice"},
    {"id": "s8", "name": "Физкультура", "type": "sport"},
    {"id": "s9", "name": "Операционные системы", "type": "practice"},
    {"id": "s10", "name": "Компьютерные сети", "type": "practice"},
    {"id": "s11", "name": "Философия", "type": "lecture"},
    {"id": "s12", "name": "Информационная безопасность", "type": "practice"}
]

course_subjects = {
    1: ["s1", "s2", "s6", "s8", "s11"],       # 1 курс
    2: ["s1", "s3", "s7", "s8", "s9"],        # 2 курс
    3: ["s4", "s5", "s7", "s10"],             # 3 курс
    4: ["s4", "s5", "s10", "s12"]             # 4 курс
}

groups = []
group_prefixes = ["ИС", "ПРОГ", "ВЕБ", "БД", "СЕТИ"]
for i in range(1, 31):
    course = random.randint(1, 4)
    year = 26 - course  # Отталкиваемся от 2026 года
    groups.append({
        "id": f"g{i}",
        "name": f"{random.choice(group_prefixes)}-{year}-{random.randint(1,3)}",
        "course": course,
        "students_count": random.randint(15, 30)
    })

teachers = []
teacher_subjects = {} 
for i in range(1, 51):
    subject = random.choice(subjects_data)
    t_id = f"t{i}"
    teachers.append({
        "id": t_id,
        "name": f"{random.choice(last_names)} {random.choice(initials)}",
        "specialty": subject["name"],
        "max_pairs_per_week": random.choice([12, 15, 18, 20])
    })
    teacher_subjects[t_id] = subject["id"]

curriculum = []
teacher_current_load = {t["id"]: 0 for t in teachers}

for group in groups:
    pairs_needed = 18
    course = group["course"]
    allowed_subject_ids = course_subjects[course] 
    
    attempts = 0
    while pairs_needed > 0 and attempts < 100:
        attempts += 1
        
        available_teachers = [
            t for t in teachers 
            if teacher_subjects[t["id"]] in allowed_subject_ids and teacher_current_load[t["id"]] < t["max_pairs_per_week"]
        ]
        
        if not available_teachers:
            break 
            
        teacher = random.choice(available_teachers)
        t_id = teacher["id"]
        sub_id = teacher_subjects[t_id]
        
        max_assign = min(4, pairs_needed)
        if max_assign < 2:
            pairs_to_assign = 1
        else:
            pairs_to_assign = random.randint(2, max_assign)
        
        if teacher_current_load[t_id] + pairs_to_assign > teacher["max_pairs_per_week"]:
            pairs_to_assign = teacher["max_pairs_per_week"] - teacher_current_load[t_id]
            
        if pairs_to_assign <= 0:
            continue

        existing_record = next((item for item in curriculum if item["group_id"] == group["id"] and item["subject_id"] == sub_id), None)
        
        if existing_record:
            existing_record["pairs_per_week"] += pairs_to_assign
        else:
            curriculum.append({
                "group_id": group["id"],
                "subject_id": sub_id,
                "teacher_id": t_id,
                "pairs_per_week": pairs_to_assign
            })
            
        teacher_current_load[t_id] += pairs_to_assign
        pairs_needed -= pairs_to_assign

final_data = {
    "subjects": subjects_data,
    "groups": groups,
    "teachers": teachers,
    "curriculum": curriculum
}

with open("college_data.json", "w", encoding="utf-8") as file:
    json.dump(final_data, file, ensure_ascii=False, indent=2)

print("✅ Файл 'college_data.json' успешно сгенерирован (без ошибок)!")