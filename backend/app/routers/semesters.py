"""
semesters / academic_years router — таблицы могут отсутствовать в текущей схеме.
В текущем проекте семестры хранятся в таблице `academic_periods`.
Этот роутер отдаёт совместимый формат для фронтенда (/api/semesters, /api/academic_years).
"""
from fastapi import APIRouter, Depends
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import AcademicPeriod
from app.schemas.schemas import AcademicYearResponse, SemesterResponse

router = APIRouter(prefix="/api", tags=["Учебные годы и семестры"])

def _build_year_index(periods: List[AcademicPeriod]) -> Tuple[Dict[str, int], Dict[str, Dict]]:
    """
    Возвращает:
    - year_to_id: mapping академ.года (строка) -> стабильный int id (по сортировке)
    - year_meta: mapping академ.года -> {start_date,end_date}
    """
    years = sorted({p.academic_year for p in periods if p.academic_year})
    year_to_id = {y: i + 1 for i, y in enumerate(years)}
    meta: Dict[str, Dict] = {y: {"start_date": None, "end_date": None} for y in years}
    for p in periods:
        y = p.academic_year
        if not y or y not in meta:
            continue
        sd = p.start_date
        ed = p.end_date
        if sd and (meta[y]["start_date"] is None or sd < meta[y]["start_date"]):
            meta[y]["start_date"] = sd
        if ed and (meta[y]["end_date"] is None or ed > meta[y]["end_date"]):
            meta[y]["end_date"] = ed
    return year_to_id, meta


@router.get("/academic_years", response_model=List[AcademicYearResponse])
def get_academic_years(db: Session = Depends(get_db)):
    periods = db.query(AcademicPeriod).all()
    year_to_id, meta = _build_year_index(periods)
    return [
        {
            "id": year_id,
            "name": year,
            "start_date": meta[year]["start_date"],
            "end_date": meta[year]["end_date"],
        }
        for year, year_id in year_to_id.items()
    ]

@router.get("/academic_years/", response_model=List[AcademicYearResponse])
def get_academic_years_slash(db: Session = Depends(get_db)):
    return get_academic_years(db)


@router.get("/semesters", response_model=List[SemesterResponse])
def get_semesters(db: Session = Depends(get_db)):
    periods = db.query(AcademicPeriod).all()
    year_to_id, meta = _build_year_index(periods)

    result = []
    for p in periods:
        year = p.academic_year
        if not year or year not in year_to_id:
            continue
        result.append(
            {
                "id": int(p.academic_period_id),
                "academic_year_id": year_to_id[year],
                "number": int(p.term_no) if p.term_no is not None else 1,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "academic_year": {
                    "id": year_to_id[year],
                    "name": year,
                    "start_date": meta[year]["start_date"],
                    "end_date": meta[year]["end_date"],
                },
            }
        )

    result.sort(key=lambda s: (s["academic_year"]["name"], s["number"]))
    return result

@router.get("/semesters/", response_model=List[SemesterResponse])
def get_semesters_slash(db: Session = Depends(get_db)):
    return get_semesters(db)
