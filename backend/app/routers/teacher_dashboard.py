from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.dependencies import require_authenticated
from app.models.models import (
    User, ScheduleRow, Subject, Group, TeacherSubject,
)

router = APIRouter(prefix="/api/teacher", tags=["Дашборд преподавателя"])


@router.get("/stats")
def get_teacher_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if not current_user.teacher_id:
        return {"hours_per_week": 0, "total_lessons": 0, "subjects_count": 0, "groups_count": 0}

    tid = int(current_user.teacher_id)

    total_lessons = db.query(func.count(ScheduleRow.schedule_id)).filter(
        ScheduleRow.teacher_id == tid
    ).scalar() or 0

    subjects_count = db.query(func.count(func.distinct(TeacherSubject.subject_id))).filter(
        TeacherSubject.teacher_id == tid,
        TeacherSubject.is_active == True,
    ).scalar() or 0

    groups_count = db.query(func.count(func.distinct(ScheduleRow.group_id))).filter(
        ScheduleRow.teacher_id == tid
    ).scalar() or 0

    hours_per_week = total_lessons * 2

    return {
        "hours_per_week": hours_per_week,
        "total_lessons": total_lessons,
        "subjects_count": subjects_count,
        "groups_count": groups_count,
    }


@router.get("/workload")
def get_teacher_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if not current_user.teacher_id:
        return []

    tid = int(current_user.teacher_id)

    # Если расписание сгенерировано — берём оттуда (уникальные пары предмет+группа)
    rows = db.query(ScheduleRow).filter(ScheduleRow.teacher_id == tid).all()
    if rows:
        subject_map = {s.subject_id: s for s in db.query(Subject).all()}
        group_map = {g.group_id: g for g in db.query(Group).all()}
        seen: set = set()
        result = []
        for r in rows:
            key = (int(r.subject_id), int(r.group_id))
            if key in seen:
                continue
            seen.add(key)
            subj = subject_map.get(int(r.subject_id))
            grp = group_map.get(int(r.group_id))
            result.append({
                "subject_name": subj.name if subj else "—",
                "group_name": grp.name if grp else "—",
            })
        return result

    # Иначе — показываем дисциплины из teacher_subjects
    ts_rows = db.query(TeacherSubject).filter(TeacherSubject.teacher_id == tid).all()
    if not ts_rows:
        return []

    subject_map = {s.subject_id: s for s in db.query(Subject).all()}
    return [
        {
            "subject_name": subject_map[int(r.subject_id)].name
                if int(r.subject_id) in subject_map else "—",
            "group_name": "—",
        }
        for r in ts_rows
    ]
