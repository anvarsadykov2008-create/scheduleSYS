from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import LessonType, User
from app.dependencies import require_admin_or_dispatcher

router = APIRouter(prefix="/api/lesson-types", tags=["Виды занятий"])


class LessonTypeCreate(BaseModel):
    code: str
    name: str
    is_lab: bool = False
    requires_room_match: bool = True


class LessonTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    is_lab: Optional[bool] = None
    requires_room_match: Optional[bool] = None
    is_active: Optional[bool] = None


class LessonTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    is_lab: bool
    requires_room_match: bool
    is_active: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[LessonTypeResponse])
def get_lesson_types(db: Session = Depends(get_db)):
    rows = db.query(LessonType).filter(LessonType.is_active == True).all()
    return [LessonTypeResponse(
        id=int(r.lesson_type_id), code=r.code, name=r.name,
        is_lab=bool(r.is_lab), requires_room_match=bool(r.requires_room_match),
        is_active=bool(r.is_active),
    ) for r in rows]


@router.post("", response_model=LessonTypeResponse, status_code=201)
def create_lesson_type(
    data: LessonTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    if db.query(LessonType).filter(LessonType.code == data.code).first():
        raise HTTPException(status_code=409, detail="Вид занятий с таким кодом уже существует")
    lt = LessonType(code=data.code, name=data.name, is_lab=data.is_lab, requires_room_match=data.requires_room_match)
    db.add(lt)
    db.commit()
    db.refresh(lt)
    return LessonTypeResponse(
        id=int(lt.lesson_type_id), code=lt.code, name=lt.name,
        is_lab=bool(lt.is_lab), requires_room_match=bool(lt.requires_room_match),
        is_active=bool(lt.is_active),
    )


@router.put("/{lt_id}", response_model=LessonTypeResponse)
def update_lesson_type(
    lt_id: int,
    data: LessonTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    lt = db.query(LessonType).filter(LessonType.lesson_type_id == lt_id).first()
    if not lt:
        raise HTTPException(status_code=404, detail="Вид занятий не найден")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lt, key, value)
    db.commit()
    db.refresh(lt)
    return LessonTypeResponse(
        id=int(lt.lesson_type_id), code=lt.code, name=lt.name,
        is_lab=bool(lt.is_lab), requires_room_match=bool(lt.requires_room_match),
        is_active=bool(lt.is_active),
    )


@router.delete("/{lt_id}", status_code=204)
def delete_lesson_type(
    lt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    lt = db.query(LessonType).filter(LessonType.lesson_type_id == lt_id).first()
    if not lt:
        raise HTTPException(status_code=404, detail="Вид занятий не найден")
    lt.is_active = False
    db.commit()
