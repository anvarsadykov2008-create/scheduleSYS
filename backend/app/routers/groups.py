from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from app.database import get_db
from app.models.models import Group, User
from app.dependencies import require_admin_or_dispatcher
from app.routers.audit import log_action
from app.schemas.schemas import (
    GroupCreate, GroupUpdate, GroupResponse,
)

router = APIRouter(prefix="/api/groups", tags=["Группы"])


@router.get("", response_model=List[GroupResponse])
def get_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()


@router.post("/import-csv")
def import_groups_csv(
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
        
        content = content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Файл пуст")
            
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
                
                if not row.get('name'):
                    errors.append(f"Строка {csv_reader.line_num}: Отсутствует обязательное поле name")
                    continue
                    
                if not row.get('specialty_id'):
                    errors.append(f"Строка {csv_reader.line_num}: Отсутствует обязательное поле specialty_id")
                    continue
                exists = db.query(Group).filter(Group.name == row['name']).first()
                if exists:
                    errors.append(f"Строка {csv_reader.line_num}: Группа '{row['name']}' уже существует, пропущена")
                    continue

                group = Group(
                    name=row.get('name', ''),
                    code=row.get('code', row.get('name', '')),
                    specialty_id=int(row['specialty_id']),
                    course_no=int(row['course_no']) if row.get('course_no') else 1,
                    student_count=int(row['student_count']) if row.get('student_count') else None,
                )
                db.add(group)
                db.flush()
                count += 1
            except Exception as e:
                db.rollback()
                errors.append(f"Ошибка в строке {csv_reader.line_num}: {str(e)}")
                continue

        db.commit()
        return {"message": f"Успешно импортировано {count} групп", "errors": errors}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group


@router.post("", response_model=GroupResponse, status_code=201)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    if not data.specialty_id:
        raise HTTPException(status_code=422, detail="specialty_id обязателен")
    group = Group(
        name=data.name,
        code=data.code or data.name,
        specialty_id=data.specialty_id,
        course_no=data.course_no or 1,
        student_count=data.student_count,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    log_action(db, current_user.id, "CREATE", "groups", int(group.group_id), {"name": group.name})
    return group


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    log_action(db, current_user.id, "UPDATE", "groups", group_id, {"name": group.name})
    return group


@router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    # [FIX B-08] Save data before delete
    audit_info = {"name": group.name}
    db.delete(group)
    db.commit()
    log_action(db, current_user.id, "DELETE", "groups", group_id, audit_info)
