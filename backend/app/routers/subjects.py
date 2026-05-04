from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from app.database import get_db
from app.models.models import Subject, User
from app.dependencies import require_admin_or_dispatcher
from app.routers.audit import log_action
from app.schemas.schemas import SubjectCreate, SubjectUpdate, SubjectResponse

router = APIRouter(prefix="/api/subjects", tags=["Дисциплины"])


@router.get("", response_model=List[SubjectResponse])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/import-csv")
def import_subjects_csv(
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
                    
                exists = db.query(Subject).filter(Subject.name == row['name']).first()
                if exists:
                    errors.append(f"Строка {csv_reader.line_num}: Дисциплина '{row['name']}' уже существует, пропущена")
                    continue

                s = Subject(name=row['name'])
                db.add(s)
                db.flush()
                count += 1
            except Exception as e:
                db.rollback()
                errors.append(f"Ошибка в строке {csv_reader.line_num}: {str(e)}")
                continue

        db.commit()
        return {"message": f"Успешно импортировано {count} дисциплин", "errors": errors}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    s = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    return s


@router.post("", response_model=SubjectResponse, status_code=201)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_dispatcher)):
    s = Subject(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    log_action(db, current_user.id, "CREATE", "subjects", int(s.subject_id), {"name": s.name})
    return s


@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_dispatcher)):
    s = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    log_action(db, current_user.id, "UPDATE", "subjects", subject_id, {"name": s.name})
    return s


@router.delete("/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_dispatcher)):
    s = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    # [FIX B-08] Save data before delete
    audit_info = {"name": s.name}
    db.delete(s)
    db.commit()
    log_action(db, current_user.id, "DELETE", "subjects", subject_id, audit_info)
