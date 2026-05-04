"""
Тестирует генерацию расписания для периода 5 напрямую через PostgreSQL.
"""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.scheduler import ScheduleGenerator
from app.models.models import ScheduleGenerationRun, AcademicPeriod
from datetime import datetime, timezone

db = SessionLocal()
try:
    # Получаем активный период
    period = db.query(AcademicPeriod).filter(
        AcademicPeriod.is_active == True,
        AcademicPeriod.term_no == 2
    ).first()

    if not period:
        print("ОШИБКА: Активный период (term_no=2) не найден")
        sys.exit(1)

    print(f"Генерация для периода: id={period.academic_period_id} name={period.name!r}")

    # Создаём run запись
    run = ScheduleGenerationRun(
        academic_period_id=period.academic_period_id,
        status="queued",
        requested_by="test",
        generator_version="greedy-v2-test",
        parameters={"description": "test run", "ui_status": "generated"},
        created_schedule_rows=0,
        detected_conflicts=0,
        requested_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        notes="test run",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    print(f"Run ID: {run.generation_run_id}")

    # Удаляем старые записи расписания для этого периода
    from app.models.models import ScheduleRow
    deleted = db.query(ScheduleRow).filter(
        ScheduleRow.academic_period_id == period.academic_period_id
    ).delete(synchronize_session=False)
    db.commit()
    print(f"Удалено старых записей: {deleted}")

    # Генерируем
    generator = ScheduleGenerator(db)
    run.status = "running"
    db.commit()

    result = generator.generate(
        academic_period_id=period.academic_period_id,
        generation_run_id=run.generation_run_id
    )
    run.status = "completed"
    db.commit()

    print(f"\n=== РЕЗУЛЬТАТ ===")
    print(f"Размещено: {result.placed_count} / {result.total_count}")
    print(f"Не размещено: {len(result.unplaced)}")
    print(f"Предупреждения: {len(result.warnings)}")

    if result.warnings:
        print("\nПредупреждения:")
        for w in result.warnings[:10]:
            print(f"  - {w}")

    if result.unplaced:
        print("\nНеразмещённые (первые 10):")
        for u in result.unplaced[:10]:
            print(f"  - {u['group']} / {u['subject']} / {u['teacher']}: {u['reason']}")

finally:
    db.close()
