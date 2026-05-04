"""
CRUD пользователей (ТЗ §4 — управление пользователями и ролями).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import User, UserRole, AuditLog
from app.auth import get_password_hash, verify_password, get_current_active_user
from app.dependencies import require_admin

router = APIRouter(prefix="/api/users", tags=["Пользователи"])


# ──── Schemas ────

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    full_name: Optional[str] = None
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    full_name: Optional[str] = None
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None

    class Config:
        from_attributes = True


# ──── Endpoints ────

@router.get("", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id).all()
    return [
        UserOut(
            id=u.id,
            username=u.username,
            role=u.role.value if hasattr(u.role, 'value') else str(u.role),
            full_name=u.full_name,
            teacher_id=u.teacher_id,
            group_id=u.group_id,
        )
        for u in users
    ]


@router.post("", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    role_map = {
        "ADMIN": UserRole.ADMIN,
        "DISPATCHER": UserRole.DISPATCHER,
        "TEACHER": UserRole.TEACHER,
        "STUDENT": UserRole.STUDENT,
        "MANAGEMENT": UserRole.MANAGEMENT,
        # Русские варианты (для совместимости)
        "администратор": UserRole.ADMIN,
        "диспетчер": UserRole.DISPATCHER,
        "преподаватель": UserRole.TEACHER,
        "студент": UserRole.STUDENT,
        "администрация": UserRole.MANAGEMENT,
    }
    
    role_enum = role_map.get(data.role.upper() if data.role else "STUDENT")
    if not role_enum:
        # Пытаемся по русскому ключу (без upper)
        role_enum = role_map.get(data.role)
        
    if not role_enum:
        raise HTTPException(status_code=400, detail=f"Неизвестная роль: {data.role}")

    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        role=role_enum,
        full_name=data.full_name,
        teacher_id=data.teacher_id,
        group_id=data.group_id,
        is_not_student=(role_enum != UserRole.STUDENT)
    )
    db.add(user)
    db.flush()  # Get ID

    # Audit Log
    db.add(AuditLog(
        user_id=current_user.id,
        action="CREATE",
        entity="users",
        entity_id=user.id,
        details={"username": user.username, "role": user.role.value}
    ))
    
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        username=user.username,
        role=user.role.value,
        full_name=user.full_name,
        teacher_id=user.teacher_id,
        group_id=user.group_id,
    )


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        role_map = {
            "ADMIN": UserRole.ADMIN,
            "DISPATCHER": UserRole.DISPATCHER,
            "TEACHER": UserRole.TEACHER,
            "STUDENT": UserRole.STUDENT,
            "MANAGEMENT": UserRole.MANAGEMENT,
            # Русские варианты (для совместимости)
            "администратор": UserRole.ADMIN,
            "диспетчер": UserRole.DISPATCHER,
            "преподаватель": UserRole.TEACHER,
            "студент": UserRole.STUDENT,
            "администрация": UserRole.MANAGEMENT,
        }
        role_enum = role_map.get(data.role.upper() if data.role else "STUDENT")
        if not role_enum:
            role_enum = role_map.get(data.role)
            
        if not role_enum:
            raise HTTPException(status_code=400, detail=f"Неизвестная роль: {data.role}")
        user.role = role_enum
        user.is_not_student = (role_enum != UserRole.STUDENT)
    if data.teacher_id is not None:
        user.teacher_id = data.teacher_id
    if data.group_id is not None:
        user.group_id = data.group_id
    if data.password:
        user.password_hash = get_password_hash(data.password)

    # Audit Log
    db.add(AuditLog(
        user_id=current_user.id,
        action="UPDATE",
        entity="users",
        entity_id=user.id,
        details=data.model_dump(exclude_unset=True)
    ))

    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        username=user.username,
        role=user.role.value,
        full_name=user.full_name,
        teacher_id=user.teacher_id,
        group_id=user.group_id,
    )


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Невозможно удалить самого себя")
    
    # Audit Log
    db.add(AuditLog(
        user_id=current_user.id,
        action="DELETE",
        entity="users",
        entity_id=user.id,
        details={"username": user.username}
    ))

    db.delete(user)
    db.commit()

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

@router.post("/me/change-password")
def change_my_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный старый пароль")
    
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Пароль успешно изменен"}
