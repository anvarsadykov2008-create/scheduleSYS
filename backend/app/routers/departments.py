import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_or_dispatcher
from app.models.models import Department, Specialty, User
from app.routers.audit import log_action
from app.schemas.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse, SpecialtyBase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/departments", tags=["Отделения"])


class SpecialtyOut(BaseModel):
    specialty_id: int
    department_id: int
    code: str
    name: str
    qualification: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ──── Departments ────

@router.get("", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()


@router.get("/{dept_id}", response_model=DepartmentResponse)
def get_department(dept_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.department_id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Отделение не найдено")
    return dept


@router.post("", response_model=DepartmentResponse, status_code=201)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    dept = Department(name=data.name, code=data.code)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_action(db, current_user.id, "CREATE", "departments", int(dept.department_id),
               {"name": dept.name})
    return dept


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    _auth: User = Depends(require_admin_or_dispatcher),
):
    dept = db.query(Department).filter(Department.department_id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Отделение не найдено")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}", status_code=204)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    dept = db.query(Department).filter(Department.department_id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Отделение не найдено")
    audit_info = {"name": dept.name}
    db.delete(dept)
    db.commit()
    log_action(db, current_user.id, "DELETE", "departments", dept_id, audit_info)


# ──── Specialties ────

@router.get("/specialties/all", response_model=List[SpecialtyOut])
def get_all_specialties(db: Session = Depends(get_db)):
    return db.query(Specialty).all()


@router.get("/{dept_id}/specialties", response_model=List[SpecialtyOut])
def get_specialties(dept_id: int, db: Session = Depends(get_db)):
    if not db.query(Department).filter(Department.department_id == dept_id).first():
        raise HTTPException(status_code=404, detail="Отделение не найдено")
    return db.query(Specialty).filter(Specialty.department_id == dept_id).all()


@router.post("/{dept_id}/specialties", response_model=SpecialtyOut, status_code=201)
def create_specialty(
    dept_id: int,
    data: SpecialtyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    if not db.query(Department).filter(Department.department_id == dept_id).first():
        raise HTTPException(status_code=404, detail="Отделение не найдено")
    spec = Specialty(department_id=dept_id, code=data.code, name=data.name)
    db.add(spec)
    db.commit()
    db.refresh(spec)
    log_action(db, current_user.id, "CREATE", "specialties", int(spec.specialty_id),
               {"name": spec.name, "dept_id": dept_id})
    return spec


@router.put("/{dept_id}/specialties/{spec_id}", response_model=SpecialtyOut)
def update_specialty(
    dept_id: int,
    spec_id: int,
    data: SpecialtyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    spec = db.query(Specialty).filter(
        Specialty.specialty_id == spec_id,
        Specialty.department_id == dept_id,
    ).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Специальность не найдена")
    spec.code = data.code
    spec.name = data.name
    db.commit()
    db.refresh(spec)
    return spec


@router.delete("/{dept_id}/specialties/{spec_id}", status_code=204)
def delete_specialty(
    dept_id: int,
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    spec = db.query(Specialty).filter(
        Specialty.specialty_id == spec_id,
        Specialty.department_id == dept_id,
    ).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Специальность не найдена")
    db.delete(spec)
    db.commit()
