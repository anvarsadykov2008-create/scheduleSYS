from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from app.database import get_db
from app.models.models import Classroom, User
from app.dependencies import require_admin_or_dispatcher
from app.routers.audit import log_action
from app.schemas.schemas import ClassroomCreate, ClassroomUpdate, ClassroomResponse

router = APIRouter(prefix="/api/classrooms", tags=["Аудитории"])


@router.get("", response_model=List[ClassroomResponse])
def get_classrooms(db: Session = Depends(get_db)):
    return db.query(Classroom).all()


@router.post("/import-csv")
def import_classrooms_csv(
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
                
                if not row.get('code') and not row.get('room_number'):
                    errors.append(f"Строка {csv_reader.line_num}: Отсутствует обязательное поле code")
                    continue
                    
                code = row.get('code') or row.get('room_number', '')
                if not row.get('room_type_id'):
                    errors.append(f"Строка {csv_reader.line_num}: Отсутствует обязательное поле room_type_id")
                    continue
                exists = db.query(Classroom).filter(Classroom.code == code).first()
                if exists:
                    errors.append(f"Строка {csv_reader.line_num}: Аудитория '{code}' уже существует, пропущена")
                    continue

                c = Classroom(
                    code=code,
                    name=row.get('name', code),
                    building=row.get('building', 'Главный корпус'),
                    floor=int(row['floor']) if row.get('floor') else None,
                    capacity=int(row['capacity']) if row.get('capacity') else None,
                    room_type_id=int(row['room_type_id']),
                )
                db.add(c)
                db.flush()
                count += 1
            except Exception as e:
                db.rollback()
                errors.append(f"Ошибка в строке {csv_reader.line_num}: {str(e)}")
                continue

        db.commit()
        return {"message": f"Успешно импортировано {count} аудиторий", "errors": errors}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.get("/{classroom_id}", response_model=ClassroomResponse)
def get_classroom(classroom_id: int, db: Session = Depends(get_db)):
    c = db.query(Classroom).filter(Classroom.room_id == classroom_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Аудитория не найдена")
    return c


@router.post("", response_model=ClassroomResponse, status_code=201)
def create_classroom(
    data: ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    if not data.room_type_id:
        raise HTTPException(status_code=422, detail="room_type_id обязателен")
    c = Classroom(
        code=data.code,
        name=data.name,
        building=data.building,
        floor=data.floor,
        capacity=data.capacity,
        room_type_id=data.room_type_id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    log_action(db, current_user.id, "CREATE", "classrooms", int(c.room_id), {"code": c.code, "name": c.name})
    return c


@router.put("/{classroom_id}", response_model=ClassroomResponse)
def update_classroom(
    classroom_id: int,
    data: ClassroomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    c = db.query(Classroom).filter(Classroom.room_id == classroom_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Аудитория не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(c, key, value)
    db.commit()
    db.refresh(c)
    log_action(db, current_user.id, "UPDATE", "classrooms", classroom_id, {"code": c.code, "name": c.name})
    return c


@router.delete("/{classroom_id}", status_code=204)
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    c = db.query(Classroom).filter(Classroom.room_id == classroom_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Аудитория не найдена")
    # [FIX B-08] Save data before delete
    audit_info = {"code": c.code}
    db.delete(c)
    db.commit()
    log_action(db, current_user.id, "DELETE", "classrooms", classroom_id, audit_info)
