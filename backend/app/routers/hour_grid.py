import io
import logging
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_or_dispatcher
from app.models.models import AcademicPeriod, Curriculum, Group, Subject, Teacher, TeacherSubject, User
from app.routers.audit import log_action
from app.schemas.schemas import HourGridCreate, HourGridResponse, HourGridUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hour-grid", tags=["Сетка часов / Учебный план"])


@router.get("", response_model=List[HourGridResponse])
def get_hour_grids(
    group_id: Optional[int] = None,
    # [FIX] Фильтр по academic_period_id (старый semester не существует в модели)
    academic_period_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Curriculum)
    if group_id:
        query = query.filter(Curriculum.group_id == group_id)
    if academic_period_id:
        query = query.filter(Curriculum.academic_period_id == academic_period_id)
    return query.all()


@router.post("", response_model=HourGridResponse, status_code=201)
def create_hour_grid(
    data: HourGridCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    hg = Curriculum(**data.model_dump())
    db.add(hg)
    db.commit()
    db.refresh(hg)
    log_action(db, current_user.id, "CREATE", "hour_grid", hg.group_subject_load_id,
               {"group_id": hg.group_id, "subject_id": hg.subject_id})
    return hg


@router.put("/{hg_id}", response_model=HourGridResponse)
def update_hour_grid(
    hg_id: int,
    data: HourGridUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    hg = db.query(Curriculum).filter(Curriculum.group_subject_load_id == hg_id).first()
    if not hg:
        raise HTTPException(status_code=404, detail="Запись учебного плана не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(hg, key, value)
    db.commit()
    db.refresh(hg)
    return hg


@router.delete("/{hg_id}", status_code=204)
def delete_hour_grid(
    hg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    hg = db.query(Curriculum).filter(Curriculum.group_subject_load_id == hg_id).first()
    if not hg:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    # [FIX B-08] Сохраняем данные ДО удаления — после commit объект detached
    audit_info = {"group_id": hg.group_id, "subject_id": hg.subject_id,
                  "academic_period_id": hg.academic_period_id}
    db.delete(hg)
    db.commit()
    log_action(db, current_user.id, "DELETE", "hour_grid", hg_id, audit_info)


# ──── Импорт из docx / xls ────────────────────────────────────────────────────

def _parse_hours(val: str) -> float:
    """'48', '48+12', '96/48' → float сумма первого числа."""
    if not val:
        return 0.0
    val = val.strip().replace(',', '.')
    # берём только первый числовой блок
    m = re.match(r'[\d.]+', val)
    return float(m.group()) if m else 0.0


def _find_or_create_subject(db: Session, name: str) -> Subject:
    name = name.strip()[:200]  # ограничение колонки VARCHAR(200)
    subj = db.query(Subject).filter(Subject.name.ilike(name)).first()
    if not subj:
        code = ''.join(w[0].upper() for w in name.split()[:4]) or name[:8]
        code = code[:50]  # VARCHAR(50)
        existing = db.query(Subject).filter(Subject.code == code).first()
        if existing:
            suffix = str(db.query(Subject).count())
            code = code[:50 - len(suffix)] + suffix
        subj = Subject(name=name, code=code, subject_kind='standard', is_active=True)
        db.add(subj)
        db.flush()
    return subj


def _find_teacher_by_lastname(db: Session, raw: str) -> Optional[Teacher]:
    """Пытается найти преподавателя по фамилии из строки вида 'Иванов И.И.(48)'."""
    if not raw:
        return None
    last = raw.strip().split()[0]
    return db.query(Teacher).filter(Teacher.last_name.ilike(last)).first()


def _parse_docx(content: bytes) -> List[dict]:
    import docx
    doc = docx.Document(io.BytesIO(content))
    rows_out = []
    current_group = None

    # Обходим элементы документа в порядке появления
    from docx.oxml.ns import qn
    body = doc.element.body
    for child in body:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            text = child.text_content() if hasattr(child, 'text_content') else ''.join(
                r.text for r in child.findall('.//' + '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            )
            text = text.strip()
            # Ищем название группы в параграфах
            m = re.search(r'((?:тоб[ыа]|группа|group)[:\s]+)?([А-ЯA-Z][А-ЯA-Zа-яa-z]*[\s\-]+\d[\-\d]*(?:[\s\-]+[ққ]\.?б\.?)?)', text, re.IGNORECASE)
            if not m:
                # простой паттерн: «ТК 2-1», «БД 1-1», «WEB 3-5»
                m2 = re.search(r'\b([А-ЯA-Z]{2,}[\s\-]+\d[\-\d\s]*)\b', text)
                if m2:
                    candidate = m2.group(1).strip()
                    if 2 <= len(candidate.split()) <= 3:
                        current_group = candidate
            else:
                current_group = m.group(2).strip()
        elif tag == 'tbl':
            # Находим соответствующую таблицу через python-docx
            from docx.table import Table
            tbl_obj = Table(child, doc)
            for row in tbl_obj.rows:
                cells = [c.text.strip() for c in row.cells]
                if len(cells) < 7:
                    continue
                # Пропускаем заголовки и модульные строки (нет числовых часов)
                name_cell = cells[1] if len(cells) > 1 else ''
                if not name_cell or name_cell in ('Пәндер/модульдер', 'Дисциплины/модули',
                                                   'Модуль/Дисциплины', 'Пәндер', 'Дисциплины/модули'):
                    continue
                # Колонки: [code, name, s1_theory, s1_practice, s2_theory, s2_practice, exams, total, teacher]
                s1t = _parse_hours(cells[2]) if len(cells) > 2 else 0
                s1p = _parse_hours(cells[3]) if len(cells) > 3 else 0
                s2t = _parse_hours(cells[4]) if len(cells) > 4 else 0
                s2p = _parse_hours(cells[5]) if len(cells) > 5 else 0
                total = _parse_hours(cells[7]) if len(cells) > 7 else s1t + s1p + s2t + s2p
                teacher_raw = cells[8] if len(cells) > 8 else ''

                sem1_hours = s1t + s1p
                sem2_hours = s2t + s2p

                if total == 0 and sem1_hours == 0 and sem2_hours == 0:
                    continue
                if not name_cell or re.match(r'^(Модуль|Module|ЖБП\d*$|ООД\d*$|БМ\d*$|КМ\d*$|ПМ\d*$|ЖММ\d*$)', name_cell):
                    continue

                rows_out.append({
                    'group_name': current_group,
                    'subject_name': name_cell,
                    'sem1_hours': sem1_hours,
                    'sem2_hours': sem2_hours,
                    'total_hours': total,
                    'teacher_raw': teacher_raw,
                })
    return rows_out


def _parse_xls(content: bytes) -> List[dict]:
    import xlrd
    wb = xlrd.open_workbook(file_contents=content)
    rows_out = []
    current_group = None
    for sheet in wb.sheets():
        for r in range(sheet.nrows):
            row = [str(sheet.cell_value(r, c)).strip() for c in range(sheet.ncols)]
            # Поиск группы в первом столбце
            if row and re.search(r'\b([А-ЯA-Z]{2,}[\s\-]+\d[\-\d]*)\b', row[0]):
                current_group = re.search(r'\b([А-ЯA-Z]{2,}[\s\-]+\d[\-\d]*)\b', row[0]).group(1)
                continue
            if len(row) < 8:
                continue
            name_cell = row[2] if len(row) > 2 else ''
            if not name_cell or name_cell in ('Пәндер', 'Дисциплины/модули', 'теория', 'Теория'):
                continue
            s1t = _parse_hours(row[3]) if len(row) > 3 else 0
            s1p = _parse_hours(row[4]) if len(row) > 4 else 0
            s2t = _parse_hours(row[5]) if len(row) > 5 else 0
            s2p = _parse_hours(row[6]) if len(row) > 6 else 0
            total = _parse_hours(row[8]) if len(row) > 8 else s1t + s1p + s2t + s2p
            teacher_raw = row[9] if len(row) > 9 else ''
            sem1_hours = s1t + s1p
            sem2_hours = s2t + s2p
            if total == 0 and sem1_hours == 0 and sem2_hours == 0:
                continue
            rows_out.append({
                'group_name': current_group,
                'subject_name': name_cell,
                'sem1_hours': sem1_hours,
                'sem2_hours': sem2_hours,
                'total_hours': total,
                'teacher_raw': teacher_raw,
            })
    return rows_out


@router.post("/import-file")
def import_hour_grid_file(
    file: UploadFile = File(...),
    academic_period_id: int = 5,
    weeks: int = 18,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_dispatcher),
):
    """
    Импортирует сетку часов из файла .docx или .xls/.xlsx.
    Автоматически создаёт предметы если не найдены.
    Параметры:
      academic_period_id — семестр для записи (по умолчанию 5)
      weeks — количество учебных недель (по умолчанию 18)
    """
    content = file.file.read()
    fname = file.filename.lower()

    try:
        if fname.endswith('.docx'):
            parsed = _parse_docx(content)
        elif fname.endswith('.xls'):
            parsed = _parse_xls(content)
        elif fname.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            parsed = []
            current_group_xlsx = None
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    cells = [str(c).strip() if c is not None else '' for c in row]
                    if len(cells) < 2:
                        continue
                    # Detect group header in first column (same pattern as xls parser)
                    if cells[0] and re.search(r'\b([А-ЯA-Z]{2,}[\s\-]+\d[\-\d]*)\b', cells[0]):
                        m = re.search(r'\b([А-ЯA-Z]{2,}[\s\-]+\d[\-\d]*)\b', cells[0])
                        current_group_xlsx = m.group(1)
                        continue
                    if len(cells) < 8:
                        continue
                    name_cell = cells[2] if len(cells) > 2 else ''
                    if not name_cell:
                        continue
                    s1t = _parse_hours(cells[3])
                    s1p = _parse_hours(cells[4])
                    s2t = _parse_hours(cells[5])
                    s2p = _parse_hours(cells[6])
                    total = _parse_hours(cells[8]) if len(cells) > 8 else s1t+s1p+s2t+s2p
                    if total == 0:
                        continue
                    parsed.append({
                        'group_name': current_group_xlsx,
                        'subject_name': name_cell,
                        'sem1_hours': s1t + s1p,
                        'sem2_hours': s2t + s2p,
                        'total_hours': total,
                        'teacher_raw': cells[9] if len(cells) > 9 else '',
                    })
        else:
            raise HTTPException(status_code=400, detail="Поддерживаются файлы .docx, .xls, .xlsx")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга файла: {e}")

    # Получаем все группы для поиска по имени
    all_groups = db.query(Group).all()

    def _norm(s: str) -> str:
        return re.sub(r'\s+', '', s).lower()

    group_map = {_norm(g.name): g for g in all_groups}
    group_map.update({_norm(g.code): g for g in all_groups})

    created = 0
    skipped = 0
    errors = []
    added_ts: set = set()   # (teacher_id, subject_id) — уже добавлено в этом импорте
    added_hg: set = set()  # (group_id, subject_id, period_id) — дубликаты curriculum

    period = db.query(AcademicPeriod).filter(AcademicPeriod.academic_period_id == academic_period_id).first()
    use_sem2 = period and period.term_no == 2

    for item in parsed:
        subj_name = item['subject_name']
        # Пропускаем мусорные строки
        if not subj_name or len(subj_name) < 3:
            continue
        if re.match(r'^(Модуль|Module|Итого|Барлығы|Всего|№|р/с|ЖБП|ООД|БМ|КМ|ПМ|ЖММ)\b', subj_name, re.I):
            continue

        sem_hours = (item['sem2_hours'] or item['total_hours']) if use_sem2 else (item['sem1_hours'] or item['total_hours'])

        if sem_hours == 0 or sem_hours > 500:  # >500 — итоговая/суммарная строка
            skipped += 1
            continue

        planned_weekly = round(sem_hours / weeks, 2)

        # Ищем предмет
        try:
            subj = _find_or_create_subject(db, subj_name)
        except Exception as e:
            db.rollback()
            errors.append(f"Предмет '{subj_name}': {e}")
            continue

        # Ищем преподавателя
        teacher = _find_teacher_by_lastname(db, item.get('teacher_raw', ''))

        # Ищем группу
        group_name = item.get('group_name')
        group = None
        if group_name:
            gn = _norm(group_name)
            group = group_map.get(gn)
            if not group:
                # нечёткий поиск — первые 4 символа
                for k, g in group_map.items():
                    if k[:4] == gn[:4]:
                        group = g
                        break
        if not group and group_id:
            # Fallback: use explicitly provided group_id
            group = next((g for g in all_groups if g.group_id == group_id), None)

        if not group:
            skipped += 1
            errors.append(f"Группа не найдена для '{subj_name}' (group_name={group_name!r}) — пропущено")
            continue

        # Проверяем дубликат
        hg_key = (int(group.group_id), int(subj.subject_id), academic_period_id)
        if hg_key in added_hg:
            skipped += 1
            continue

        exists = db.query(Curriculum).filter(
            Curriculum.group_id == group.group_id,
            Curriculum.subject_id == subj.subject_id,
            Curriculum.academic_period_id == academic_period_id,
        ).first()
        if exists:
            skipped += 1
            added_hg.add(hg_key)
            continue

        added_hg.add(hg_key)

        # Создаём запись
        hg = Curriculum(
            group_id=int(group.group_id),
            subject_id=int(subj.subject_id),
            lesson_type_id=1,
            academic_period_id=academic_period_id,
            planned_weekly_hours=planned_weekly,
            total_hours=float(sem_hours),
            preferred_teacher_id=int(teacher.teacher_id) if teacher else None,
            is_mandatory=True,
            notes=f"Импорт: {file.filename}",
        )
        db.add(hg)
        created += 1

        # Связываем преподавателя с предметом если не связан
        if teacher:
            ts_key = (int(teacher.teacher_id), int(subj.subject_id))
            if ts_key not in added_ts:
                ts_exists = db.query(TeacherSubject).filter(
                    TeacherSubject.teacher_id == teacher.teacher_id,
                    TeacherSubject.subject_id == subj.subject_id,
                ).first()
                if not ts_exists:
                    db.add(TeacherSubject(
                        teacher_id=ts_key[0],
                        subject_id=ts_key[1],
                        lesson_type_id=1,
                        is_active=True,
                    ))
                added_ts.add(ts_key)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {e}")

    log_action(db, current_user.id, "IMPORT", "hour_grid", 0,
               {"file": file.filename, "created": created, "skipped": skipped})

    return {
        "message": f"Импортировано {created} записей, пропущено {skipped}",
        "created": created,
        "skipped": skipped,
        "errors": errors[:20],
    }
