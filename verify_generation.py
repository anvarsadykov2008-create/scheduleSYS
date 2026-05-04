import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.database import SessionLocal
from app.services.scheduler import ScheduleGenerator
from app.models.models import Semester

def verify_generation():
    db = SessionLocal()
    try:
        # Получаем семестр 1 (осенний)
        semester = db.query(Semester).filter(Semester.number == 1).first()
        if not semester:
            print("❌ Семестр 1 не найден!")
            return

        print(f"🔄 Сгенерируем расписание для семестра {semester.id}...")
        generator = ScheduleGenerator(db, semester.id)
        result = generator.generate(description="Verification Test Run")
        
        print(f"✅ Генерация завершена. Версия ID: {result.version_id}")
        print(f"📦 Размещено: {result.placed_count} / {result.total_count}")
        
        if result.unplaced:
            print(f"⚠️ Неразмещенные ({len(result.unplaced)}):")
            for u in result.unplaced[:5]:
                print(f"  - {u['group']} / {u['subject']} ({u['reason']})")
        else:
            print("🎉 Все занятия успешно размещены!")
            
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_generation()
