import sys
import os

# Ensure we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.scheduler import ScheduleGenerator
from app.models.models import Semester

def verify_generation():
    db = SessionLocal()
    try:
        # Get semester 1
        semester = db.query(Semester).filter(Semester.number == 1).first()
        if not semester:
            print("❌ Semester 1 not found!")
            return

        print(f"🔄 Generating schedule for semester {semester.id}...")
        generator = ScheduleGenerator(db, semester.id)
        result = generator.generate(description="Verification Run")
        
        print(f"✅ Generation complete. Version ID: {result.version_id}")
        print(f"📦 Placed: {result.placed_count} / {result.total_count}")
        
        if result.unplaced:
            print(f"⚠️ Unplaced ({len(result.unplaced)}):")
            for u in result.unplaced[:5]:
                print(f"  - {u['group']} / {u['subject']} ({u['reason']})")
        else:
            print("🎉 All lessons successfully placed!")
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_generation()
