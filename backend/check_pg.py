import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.models import (
    Curriculum, AcademicPeriod, TeacherSubject, TimeSlot,
    Room, Group, Teacher, Subject
)

db = SessionLocal()
try:
    periods = db.query(AcademicPeriod).filter(AcademicPeriod.is_active == True).all()
    print("Активные периоды:")
    for p in periods:
        count = db.query(Curriculum).filter(
            Curriculum.academic_period_id == p.academic_period_id
        ).count()
        print(f"  id={p.academic_period_id} name={p.name!r} term={p.term_no} curriculum={count}")

    print()
    print("TimeSlots:", db.query(TimeSlot).count())
    print("Rooms:    ", db.query(Room).count())
    print("Groups:   ", db.query(Group).count())
    print("Teachers: ", db.query(Teacher).count())
    print("TeacherSubjects:", db.query(TeacherSubject).count())

    if periods:
        pid = periods[-1].academic_period_id  # последний (активный) период
        currs = db.query(Curriculum).filter(
            Curriculum.academic_period_id == pid
        ).limit(30).all()
        matched = 0
        unmatched_ids = []
        for c in currs:
            tids = [
                ts.teacher_id
                for ts in db.query(TeacherSubject)
                    .filter(TeacherSubject.subject_id == c.subject_id).all()
            ]
            if tids:
                matched += 1
            else:
                unmatched_ids.append(c.subject_id)
        print(f"\nПроверка 30 curriculum периода {pid}: matched={matched} unmatched={len(unmatched_ids)}")
        if unmatched_ids:
            print("  subject_ids без учителей (первые 5):", unmatched_ids[:5])

        # Проверяем planned_weekly_hours
        small = db.query(Curriculum).filter(
            Curriculum.academic_period_id == pid,
            Curriculum.planned_weekly_hours < 2
        ).count()
        zero = db.query(Curriculum).filter(
            Curriculum.academic_period_id == pid,
            Curriculum.planned_weekly_hours == 0
        ).count()
        print(f"  planned_weekly_hours < 2: {small}")
        print(f"  planned_weekly_hours = 0: {zero}")
finally:
    db.close()

print("\nОК!")
