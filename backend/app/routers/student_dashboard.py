from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.dependencies import require_authenticated
from app.models.models import User, ScheduleRow, Subject, Group

router = APIRouter(prefix="/api/student", tags=["Дашборд студента"])


@router.get("/dashboard")
def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if not current_user.group_id:
        return {
            "group_name": "—",
            "course": None,
            "stats": {"hours_per_week": 0, "lessons_per_week": 0, "subjects_count": 0, "days_count": 0},
        }

    gid = int(current_user.group_id)
    grp = db.query(Group).filter(Group.group_id == gid).first()

    rows = db.query(ScheduleRow).filter(ScheduleRow.group_id == gid).all()

    lessons_per_week = len(rows)
    hours_per_week = lessons_per_week * 2
    subjects_count = len({int(r.subject_id) for r in rows})

    from app.models.models import TimeSlot
    ts_map = {ts.time_slot_id: ts for ts in db.query(TimeSlot).all()}
    days_with_lessons = {int(ts_map[int(r.time_slot_id)].day_of_week) for r in rows if int(r.time_slot_id) in ts_map}
    days_count = len(days_with_lessons)

    return {
        "group_name": grp.name if grp else "—",
        "course": grp.course_no if grp else None,
        "stats": {
            "hours_per_week": hours_per_week,
            "lessons_per_week": lessons_per_week,
            "subjects_count": subjects_count,
            "days_count": days_count,
        },
    }
