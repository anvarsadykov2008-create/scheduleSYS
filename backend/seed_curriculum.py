"""
seed_curriculum.py - Заполнение teacher_subjects и group_subject_load
из документов в папке 'База данных'.

Запуск: cd backend && python seed_curriculum.py
"""

import sys, os, re, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import xlrd
from sqlalchemy.orm import Session
from app.database import engine
from app.models.models import (
    Teacher, Subject, Group, AcademicPeriod, LessonType,
    TeacherSubject, Curriculum
)

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'База данных')

# ─── Загрузка справочников из БД ────────────────────────────────────────────

def load_maps(db):
    # teacher: last_name -> teacher_id (+ aliases)
    teachers_raw = db.query(Teacher).all()
    t_map = {}
    for t in teachers_raw:
        key = t.last_name.lower().strip()
        t_map[key] = t.teacher_id

    # subject: name (lower) -> subject_id
    subjects_raw = db.query(Subject).all()
    s_map = {s.name.lower().strip(): s.subject_id for s in subjects_raw}

    # group: code (upper, no spaces) -> group_id
    groups_raw = db.query(Group).all()
    g_map = {}
    for g in groups_raw:
        key = g.code.upper().replace(' ', '').replace('-', '')
        g_map[key] = g.group_id
        # Also store normalized version
        g_map[g.code] = g.group_id

    # lesson types
    lt_raw = db.query(LessonType).all()
    lt_map = {lt.code: lt.lesson_type_id for lt in lt_raw}

    # academic periods
    ap_raw = db.query(AcademicPeriod).all()
    ap_map = {ap.code: ap.academic_period_id for ap in ap_raw}

    return t_map, s_map, g_map, lt_map, ap_map


# ─── Нормализация ────────────────────────────────────────────────────────────

SUBJECT_ALIASES = {
    'математика': 'Высшая математика',
    'алгебра': 'Высшая математика',
    'информатика': 'Информатика',
    'казахский язык': 'Казахский язык',
    'казахский язык и литература': 'Казахский язык',
    'казах тілі': 'Казахский язык',
    'қазақ тілі': 'Казахский язык',
    'казах адебиеті': 'Казахская литература',
    'қазақ әдебиеті': 'Казахская литература',
    'русский язык': 'Русский язык',
    'русский язык и литература': 'Русский язык',
    'орыс тілі және әдебиеті': 'Русский язык',
    'русская литература': 'Русская литература',
    'орыс тілі': 'Русский язык',
    'иностранный язык': 'Иностранный язык',
    'шет тілі': 'Иностранный язык',
    'английский язык': 'Иностранный язык',
    'история казахстана': 'История Казахстана',
    'қазақстан тарихы': 'История Казахстана',
    'физическая культура': 'Физическая культура',
    'дене тәрбиесі': 'Физическая культура',
    'начальная военная и технологическая подготовка': 'НВП',
    'алғашқы әскери және технологиялық дайындық': 'НВП',
    'нвтп': 'НВП',
    'аәтд': 'НВП',
    'биология': 'Биология',
    'всемирная история': 'Всемирная история',
    'дүниежүзілік тарихы': 'Всемирная история',
    'география': 'География',
    'физика': 'Физика',
    'химия': 'Химия',
    'веб-порталы': 'Веб-порталы',
    'веб порталы': 'Веб-порталы',
    'sql': 'SQL',
    'базы данных': 'Базы данных',
    'бухгалтерский учет': 'Бухгалтерский учет',
    'бухгалтерский учёт': 'Бухгалтерский учет',
    'бухгалтерский учет негіздері': 'Бухгалтерский учет негіздері',
    'аудит': 'Аудит',
    'банковские операции': 'Банковские операции',
    'банк операциялары': 'Банковские операции',
    'экономика': 'Экономика',
    'менеджмент': 'Менеджмент',
    'маркетинг': 'Маркетинг',
    '1с': '1С',
    'big data': 'Big Data',
    'cms': 'CMS',
    'визуальное программирование': 'Визуальное программирование',
    'верстка': 'Верстка портфолио',
}

