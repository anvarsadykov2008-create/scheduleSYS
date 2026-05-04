from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.dependencies import require_authenticated
from app.models.models import Teacher, ScheduleRow, Room, RoomType, User

router = APIRouter(prefix="/api/reports", tags=["Отчёты"])


@router.get("/teacher-workload")
def get_teacher_workload(db: Session = Depends(get_db), current_user: User = Depends(require_authenticated)):
    results = (
        db.query(
            Teacher.teacher_id,
            Teacher.last_name,
            Teacher.first_name,
            Teacher.middle_name,
            func.count(ScheduleRow.schedule_id).label("total_lessons"),
            func.count(func.distinct(ScheduleRow.subject_id)).label("unique_subjects"),
            func.count(func.distinct(ScheduleRow.group_id)).label("unique_groups"),
        )
        .join(ScheduleRow, ScheduleRow.teacher_id == Teacher.teacher_id)
        .group_by(Teacher.teacher_id, Teacher.last_name, Teacher.first_name, Teacher.middle_name)
        .order_by(Teacher.last_name)
        .all()
    )
    return [
        {
            "teacher_id": r.teacher_id,
            "full_name": f"{r.last_name} {r.first_name}" + (f" {r.middle_name}" if r.middle_name else ""),
            "total_lessons": r.total_lessons,
            "hours_per_week": r.total_lessons * 2,
            "unique_subjects": r.unique_subjects,
            "unique_groups": r.unique_groups,
        }
        for r in results
    ]


@router.get("/classroom-utilization")
def get_classroom_utilization(db: Session = Depends(get_db), current_user: User = Depends(require_authenticated)):
    total_slots = db.query(func.count(func.distinct(
        func.concat(ScheduleRow.time_slot_id)
    ))).scalar() or 30

    results = (
        db.query(
            Room.room_id,
            Room.code,
            RoomType.name.label("room_type"),
            func.count(ScheduleRow.schedule_id).label("used_slots"),
        )
        .outerjoin(ScheduleRow, ScheduleRow.room_id == Room.room_id)
        .outerjoin(RoomType, RoomType.room_type_id == Room.room_type_id)
        .group_by(Room.room_id, Room.code, RoomType.name)
        .order_by(Room.code)
        .all()
    )
    return [
        {
            "classroom_id": r.room_id,
            "name": r.code,
            "room_type": r.room_type or "—",
            "used_slots": r.used_slots,
            "total_slots": total_slots,
            "utilization_percent": round((r.used_slots / total_slots) * 100, 1) if total_slots > 0 else 0,
        }
        for r in results
    ]
