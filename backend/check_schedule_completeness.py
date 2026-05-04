from app.database import SessionLocal
from app.models.models import HourGrid, ScheduleEntry, ScheduleVersion, Semester, Subject, Group

db = SessionLocal()

# 1. Находим последнюю версию расписания
version = db.query(ScheduleVersion).order_by(ScheduleVersion.created_at.desc()).first()
if not version:
    print("❌ Расписание не найдено")
    exit()

print(f"📅 Проверка версии {version.id} (от {version.created_at})")

# 2. Считаем требуемые часы (из HourGrid)
# Важно: учитываем только активный семестр
sem_id = version.semester_id
hgs = db.query(HourGrid).filter(HourGrid.semester_id == sem_id).all()

required_hours = 0
required_pairs = 0
details = {} # (subject_name, group_name) -> pairs

for hg in hgs:
    required_hours += hg.total_hours
    pairs = hg.total_hours // 2
    required_pairs += pairs
    
    s = db.query(Subject).get(hg.subject_id)
    g = db.query(Group).get(hg.group_id)
    
    # Считаем недельную нагрузку
    # 17 недель в семестре
    # total_hours / 2 = всего пар
    # всего пар / 17 = пар в неделю
    pairs_sem = hg.total_hours // 2
    pairs_week = max(1, round(pairs_sem / 17))
    
    # Если подгруппы, то нагрузка удваивается (или делится, если tasks создаются для каждой)
    # В scheduler мы создаем task для каждой подгруппы, если subgroup_hours есть
    if hg.subgroup_hours:
        # Предполагаем, что 2 подгруппы
        pairs_week *= 2

    required_pairs += pairs_week
    
    key = (s.name, g.name)
    details[key] = details.get(key, 0) + pairs_week

print(f"📉 Требуется разместить (в неделю): {required_pairs} пар")

# 3. Считаем размещенные часы
entries = db.query(ScheduleEntry).filter(ScheduleEntry.version_id == version.id).all()
placed_pairs = len(entries)

print(f"📈 Размещено по факту:    {placed_pairs} пар")

if placed_pairs < required_pairs:
    missing = required_pairs - placed_pairs
    percent = (missing / required_pairs) * 100
    print(f"⚠️  НЕ ХВАТАЕТ:          {missing} пар ({percent:.1f}%)")
    
    # Попробуем найти кого не хватает
    placed_counts = {}
    for e in entries:
        s = db.query(Subject).get(e.subject_id)
        g = db.query(Group).get(e.group_id)
        key = (s.name, g.name)
        placed_counts[key] = placed_counts.get(key, 0) + 1
        
    print("\n🔍 Проблемные предметы (топ-10):")
    count = 0
    for key, req in details.items():
        actual = placed_counts.get(key, 0)
        if req > actual:
             print(f"   - {key[1]} / {key[0][:40]}...: {actual}/{req} (не хв. {req-actual})")
             count += 1
             if count >= 10: break
else:
    print(f"✅ ОТЛИЧНО! Требуется {required_pairs}, размещено {placed_pairs}. (Возможно, даже больше из-за округления)")

db.close()