def normalize_subject(raw_name, s_map):
    """Find subject_id by name, trying various normalizations."""
    if not raw_name:
        return None
    name = raw_name.strip().lower()
    # Skip module headers / totals
    skip_words = ['модуль', 'барлығы', 'итого', 'всего', 'аттестация',
                  'аттестаттау', 'консультац', 'факультатив', 'аралық',
                  'промежуточн', 'оқу дала', 'учебные полевые', 'нвтп - учебные',
                  'аәтд-оқу', 'он 2.', 'ро 2.', 'директор', 'колледж', 'барлығы:']
    for sw in skip_words:
        if sw in name:
            return None

    # Try alias first
    if name in SUBJECT_ALIASES:
        alias = SUBJECT_ALIASES[name].lower()
        if alias in s_map:
            return s_map[alias]

    # Direct match
    if name in s_map:
        return s_map[name]

    # Partial match: subject name starts with raw_name
    for sname, sid in s_map.items():
        if sname.startswith(name[:10]) or name.startswith(sname[:10]):
            return sid

    return None


def normalize_teacher_name(raw, t_map):
    """Extract last name and find teacher_id."""
    if not raw:
        return None
    # Remove numbers and dots-as-numbers
    cleaned = re.sub(r'\b\d+[\.,]?\d*\b', '', raw).strip()
    # Take first word as last name
    parts = cleaned.split()
    if not parts:
        return None
    last = parts[0].strip('.,').lower()
    if last in t_map:
        return t_map[last]
    # Try fuzzy: first 5 chars
    for tname, tid in t_map.items():
        if len(last) >= 5 and tname.startswith(last[:5]):
            return tid
    return None


def parse_teachers_from_cell(cell_val, t_map):
    """Return list of teacher_ids from a teachers cell like 'Калабаева Г.К.120, Иванов А.Б.'"""
    if not cell_val or str(cell_val).strip() in ('', 'Вакансия', 'вакансия'):
        return []
    raw = str(cell_val)
    # Split on comma or slash
    parts = re.split(r'[,/]', raw)
    result = []
    seen = set()
    for part in parts:
        part = part.strip()
        if not part or 'вакансия' in part.lower():
            continue
        tid = normalize_teacher_name(part, t_map)
        if tid and tid not in seen:
            result.append(tid)
            seen.add(tid)
    return result


def normalize_group_code(raw, g_map):
    """БД 1-1 қ.б. тобы -> БД1-1"""
    if not raw:
        return None
    # Normalize em-dash/en-dash to hyphen
    raw = raw.replace('\u2013', '-').replace('\u2014', '-')
    # Remove Kazakh/Russian suffixes and garbage
    raw = re.sub(r'(?:тобы?|тобі|группа)', '', raw, flags=re.I)
    raw = re.sub(r'(?:қ\.?б\.?|р\.?б\.?|к\.?б\.?)', '', raw, flags=re.I)
    # Keep only Cyrillic letters, Latin letters, digits, dash
    raw = re.sub(r'[^А-ЯҚҒӘІҢҮҺа-яқғәіңүһA-Za-z0-9\-]', '', raw)
    raw = raw.strip().upper()
    # Try direct match (code with dash, e.g. "БД1-1")
    if raw in g_map:
        return g_map[raw]
    # Try without dash: БД11 -> look for БД1-1
    m = re.match(r'^([А-ЯA-Z]+)(\d)(\d)$', raw)
    if m:
        candidate = f"{m.group(1)}{m.group(2)}-{m.group(3)}"
        if candidate in g_map:
            return g_map[candidate]
    # Try БД1-3Р or similar with trailing garbage
    raw3 = re.sub(r'[ҚРРКБ]+$', '', raw)
    if raw3 != raw and raw3 in g_map:
        return g_map[raw3]
    m2 = re.match(r'^([А-ЯA-Z]+)(\d)(\d)[А-ЯA-Z]*$', raw)
    if m2:
        candidate = f"{m2.group(1)}{m2.group(2)}-{m2.group(3)}"
        if candidate in g_map:
            return g_map[candidate]
    return None


# ─── Парсинг XLS файлов ──────────────────────────────────────────────────────

def parse_hours_cell(val):
    """Parse hours like '72.0', '24/24', '48/48' -> float sum."""
    val = str(val).strip()
    if not val:
        return 0.0
    if '/' in val:
        try:
            return sum(float(p) for p in val.split('/') if p.strip())
        except:
            return 0.0
    try:
        return float(val)
    except:
        return 0.0


