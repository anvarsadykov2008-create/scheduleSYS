from app.database import SessionLocal
from app.models.models import Semester, ScheduleVersion, ScheduleEntry
from app.services.scheduler import ScheduleGenerator

db = SessionLocal()

print("🚀 Запуск генерации расписания...")

# 1. Получаем семестр (возьмем 2-й семестр, он активный)
sem = db.query(Semester).filter(Semester.number == 2).first()
if not sem:
    print("❌ Семестр 2 не найден!")
    exit()

print(f"📅 Семестр: {sem.academic_year.name}, семестр {sem.number}")

# 2. Запускаем генератор
try:
    generator = ScheduleGenerator(db, sem.id)
    result = generator.generate(description="Ручная генерация через скрипт")
    
    print(f"\n✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА (версия {result.version_id})")
    print(f"📌 Размещено занятий: {result.placed_count}")
    print(f"⚠️  Не удалось разместить: {len(result.unplaced)}")
    
    if result.unplaced:
        print("\nСписок неразмещенных (первые 10):")
        for u in result.unplaced[:10]:
            print(f"   - {u['group']} / {u['subject']} ({u['lesson_type']}) — {u['reason']}")
            
        print(f"\n... и еще {len(result.unplaced) - 10} занятий.")
    else:
        print("\n🎉 Все занятия успешно размещены!")

except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
