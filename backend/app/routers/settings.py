from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import SystemSetting, User, UserRole
from app.dependencies import require_admin

router = APIRouter(prefix="/api/settings", tags=["Настройки"])

class SettingSchema(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    class Config:
        from_attributes = True

@router.get("", response_model=List[SettingSchema])
def get_settings(db: Session = Depends(get_db)):
    """Получить все настройки."""
    # Ensure default settings exist
    defaults = {
        "max_daily_lessons": "4",
        "min_teacher_gap": "0", 
        "semester_start": "2025-09-01"
    }
    for k, v in defaults.items():
        if not db.query(SystemSetting).filter(SystemSetting.key == k).first():
            db.add(SystemSetting(key=k, value=v, description="Default setting"))
    db.commit()
    
    return db.query(SystemSetting).all()

@router.put("/{key}", response_model=SettingSchema)
def update_setting(
    key: str, 
    value: str, # passed as query or body? Body preferred.
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Обновить настройку (только админ)."""
    
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        setting = SystemSetting(key=key, value=value)
        db.add(setting)
    else:
        setting.value = value
    
    db.commit()
    db.refresh(setting)
    return setting

class UpdateSettingRequest(BaseModel):
    value: str

@router.post("/{key}", response_model=SettingSchema)
def update_setting_post(
    key: str, 
    body: UpdateSettingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return update_setting(key, body.value, db, current_user)