def detect_xls_cols(sh):
    """
    Detect column layout by finding the header row.
    Returns dict: {subj_col, sem1t_col, sem1p_col, sem2t_col, sem2p_col, total_col, teacher_col}
    """
    for row in range(min(20, sh.nrows)):
        for c in range(sh.ncols):
            v = str(sh.cell_value(row, c)).strip().lower()
            if v in ('барлығы', 'барлыгы', 'всего', 'итого'):
                total_col = c
                # Teacher col is usually total_col + 1
                teacher_col = total_col + 1 if total_col + 1 < sh.ncols else total_col
                # Subject col: look for 'пән' or 'дисциплин' in same row
                subj_col = 2  # default
                for sc in range(sh.ncols):
                    sv = str(sh.cell_value(row, sc)).strip().lower()
                    if any(kw in sv for kw in ('пән', 'дисципл', 'атауы', 'наименован')):
                        subj_col = sc
                        break
                return {
                    'subj_col': subj_col,
                    'sem1t': subj_col + 1,
                    'sem1p': subj_col + 2,
                    'sem2t': subj_col + 3,
                    'sem2p': subj_col + 4,
                    'total_col': total_col,
                    'teacher_col': teacher_col,
                }
    # Default: first file layout (subj=col2, total=col8, teacher=col9)
    return {'subj_col': 2, 'sem1t': 3, 'sem1p': 4, 'sem2t': 5, 'sem2p': 6,
            'total_col': 8, 'teacher_col': 9}


def parse_xls_file(filepath, t_map, s_map, g_map):
    """Returns list of {group_id, subject_id, teacher_ids, total_hours, sem1_hours, sem2_hours}"""
    records = []
    try:
        wb = xlrd.open_workbook(filepath)
    except Exception as e:
        print(f"  Cannot open {filepath}: {e}")
        return records

    GROUP_PATTERN = re.compile(
        r'((?:БД|WEB|БУХ|ОП|ТП|ТК|ТХ|РПО|ИС)\s*[\d]+[\s\-\u2013\u2014]+[\d]+)',
        re.I
    )

    for sname in wb.sheet_names():
        if 'свод' in sname.lower():
            continue
        sh = wb.sheet_by_name(sname)
        cols = detect_xls_cols(sh)
        sc = cols['subj_col']
        tc = cols['teacher_col']
        totc = cols['total_col']
        current_group_id = None
        # For "ОН X.X" rows: carry over subject name from next human-readable row
        pending_record = None  # dict to be completed when we find readable name

        for row in range(sh.nrows):
            # ── Group detection (scan all columns) ──────────────────
            for c in range(min(max(sc + 1, 3), sh.ncols)):
                val = str(sh.cell_value(row, c)).strip()
                if not val:
                    continue
                m = GROUP_PATTERN.search(val)
                if m:
                    gid = normalize_group_code(m.group(1), g_map)
                    if gid:
                        current_group_id = gid
                        pending_record = None
                        break

            if not current_group_id:
                continue

            # ── Subject + hours extraction ───────────────────────────
            subj_raw = str(sh.cell_value(row, sc)).strip() if sh.ncols > sc else ''
            total_h  = parse_hours_cell(sh.cell_value(row, totc)) if sh.ncols > totc else 0.0
            sem1_h   = (parse_hours_cell(sh.cell_value(row, cols['sem1t'])) +
                        parse_hours_cell(sh.cell_value(row, cols['sem1p']))) if sh.ncols > cols['sem1p'] else 0.0
            sem2_h   = (parse_hours_cell(sh.cell_value(row, cols['sem2t'])) +
                        parse_hours_cell(sh.cell_value(row, cols['sem2p']))) if sh.ncols > cols['sem2p'] else 0.0

            teacher_cell = str(sh.cell_value(row, tc)).strip() if sh.ncols > tc else ''

            # Check if this is an "ОН X.X" descriptor row (has hours but long description)
            is_on_row = bool(re.match(r'^ОН\s+\d', subj_raw, re.I))
            # Check if this is a human-readable name row (no hours, short name)
            is_name_row = (not is_on_row and subj_raw and total_h == 0 and
                           not any(kw in subj_raw.lower() for kw in
                                   ['модуль', 'барлығы', '№', 'жартыжылдық', 'теориял', 'тәжіриб']))

            if pending_record and is_name_row:
                # Complete the pending record with readable subject name
                sid = normalize_subject(subj_raw, s_map)
                if sid:
                    pending_record['subject_id'] = sid
                    records.append(pending_record)
                pending_record = None
                continue

            if is_on_row and (total_h > 0 or sem1_h > 0 or sem2_h > 0):
                # Store as pending - will be completed with next readable row
                tids = parse_teachers_from_cell(teacher_cell, t_map)
                pending_record = {
                    'group_id': current_group_id,
                    'subject_id': None,
                    'teacher_ids': tids,
                    'total_hours': total_h or sem1_h + sem2_h,
                    'sem1_hours': sem1_h,
                    'sem2_hours': sem2_h,
                }
                continue

            if not subj_raw or total_h == 0:
                continue

            subject_id = normalize_subject(subj_raw, s_map)
            if not subject_id:
                continue

            tids = parse_teachers_from_cell(teacher_cell, t_map)
            records.append({
                'group_id': current_group_id,
                'subject_id': subject_id,
                'teacher_ids': tids,
                'total_hours': total_h,
                'sem1_hours': sem1_h,
                'sem2_hours': sem2_h,
            })

    return records


