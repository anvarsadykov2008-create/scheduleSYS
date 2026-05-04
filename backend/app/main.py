"""
Точка входа FastAPI-приложения.
"""

import logging
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, get_db
from app.models.models import *  # noqa: F401, F403 — регистрация моделей
from app.config import CORS_ORIGINS
from app.dependencies import require_authenticated

from app.routers import (
    academic_periods,
    audit,
    auth,
    classrooms,
    departments,
    groups,
    hour_grid,
    lesson_types,
    reports,
    schedule,
    semesters,
    settings,
    subjects,
    student_dashboard,
    teacher_dashboard,
    teacher_rooms,
    teachers,
    time_slots,
    users,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Создание таблиц (dev-режим; в production используем Alembic / SQL-патч)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="scheduleSYS API",
    description="Система автоматизированной генерации и публикации расписания колледжа",
    version="1.0.0",
)

# [FIX S-01] CORS: конкретные origins из .env/config, а не wildcard "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Роутеры ────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(groups.router)
app.include_router(teachers.router)
app.include_router(classrooms.router)
app.include_router(subjects.router)
app.include_router(semesters.router)
app.include_router(time_slots.router)
app.include_router(hour_grid.router)        # [FIX F-02]
app.include_router(academic_periods.router)
app.include_router(schedule.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(lesson_types.router)
app.include_router(settings.router)
app.include_router(reports.router)
app.include_router(student_dashboard.router)
app.include_router(teacher_dashboard.router)
app.include_router(teacher_rooms.router)


# ─── Startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
def seed_default_users():
    """
    Создаёт дефолтного admin при первом запуске (только если его нет в БД).
    Пароль читается из переменной окружения ADMIN_PASSWORD (default: admin123).
    [FIX B-05] Заменён print() на logging.
    """
    from app.auth import get_password_hash
    from app.models.models import User, UserRole

    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    if admin_password == "admin123":
        logger.warning(
            "ADMIN_PASSWORD не задан в .env — используется дефолтный пароль 'admin123'. "
            "Смените его перед развёртыванием в production."
        )

    db = next(get_db())
    try:
        if not db.query(User).filter(User.username == "990101000001").first():
            db.add(User(
                username="990101000001",
                password_hash=get_password_hash(admin_password),
                role=UserRole.ADMIN,
                full_name="Администратор",
            ))
            db.commit()
            logger.info("Создан дефолтный администратор (ИИН: 990101000001)")
    except Exception as exc:
        db.rollback()
        logger.error("Ошибка при создании администратора: %s", exc)
    finally:
        db.close()


# ─── API-эндпоинты ──────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "scheduleSYS API работает"}


# [FIX B-09] Добавлена авторизация — статистика доступна только авторизованным пользователям
@app.get("/api/stats", tags=["System"])
def get_stats(
    db=Depends(get_db),
    _auth=Depends(require_authenticated),
):
    """Быстрая статистика для дашборда."""
    from app.models.models import Classroom, Curriculum, Group, Subject, Teacher
    return {
        "groups_count": db.query(Group).count(),
        "teachers_count": db.query(Teacher).count(),
        "classrooms_count": db.query(Classroom).count(),
        "subjects_count": db.query(Subject).count(),
        "workload_entries_count": db.query(Curriculum).count(),
    }


# [FIX B-01] Эндпоинт /api/seed-users УДАЛЁН.
#            Он позволял ЛЮБОМУ сбросить пароль администратора без авторизации.
#            Для восстановления admin используйте скрипт insert_admin.py напрямую в БД.


# ─── Раздача статического фронтенда (React /dist) ───────────────────────────
frontend_dist_path = os.path.join(os.path.dirname(__file__), "../../frontend/dist")

if os.path.isdir(frontend_dist_path):
    app.mount("/assets", StaticFiles(directory=f"{frontend_dist_path}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(_request: Request, full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API Route Not Found")

        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
else:
    logger.warning("Frontend 'dist' не найден. Статические файлы не будут раздаваться.")
