import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.models import AcademicPeriod, ScheduleGenerationRun
from app.services.scheduler import ScheduleGenerator

from app.config import settings

def main():
    print(f"Connecting to: {settings.database_url}")
    db = SessionLocal()
    try:
        # 1. Find active period
        period = db.query(AcademicPeriod).filter(AcademicPeriod.is_active == True).first()
        if not period:
            print("No active academic period found!")
            return
        
        print(f"Using period: {period.name} (ID: {period.id})")
        
        # 2. Create a generation run
        run = ScheduleGenerationRun(
            academic_period_id=period.id,
            status="running",
            requested_by="System (Auto-fill)",
            parameters={"mode": "auto"},
            started_at=datetime.now(timezone.utc)
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        print(f"Generation run created (ID: {run.id})")
        
        # 3. Initialize generator and run
        generator = ScheduleGenerator(db)
        result = generator.generate(period.id, run.id)
        
        # 4. Finalize run status
        run.status = "completed"
        db.commit()
        
        print(f"Generation complete!")
        print(f"Placed: {result.placed_count} / {result.total_count}")
        print(f"Unplaced: {len(result.unplaced)}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