# ─── Парсинг DOCX файлов ─────────────────────────────────────────────────────

GROUP_RE = re.compile(
    r'((?:WEB|ОП|ТП|ТК|ТХ|РПО|ИС|БД|БУХ)\s*[\d]+[\s\-\u2013\u2014]+[\d]+)',
    re.I
)


def parse_docx_file(filepath, t_map, s_map, g_map):
    """Parse docx: paragraphs set current group, tables have curriculum rows."""
    records = []
    try:
        from docx import Document
        from docx.oxml.ns import qn
        doc = Document(filepath)
    except Exception as e:
        print(f"  Cannot open {filepath}: {e}")
        return records

    current_group_id = None

    # Iterate document body elements in order (paragraphs and tables mixed)
    body = doc.element.body
    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        # ── Paragraph: detect group name ────────────────────────────
        if tag == 'p':
            text = ''.join(t.text or '' for t in child.iter() if t.tag.endswith('}t')).strip()
            m = GROUP_RE.search(text)
            if m:
                gid = normalize_group_code(m.group(1), g_map)
                if gid:
                    current_group_id = gid

        # ── Table: parse curriculum rows ─────────────────────────────
        elif tag == 'tbl':
            rows_xml = child.findall('.//' + '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
            # Try to detect group name from early table rows (for files where group is inside table)
            if not current_group_id:
                for scan_row in rows_xml[:4]:
                    cells_xml = scan_row.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc')
                    for cell_el in cells_xml:
                        cell_text = ''.join(
                            t.text or '' for t in cell_el.iter() if t.tag.endswith('}t')
                        ).strip()
                        m = GROUP_RE.search(cell_text)
                        if m:
                            gid = normalize_group_code(m.group(1), g_map)
                            if gid:
                                current_group_id = gid
                                break
                    if current_group_id:
                        break

            if not current_group_id:
                continue

            # Also scan first rows for a new group (table may have its own group header)
            # Detect column layout from header row
            subj_col, total_col, teacher_col = 1, 7, 8  # defaults

            pending_record = None  # for ОН X.X rows same as XLS parser

            for ri, row_el in enumerate(rows_xml):
                cells_xml = row_el.findall(
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'
                )
                cells = []
                for cell_el in cells_xml:
                    text = ''.join(
                        t.text or ''
                        for t in cell_el.iter()
                        if t.tag.endswith('}t')
                    ).strip()
                    cells.append(text)

                if not cells:
                    continue

                # Check if this row contains a group name (table-internal group header)
                if ri <= 2:
                    row_text = ' '.join(cells)
                    m = GROUP_RE.search(row_text)
                    if m:
                        gid = normalize_group_code(m.group(1), g_map)
                        if gid:
                            current_group_id = gid

                # Detect header row
                if ri <= 1:
                    for ci, c in enumerate(cells):
                        cl = c.lower()
                        if 'всего' in cl or 'барлығы' in cl or 'барлыгы' in cl:
                            total_col = ci
                        if 'преподав' in cl or 'оқытушы' in cl:
                            teacher_col = ci
                        if 'дисципл' in cl or 'пән' in cl or 'модуль' in cl or 'пәндер' in cl:
                            subj_col = ci
                    continue

                if len(cells) <= subj_col:
                    continue

                subj_raw = cells[subj_col] if len(cells) > subj_col else ''

                # Compute hours for this row
                total_h = parse_hours_cell(cells[total_col]) if len(cells) > total_col else 0.0
                if total_h <= 0:
                    for ci in range(2, min(6, len(cells))):
                        total_h += parse_hours_cell(cells[ci])

                sem1_h = (parse_hours_cell(cells[2]) + parse_hours_cell(cells[3])
                          ) if len(cells) > 3 else 0.0
                sem2_h = (parse_hours_cell(cells[4]) + parse_hours_cell(cells[5])
                          ) if len(cells) > 5 else 0.0
                teacher_cell = cells[teacher_col] if len(cells) > teacher_col else ''

                # Detect ОН X.X rows (Kazakhstani learning outcome rows that carry hours)
                is_on_row = bool(re.match(r'^ОН\s+\d', subj_raw, re.I))
                # Name-only row: has a subject name but no hours (hours are on the ОН row above)
                is_name_row = (not is_on_row and subj_raw and total_h == 0 and
                               not any(kw in subj_raw.lower() for kw in
                                       ['модуль', 'барлығы', '№', 'жартыжылдық', 'теориял',
                                        'тәжіриб', 'аттестац', 'консульт', 'факультат',
                                        'итого', 'всего', 'кәсіптік тәжірибе']))

                if pending_record and is_name_row:
                    sid = normalize_subject(subj_raw, s_map)
                    if sid:
                        pending_record['subject_id'] = sid
                        records.append(pending_record)
                    pending_record = None
                    continue

                if is_on_row and total_h > 0:
                    tids = parse_teachers_from_cell(teacher_cell, t_map)
                    pending_record = {
                        'group_id': current_group_id,
                        'subject_id': None,
                        'teacher_ids': tids,
                        'total_hours': total_h,
                        'sem1_hours': sem1_h,
                        'sem2_hours': sem2_h,
                    }
                    continue
                else:
                    pending_record = None  # reset if non-name row follows ОН

                subject_id = normalize_subject(subj_raw, s_map)
                if not subject_id:
                    continue

                if total_h <= 0:
                    continue

                teacher_ids = parse_teachers_from_cell(teacher_cell, t_map)

                records.append({
                    'group_id': current_group_id,
                    'subject_id': subject_id,
                    'teacher_ids': teacher_ids,
                    'total_hours': total_h,
                    'sem1_hours': sem1_h,
                    'sem2_hours': sem2_h,
                })

    return records


# ─── Основная логика ─────────────────────────────────────────────────────────

def seed(db: Session):
    t_map, s_map, g_map, lt_map, ap_map = load_maps(db)

    print(f"Loaded: {len(t_map)} teachers, {len(s_map)} subjects, {len(g_map)} groups")
    print(f"Academic periods: {list(ap_map.keys())}")

    # Use active period for semester 2 (spring)
    ap_t1 = ap_map.get('2025-2026-T1') or ap_map.get('LEGACY-S1')
    ap_t2 = ap_map.get('2025-2026-T2') or ap_t1
    print(f"Using periods: T1={ap_t1}, T2={ap_t2}")

    lt_lecture  = lt_map.get('LECTURE', list(lt_map.values())[0])
    lt_practice = lt_map.get('PRACTICE', lt_lecture)

    # ── Collect all records ──────────────────────────────────────────
    all_records = []

    # XLS files
    xls_files = [
        'сетка часов БД на 2025-2026 жанна 1 курс свод  чистовик !!!!.xls',
        'сетка часов БД на 2025-2026 жанна 2,3 курс чистовик !!!! Айнура Жанна.xls',
    ]
    for fname in xls_files:
        fpath = os.path.join(BASE_DIR, fname)
        if os.path.exists(fpath):
            print(f"Parsing: {fname}")
            recs = parse_xls_file(fpath, t_map, s_map, g_map)
            print(f"  -> {len(recs)} records")
            all_records.extend(recs)

    # DOCX files
    docx_files = [
        'Сетка 2025-2026 уч.г. (верно).docx',
        'Сетка часов 2025 - 2026 2 курс.docx',
        'Сетка часов 2025 - 2026 3 курс.docx',
        'Сетка часов 2025 -2026 1 курс.docx',
        'Сетка часов 2025- 2026 4 курс.docx',
        'сетка часов БУХ на  2025-2026 ж - Жанна +Айнур.docx',
    ]
    for fname in docx_files:
        fpath = os.path.join(BASE_DIR, fname)
        if os.path.exists(fpath):
            print(f"Parsing: {fname}")
            recs = parse_docx_file(fpath, t_map, s_map, g_map)
            print(f"  -> {len(recs)} records")
            all_records.extend(recs)

    print(f"\nTotal raw records: {len(all_records)}")

    # ── Deduplicate and insert ───────────────────────────────────────
    # Collect unique teacher-subject pairs for teacher_subjects
    ts_pairs = set()  # (teacher_id, subject_id)

    # Deduplicate curriculum: (group_id, subject_id, period_id) -> record
    curriculum_map = {}

    for rec in all_records:
        gid = rec['group_id']
        sid = rec['subject_id']
        tids = rec['teacher_ids']
        total_h = rec['total_hours']
        sem1_h = rec['sem1_hours']
        sem2_h = rec['sem2_hours']

        # Determine primary teacher
        primary_tid = tids[0] if tids else None

        # Collect teacher-subject pairs
        for tid in tids:
            ts_pairs.add((tid, sid))

        # Determine which periods get entries
        entries = []
        if sem1_h > 0 and ap_t1:
            entries.append((ap_t1, sem1_h))
        if sem2_h > 0 and ap_t2 and ap_t2 != ap_t1:
            entries.append((ap_t2, sem2_h))
        if not entries and ap_t2:
            entries.append((ap_t2, total_h))

        for ap_id, hours in entries:
            key = (gid, sid, ap_id)
            if key not in curriculum_map or hours > curriculum_map[key]['total_hours']:
                curriculum_map[key] = {
                    'academic_period_id': ap_id,
                    'group_id': gid,
                    'subject_id': sid,
                    'teacher_id': primary_tid,
                    'total_hours': hours,
                    'planned_weekly_hours': round(hours / 16, 2),
                }

    # ── Insert teacher_subjects ──────────────────────────────────────
    print(f"\nInserting {len(ts_pairs)} teacher-subject pairs...")
    inserted_ts = 0
    for tid, sid in ts_pairs:
        exists = db.query(TeacherSubject).filter_by(
            teacher_id=tid, subject_id=sid
        ).first()
        if not exists:
            db.add(TeacherSubject(
                teacher_id=tid,
                subject_id=sid,
                is_primary=False,
                is_active=True,
            ))
            inserted_ts += 1
    db.commit()
    print(f"  Inserted: {inserted_ts} new records")

    # ── Insert group_subject_load ────────────────────────────────────
    print(f"\nInserting {len(curriculum_map)} curriculum entries...")
    inserted_c = 0
    skipped_c = 0
    for key, rec in curriculum_map.items():
        exists = db.query(Curriculum).filter_by(
            academic_period_id=rec['academic_period_id'],
            group_id=rec['group_id'],
            subject_id=rec['subject_id'],
        ).first()
        if exists:
            skipped_c += 1
            continue

        db.add(Curriculum(
            academic_period_id=rec['academic_period_id'],
            group_id=rec['group_id'],
            subject_id=rec['subject_id'],
            lesson_type_id=lt_lecture,
            planned_weekly_hours=max(rec['planned_weekly_hours'], 2.0),
            total_hours=rec['total_hours'],
            preferred_teacher_id=rec['teacher_id'],
            is_mandatory=True,
        ))
        inserted_c += 1

    db.commit()
    print(f"  Inserted: {inserted_c}, Skipped (already exist): {skipped_c}")


def main():
    print("\n=== Seed curriculum from documents ===\n")
    with Session(engine) as db:
        seed(db)

    print("\n=== Final DB state ===")
    with Session(engine) as db:
        ts_count = db.query(TeacherSubject).count()
        c_count = db.query(Curriculum).count()
        print(f"  teacher_subjects:     {ts_count}")
        print(f"  group_subject_load:   {c_count}")

    print("\nDone!")


if __name__ == '__main__':
    main()
