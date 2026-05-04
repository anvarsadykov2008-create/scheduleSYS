from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models.models import Teacher, Room, TeacherRoom, User
from app.dependencies import require_admin_or_dispatcher

router = APIRouter(prefix="/api/teachers", tags=["Кабинеты преподавателей"])


class TeacherRoomCreate(BaseModel):
    room_id: int
    is_primary: bool = False


class TeacherRoomResponse(BaseModel):
    id: int
    teacher_id: int
    room_id: int
    room_code: str
    room_name: str
    is_primary: bool

    class Config:
        from_attributes = True


@router.get("/{teacher_id}/rooms", response_model=List[TeacherRoomResponse])
def get_teacher_rooms(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    room_map = {r.room_id: r for r in db.query(Room).all()}
    result = []
    for tr in db.query(TeacherRoom).filter(TeacherRoom.teacher_id == teacher_id).all():
        room = room_map.get(int(tr.room_id))
        result.append(TeacherRoomResponse(
            id=int(tr.id),
            teacher_id=int(tr.teacher_id),
            room_id=int(tr.room_id),
            room_code=room.code if room else "—",
            room_name=room.name if room else "—",
            is_primary=bool(tr.is_primary),
        ))
    return result


@router.post("/{teacher_id}/rooms", response_model=TeacherRoomResponse, status_code=201)
def add_teacher_room(
    teacher_id: int,
    data: TeacherRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    room = db.query(Room).filter(Room.room_id == data.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    existing = db.query(TeacherRoom).filter(
        TeacherRoom.teacher_id == teacher_id,
        TeacherRoom.room_id == data.room_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Этот кабинет уже привязан к преподавателю")
    if data.is_primary:
        db.query(TeacherRoom).filter(TeacherRoom.teacher_id == teacher_id).update({"is_primary": False})
    tr = TeacherRoom(teacher_id=teacher_id, room_id=data.room_id, is_primary=data.is_primary)
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return TeacherRoomResponse(
        id=int(tr.id),
        teacher_id=int(tr.teacher_id),
        room_id=int(tr.room_id),
        room_code=room.code,
        room_name=room.name,
        is_primary=bool(tr.is_primary),
    )


@router.delete("/{teacher_id}/rooms/{room_id}", status_code=204)
def remove_teacher_room(
    teacher_id: int,
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    tr = db.query(TeacherRoom).filter(
        TeacherRoom.teacher_id == teacher_id,
        TeacherRoom.room_id == room_id,
    ).first()
    if not tr:
        raise HTTPException(status_code=404, detail="Привязка не найдена")
    db.delete(tr)
    db.commit()
