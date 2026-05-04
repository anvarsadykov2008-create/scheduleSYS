from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from app.database import get_db
from app.models.models import Teacher, TeacherSubject, User, TimeSlot
from app.dependencies import require_admin_or_dispatcher
from sqlalchemy import text as sa_text
from app.routers.audit import log_action
from app.schemas.schemas import (
    TeacherCreate, TeacherUpdate, TeacherResponse,
    TeacherSubjectCreate, TeacherSubjectResponse
)

router = APIRouter(prefix="/api/teachers", tags=["Преподаватели"])


@router.get("", response_model=List[TeacherResponse])
def get_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()


@router.post("/import-csv")
def import_teachers_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Файл должен иметь расширение .csv")
    
    try:
        raw_content = file.file.read()
        try:
            content = raw_content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                content = raw_content.decode('windows-1251')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Неподдерживаемая кодировка файла. Используйте UTF-8 или Windows-1251.")
        
        # Очистка от пустых строк в начале/конце
        content = content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Файл пуст")
            
        # Определение разделителя (запятая или точка с запятой)
        try:
            dialect = csv.Sniffer().sniff(content[:1024])
        except csv.Error:
            dialect = csv.excel
            
        csv_reader = csv.DictReader(io.StringIO(content), dialect=dialect)
        
        count = 0
        errors = []
        
        for row in csv_reader:
            try:
                row = {k.strip() if k else k: v.strip() if v else v for k, v in row.items()}

                if not row.get('last_name') or not row.get('first_name'):
                    errors.append(f"Строка {csv_reader.line_num}: Отсутствуют обязательные поля last_name или first_name")
                    continue

                exists = db.query(Teacher).filter(
                    Teacher.last_name == row['last_name'],
                    Teacher.first_name == row['first_name'],
                ).first()
                if exists:
                    errors.append(f"Строка {csv_reader.line_num}: Преподаватель {row['last_name']} {row['first_name']} уже существует, пропущен")
                    continue

                t = Teacher(
                    last_name=row['last_name'],
                    first_name=row['first_name'],
                    middle_name=row.get('middle_name')
                )
                db.add(t)
                db.flush()
                count += 1
            except Exception as e:
                db.rollback()
                errors.append(f"Ошибка в строке {csv_reader.line_num}: {str(e)}")
                continue

        db.commit()
        return {"message": f"Успешно импортировано {count} преподавателей", "errors": errors}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.get("/{teacher_id}", response_model=TeacherResponse)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    t = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    return t


@router.post("", response_model=TeacherResponse, status_code=201)
def create_teacher(
    data: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    t = Teacher(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    log_action(db, current_user.id, "CREATE", "teachers", int(t.teacher_id), {"name": t.full_name})
    return t


@router.put("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    t = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(t, key, value)
    db.commit()
    db.refresh(t)
    log_action(db, current_user.id, "UPDATE", "teachers", teacher_id, {"name": t.full_name})
    return t


@router.delete("/{teacher_id}", status_code=204)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    t = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    # [FIX B-08] Save data before delete — object becomes detached after commit
    audit_info = {"name": t.last_name}
    db.delete(t)
    db.commit()
    log_action(db, current_user.id, "DELETE", "teachers", teacher_id, audit_info)


# ──── Назначения преподавателя на дисциплины ────

@router.get("/{teacher_id}/subjects", response_model=List[TeacherSubjectResponse])
def get_teacher_subjects(teacher_id: int, db: Session = Depends(get_db)):
    return db.query(TeacherSubject).filter(TeacherSubject.teacher_id == teacher_id).all()


@router.post("/{teacher_id}/subjects", response_model=TeacherSubjectResponse, status_code=201)
def assign_teacher_subject(
    teacher_id: int,
    data: TeacherSubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    ts = TeacherSubject(teacher_id=teacher_id, subject_id=data.subject_id)
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return ts


@router.delete("/{teacher_id}/subjects/{subject_id}", status_code=204)
def remove_teacher_subject(
    teacher_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    ts = db.query(TeacherSubject).filter(
        TeacherSubject.teacher_id == teacher_id,
        TeacherSubject.subject_id == subject_id,
    ).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    db.delete(ts)
    db.commit()


# ──── Недоступные дни преподавателя ────

@router.get("/{teacher_id}/unavailable-days")
def get_unavailable_days(
    teacher_id: int,
    semester_id: int,
    db: Session = Depends(get_db),
):
    """Возвращает список дней недели (1-7), в которые преподаватель недоступен."""
    rows = db.execute(sa_text(
        "SELECT DISTINCT ts.day_of_week "
        "FROM teacher_unavailability tu "
        "JOIN time_slots ts ON ts.id = tu.time_slot_id "
        "WHERE tu.teacher_id = :tid AND tu.academic_period_id = :pid AND tu.is_hard = true"
    ), {"tid": teacher_id, "pid": semester_id}).fetchall()
    return {"unavailable_days": [r[0] for r in rows]}


@router.put("/{teacher_id}/unavailable-days")
def set_unavailable_days(
    teacher_id: int,
    semester_id: int,
    days: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    """
    Устанавливает недоступные дни недели (1=Пн … 7=Вс).
    Для каждого дня блокируются все слоты этого дня.
    """
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    # Удаляем старые записи
    db.execute(sa_text(
        "DELETE FROM teacher_unavailability "
        "WHERE teacher_id = :tid AND academic_period_id = :pid AND is_hard = true"
    ), {"tid": teacher_id, "pid": semester_id})

    # Получаем все слоты для каждого указанного дня
    if days:
        slots = db.query(TimeSlot).filter(TimeSlot.day_of_week.in_(days)).all()
        for slot in slots:
            db.execute(sa_text(
                "INSERT INTO teacher_unavailability "
                "(teacher_id, academic_period_id, time_slot_id, is_hard) "
                "VALUES (:tid, :pid, :sid, true)"
            ), {"tid": teacher_id, "pid": semester_id, "sid": int(slot.time_slot_id)})

    db.commit()
    return {"unavailable_days": days}

