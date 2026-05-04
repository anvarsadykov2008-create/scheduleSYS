from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import TimeSlot, User
from app.dependencies import require_admin_or_dispatcher
from app.schemas.schemas import TimeSlotCreate, TimeSlotUpdate, TimeSlotResponse
from app.routers.audit import log_action

router = APIRouter(prefix="/api/time-slots", tags=["Временные слоты"])


@router.get("", response_model=List[TimeSlotResponse])
def get_time_slots(db: Session = Depends(get_db)):
    return db.query(TimeSlot).order_by(TimeSlot.slot_number).all()


@router.post("", response_model=TimeSlotResponse, status_code=201)
def create_time_slot(data: TimeSlotCreate, db: Session = Depends(get_db)):
    ts = TimeSlot(**data.model_dump())
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return ts


@router.put("/{slot_id}", response_model=TimeSlotResponse)
def update_time_slot(slot_id: int, data: TimeSlotUpdate, db: Session = Depends(get_db)):
    ts = db.query(TimeSlot).filter(TimeSlot.time_slot_id == slot_id).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Слот не найден")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ts, key, value)
    db.commit()
    db.refresh(ts)
    return ts


@router.delete("/{slot_id}", status_code=204)
def delete_time_slot(slot_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_dispatcher)):
    ts = db.query(TimeSlot).filter(TimeSlot.time_slot_id == slot_id).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Слот не найден")
    db.delete(ts)
    db.commit()
    log_action(db, current_user.id, "DELETE", "time_slots", slot_id, {"slot_number": ts.slot_number, "start_time": str(ts.start_time)})
