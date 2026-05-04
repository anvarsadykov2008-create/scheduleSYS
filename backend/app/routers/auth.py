import logging
import re
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token, get_current_active_user,
    get_password_hash, verify_password,
)
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db
from app.dependencies import require_admin_or_dispatcher
from app.models.models import Teacher, User, UserRole
from app.schemas.schemas import Token, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Авторизация"])

_IIN_RE = re.compile(r"^\d{12}$")
_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёҰұҚқҒғЖжӘәІіҢңҮүҺһ\s\-]+$")


# ─── Публичная регистрация (только роль STUDENT) ─────────────────────────────

class RegisterRequest(BaseModel):
    iin: str
    full_name: str
    password: Optional[str] = None
    group_id: Optional[int] = None
    # [FIX B-02] role удалена из публичного запроса — всегда STUDENT.
    #            Для назначения других ролей используйте POST /api/auth/register/staff


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Публичная регистрация студента по ИИН. Роль всегда STUDENT."""
    iin = data.iin.strip()
    full_name = data.full_name.strip()

    if not _IIN_RE.match(iin):
        raise HTTPException(status_code=400, detail="ИИН должен содержать ровно 12 цифр")
    if not _NAME_RE.match(full_name):
        raise HTTPException(status_code=400, detail="ФИО может содержать только буквы, пробелы и дефисы")
    if len(full_name.split()) < 2:
        raise HTTPException(status_code=400, detail="Введите фамилию и имя полностью")
    if db.query(User).filter(User.username == iin).first():
        raise HTTPException(status_code=400, detail="Пользователь с таким ИИН уже зарегистрирован")

    # Автогенерация пароля: последние 6 цифр ИИН + суффикс
    password = data.password or (iin[-6:] + "abc")

    user = User(
        username=iin,
        password_hash=get_password_hash(password),
        role=UserRole.STUDENT,
        full_name=full_name,
        group_id=data.group_id,
        is_not_student=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    # Пароль возвращается однократно при первой регистрации —
    # клиент должен показать его пользователю и не хранить.
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "initial_password": password,
        "message": f"Аккаунт создан. Ваш пароль: {password}",
    }


# ─── Регистрация сотрудника (требует роль admin/dispatcher) ──────────────────

class StaffRegisterRequest(BaseModel):
    iin: str
    full_name: str
    role: str  # TEACHER | DISPATCHER | MANAGEMENT | ADMIN
    password: Optional[str] = None


@router.post("/register/staff")
def register_staff(
    data: StaffRegisterRequest,
    db: Session = Depends(get_db),
    _auth: User = Depends(require_admin_or_dispatcher),  # guard: только admin/dispatcher
):
    """Регистрация сотрудника. Доступно только администратору или диспетчеру."""
    iin = data.iin.strip()
    full_name = data.full_name.strip()

    if not _IIN_RE.match(iin):
        raise HTTPException(status_code=400, detail="ИИН должен содержать ровно 12 цифр")
    if not _NAME_RE.match(full_name):
        raise HTTPException(status_code=400, detail="ФИО может содержать только буквы, пробелы и дефисы")
    if db.query(User).filter(User.username == iin).first():
        raise HTTPException(status_code=400, detail="Пользователь с таким ИИН уже зарегистрирован")

    role_map = {
        "ADMIN": UserRole.ADMIN,
        "DISPATCHER": UserRole.DISPATCHER,
        "TEACHER": UserRole.TEACHER,
        "MANAGEMENT": UserRole.MANAGEMENT,
    }
    role = role_map.get(data.role.upper())
    if not role:
        raise HTTPException(status_code=400, detail=f"Недопустимая роль: {data.role}. Допустимо: ADMIN, DISPATCHER, TEACHER, MANAGEMENT")

    password = data.password or (iin[-6:] + "abc")

    # Попытка найти преподавателя по ФИО
    teacher_id = None
    if role == UserRole.TEACHER:
        names = full_name.split()
        if len(names) >= 2:
            teacher = db.query(Teacher).filter(
                Teacher.last_name == names[0],
                Teacher.first_name == names[1],
            ).first()
            if teacher:
                teacher_id = teacher.teacher_id

    user = User(
        username=iin,
        password_hash=get_password_hash(password),
        role=role,
        full_name=full_name,
        teacher_id=teacher_id,
        is_not_student=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "initial_password": password,
        "message": f"Аккаунт сотрудника создан. Пароль: {password}",
    }


# ─── Логин ────────────────────────────────────────────────────────────────────

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # [FIX B-05] print заменён на logging
    username = form_data.username.strip()
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        # Единственное сообщение для обоих случаев — не раскрываем, что именно неверно
        logger.warning("Неудачная попытка входа для пользователя: %s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный ИИН или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Успешный вход: %s", username)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ─── Текущий пользователь ─────────────────────────────────────────────────────

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    full_name = current_user.full_name
    # Если full_name не задан, подставляем имя из записи преподавателя
    if not full_name and current_user.teacher_id:
        teacher = db.query(Teacher).filter(Teacher.teacher_id == current_user.teacher_id).first()
        if teacher:
            full_name = teacher.full_name
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        teacher_id=current_user.teacher_id,
        group_id=current_user.group_id,
        full_name=full_name,
        is_not_student=current_user.is_not_student,
    )
