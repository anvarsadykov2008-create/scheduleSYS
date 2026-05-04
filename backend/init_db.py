"""
init_db.py — Инициализация базы данных scheduleSYS
Создаёт все таблицы и заполняет реальными данными.

Запуск:  cd backend && python init_db.py
"""

import os
import sys
import shutil
from datetime import date, time as dtime, datetime, timezone

# Чтобы импорты app.* работали из папки backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings, DEFAULT_DB_PATH
from app.database import Base, engine
from app.models.models import (
    Department, Specialty, AcademicPeriod, LessonType, RoomType,
    TimeSlot, Teacher, Subject, TeacherSubject, Group, Room,
    Curriculum, User, UserRole, SystemSetting,
)
from app.auth import get_password_hash
from sqlalchemy.orm import Session

DB_PATH = DEFAULT_DB_PATH


def backup_existing():
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        bak = DB_PATH + ".bak"
        shutil.copy2(DB_PATH, bak)
        print(f"  Резервная копия: {bak}")


def recreate_tables():
    print(">> Пересоздаём таблицы...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("  ОК")


def seed_all(db: Session):
    # ── 1. LESSON TYPES ─────────────────────────────────────────────
    print(">> lesson_types...")
    lesson_types = [
        LessonType(code="LECTURE",   name="Лекция",             is_lab=False, requires_room_match=False),
        LessonType(code="PRACTICE",  name="Практика",           is_lab=False, requires_room_match=False),
        LessonType(code="LAB",       name="Лабораторная",       is_lab=True,  requires_room_match=True),
        LessonType(code="PE",        name="Физическая культура",is_lab=False, requires_room_match=False),
        LessonType(code="SEMINAR",   name="Семинар",            is_lab=False, requires_room_match=False),
    ]
    db.add_all(lesson_types)
    db.commit()
    lt_map = {lt.code: lt for lt in db.query(LessonType).all()}

    # ── 2. ROOM TYPES ───────────────────────────────────────────────
    print(">> room_types...")
    room_types = [
        RoomType(code="CLASSROOM",   name="Учебная аудитория",  is_lab=False),
        RoomType(code="COMPUTER_LAB",name="Компьютерный класс", is_lab=True),
        RoomType(code="GYM",         name="Спортивный зал",     is_lab=False),
        RoomType(code="LECTURE_HALL",name="Лекционный зал",     is_lab=False),
    ]
    db.add_all(room_types)
    db.commit()
    rt_map = {rt.code: rt for rt in db.query(RoomType).all()}

    # ── 3. TIME SLOTS (Пн=1..Сб=6, 7 пар) ──────────────────────────
    print(">> time_slots...")
    pairs = [
        (1, "08:00", "09:30"),
        (2, "09:35", "11:05"),
        (3, "11:20", "12:50"),
        (4, "13:10", "14:40"),
        (5, "14:50", "16:20"),
        (6, "16:25", "17:55"),
        (7, "18:00", "19:30"),
    ]
    slots = []
    for day in range(1, 7):
        for slot_no, start_s, end_s in pairs:
            h1, m1 = map(int, start_s.split(":"))
            h2, m2 = map(int, end_s.split(":"))
            slots.append(TimeSlot(
                day_of_week=day,
                slot_number=slot_no,
                start_time=dtime(h1, m1),
                end_time=dtime(h2, m2),
                academic_hours=2.00,
            ))
    db.add_all(slots)
    db.commit()

    # ── 4. DEPARTMENTS + SPECIALTIES ────────────────────────────────
    print(">> departments + specialties...")
    dept_it  = Department(code="IT",  name="Информационные технологии")
    dept_buh = Department(code="BUH", name="Экономика и бухгалтерия")
    db.add_all([dept_it, dept_buh])
    db.commit()

    specialties_data = [
        (dept_it,  "IS",   "Информационные системы",               "Техник"),
        (dept_it,  "SETI", "Компьютерные сети и телекоммуникации", "Техник"),
        (dept_it,  "PROG", "Программное обеспечение",              "Техник"),
        (dept_it,  "WEB",  "Веб-разработка",                       "Техник"),
        (dept_it,  "BD",   "Базы данных",                          "Техник"),
        (dept_buh, "BUH",  "Бухгалтерский учёт",                   "Бухгалтер"),
    ]
    specs = []
    for dept, code, name, qual in specialties_data:
        s = Specialty(department_id=dept.department_id, code=code, name=name, qualification=qual)
        db.add(s)
        specs.append(s)
    db.commit()
    spec_map = {sp.code: sp for sp in db.query(Specialty).all()}

    # ── 5. ACADEMIC PERIODS ─────────────────────────────────────────
    print(">> academic_periods...")
    ap_fall = AcademicPeriod(
        code="2025-2026-1", name="Осенний семестр 2025-2026",
        academic_year="2025-2026", term_no=1,
        start_date=date(2025, 9, 1), end_date=date(2026, 1, 23),
        weeks_in_period=17.00, is_active=False,
    )
    ap_spring = AcademicPeriod(
        code="2025-2026-2", name="Весенний семестр 2025-2026",
        academic_year="2025-2026", term_no=2,
        start_date=date(2026, 2, 2), end_date=date(2026, 5, 29),
        weeks_in_period=16.00, is_active=True,
    )
    db.add_all([ap_fall, ap_spring])
    db.commit()
    ap = db.query(AcademicPeriod).filter_by(code="2025-2026-2").first()

    # ── 6. SUBJECTS ─────────────────────────────────────────────────
    print(">> subjects...")
    subjects_data = [
        ("Высшая математика",          "standard"),
        ("Физика",                     "standard"),
        ("Основы алгоритмизации",      "standard"),
        ("Базы данных (SQL)",          "standard"),
        ("Веб-разработка",             "standard"),
        ("История Казахстана",         "standard"),
        ("Английский язык",            "standard"),
        ("Физкультура",                "physical"),
        ("Операционные системы",       "standard"),
        ("Компьютерные сети",          "standard"),
        ("Философия",                  "standard"),
        ("Информационная безопасность","standard"),
    ]
    for name, kind in subjects_data:
        db.add(Subject(name=name, subject_kind=kind))
    db.commit()
    subj_map = {s.name: s for s in db.query(Subject).all()}

    # ── 7. TEACHERS ─────────────────────────────────────────────────
    print(">> teachers...")
    teachers_data = [
        ("T001","Попов",    "М.","И."),    ("T002","Смирнов",  "И.","И.(1)"),
        ("T003","Фёдоров",  "Е.","Е."),    ("T004","Смирнов",  "Д.","Д."),
        ("T005","Захаров",  "И.","И.(1)"), ("T006","Волков",   "Д.","Д."),
        ("T007","Волков",   "Н.","Н.(1)"), ("T008","Смирнов",  "И.","И.(2)"),
        ("T009","Лебедев",  "М.","М."),    ("T010","Николаев", "В.","В."),
        ("T011","Захаров",  "И.","И.(2)"), ("T012","Егоров",   "Д.","Д."),
        ("T013","Степанов", "М.","М.(1)"), ("T014","Соколов",  "И.","И."),
        ("T015","Смирнов",  "И.","И.(3)"), ("T016","Васильев", "Н.","Н."),
        ("T017","Никитин",  "А.","А."),    ("T018","Петров",   "О.","О."),
        ("T019","Попов",    "В.","В."),    ("T020","Лебедев",  "И.","И."),
        ("T021","Никитин",  "Е.","Е."),    ("T022","Кузнецов", "С.","С."),
        ("T023","Захаров",  "М.","М."),    ("T024","Михайлов", "М.","М.(1)"),
        ("T025","Иванов",   "С.","С.(1)"), ("T026","Новиков",  "С.","С."),
        ("T027","Орлов",    "С.","С."),    ("T028","Соколов",  "Е.","Е."),
        ("T029","Егоров",   "М.","М."),    ("T030","Захаров",  "О.","О."),
        ("T031","Петров",   "С.","С."),    ("T032","Егоров",   "В.","В."),
        ("T033","Степанов", "О.","О."),    ("T034","Орлов",    "И.","И."),
        ("T035","Волков",   "Н.","Н.(2)"), ("T036","Никитин",  "С.","С."),
        ("T037","Орлов",    "Е.","Е."),    ("T038","Волков",   "П.","П."),
        ("T039","Петров",   "Д.","Д."),    ("T040","Петров",   "Н.","Н."),
        ("T041","Иванов",   "С.","С.(2)"), ("T042","Попов",    "Е.","Е."),
        ("T043","Захаров",  "П.","П."),    ("T044","Степанов", "М.","М.(2)"),
        ("T045","Михайлов", "М.","М.(2)"), ("T046","Волков",   "Н.","Н.(3)"),
        ("T047","Морозов",  "В.","В."),    ("T048","Андреев",  "Д.","Д."),
        ("T049","Лебедев",  "Е.","Е."),    ("T050","Новиков",  "О.","О."),
    ]
    for code, last, first, mid in teachers_data:
        db.add(Teacher(employee_code=code, last_name=last, first_name=first, middle_name=mid))
    db.commit()
    t_map = {t.employee_code: t for t in db.query(Teacher).all()}

    # ── 8. GROUPS ───────────────────────────────────────────────────
    print(">> groups...")
    groups_data = [
        ("IS",   "ИС-22-3",   "ИС-22-3",   4, 29),
        ("IS",   "ИС-24-1",   "ИС-24-1",   2, 20),
        ("IS",   "ИС-24-2",   "ИС-24-2",   2, 16),
        ("IS",   "ИС-25-1",   "ИС-25-1",   1, 28),
        ("SETI", "СЕТИ-22-1", "СЕТИ-22-1", 4, 16),
        ("SETI", "СЕТИ-23-3", "СЕТИ-23-3", 3, 24),
        ("SETI", "СЕТИ-24-1", "СЕТИ-24-1", 2, 26),
        ("SETI", "СЕТИ-25-3", "СЕТИ-25-3", 1, 17),
        ("PROG", "ПРОГ-22-2", "ПРОГ-22-2", 4, 18),
        ("PROG", "ПРОГ-24-2", "ПРОГ-24-2", 2, 17),
        ("PROG", "ПРОГ-25-1", "ПРОГ-25-1", 1, 17),
        ("PROG", "ПРОГ-25-3", "ПРОГ-25-3", 1, 24),
        ("WEB",  "ВЕБ-22-1",  "ВЕБ-22-1",  4, 21),
        ("WEB",  "ВЕБ-22-3",  "ВЕБ-22-3",  4, 17),
        ("WEB",  "ВЕБ-23-1",  "ВЕБ-23-1",  3, 30),
        ("WEB",  "ВЕБ-23-3",  "ВЕБ-23-3",  3, 22),
        ("WEB",  "ВЕБ-25-1",  "ВЕБ-25-1",  1, 22),
        ("BD",   "БД-22-2",   "БД-22-2",   4, 30),
        ("BD",   "БД-23-1",   "БД-23-1",   3, 24),
        ("BD",   "БД-23-3",   "БД-23-3",   3, 17),
        ("BD",   "БД-24-1",   "БД-24-1",   2, 20),
        ("BD",   "БД-25-2",   "БД-25-2",   1, 21),
        ("BD",   "БД-25-3",   "БД-25-3",   1, 26),
    ]
    for spec_code, code, name, course_no, sc in groups_data:
        db.add(Group(
            specialty_id=spec_map[spec_code].specialty_id,
            code=code, name=name, course_no=course_no, student_count=sc,
        ))
    db.commit()
    g_map = {g.code: g for g in db.query(Group).all()}

    # ── 9. ROOMS ────────────────────────────────────────────────────
    print(">> rooms...")
    rooms_data = [
        ("101","Кабинет 101",       1, 30, "CLASSROOM"),
        ("104","Кабинет 104",       1, 30, "CLASSROOM"),
        ("113","Кабинет 113",       1, 30, "CLASSROOM"),
        ("114","Кабинет 114",       1, 32, "CLASSROOM"),
        ("115","Кабинет 115 (комп)",1, 30, "COMPUTER_LAB"),
        ("116","Кабинет 116",       1, 32, "CLASSROOM"),
        ("117","Кабинет 117",       1, 26, "CLASSROOM"),
        ("118","Кабинет 118",       1, 30, "CLASSROOM"),
        ("120","Кабинет 120 (комп)",1, 30, "COMPUTER_LAB"),
        ("200","Кабинет 200",       2, 30, "CLASSROOM"),
        ("201","Кабинет 201",       2, 30, "CLASSROOM"),
        ("203","Кабинет 203",       2, 30, "CLASSROOM"),
        ("208","Кабинет 208",       2, 30, "CLASSROOM"),
        ("209","Кабинет 209",       2, 30, "CLASSROOM"),
        ("210","Кабинет 210",       2, 28, "CLASSROOM"),
        ("211","Кабинет 211",       2, 30, "CLASSROOM"),
        ("212","Кабинет 212",       2, 30, "CLASSROOM"),
        ("213","Кабинет 213",       2, 30, "CLASSROOM"),
        ("218","Кабинет 218 (комп)",2, 30, "COMPUTER_LAB"),
        ("220","Кабинет 220 (комп)",2, 30, "COMPUTER_LAB"),
        ("222","Кабинет 222 (комп)",2, 30, "COMPUTER_LAB"),
        ("224","Кабинет 224 (комп)",2, 30, "COMPUTER_LAB"),
        ("300","Кабинет 300",       3, 30, "CLASSROOM"),
        ("301","Кабинет 301",       3, 30, "CLASSROOM"),
        ("302","Кабинет 302",       3, 30, "CLASSROOM"),
        ("303","Кабинет 303",       3, 30, "CLASSROOM"),
        ("304","Кабинет 304",       3, 30, "CLASSROOM"),
        ("306","Кабинет 306",       3, 30, "CLASSROOM"),
        ("308","Кабинет 308",       3, 30, "CLASSROOM"),
        ("309","Кабинет 309",       3, 30, "CLASSROOM"),
        ("310","Кабинет 310",       3, 30, "CLASSROOM"),
        ("311","Кабинет 311 (комп)",3, 16, "COMPUTER_LAB"),
        ("312","Кабинет 312",       3, 30, "CLASSROOM"),
        ("316","Кабинет 316",       3, 28, "CLASSROOM"),
        ("320","Кабинет 320 (комп)",3, 30, "COMPUTER_LAB"),
        ("322","Кабинет 322 (комп)",3, 30, "COMPUTER_LAB"),
        ("324","Кабинет 324 (комп)",3, 30, "COMPUTER_LAB"),
    ]
    for code, name, floor, cap, rtype in rooms_data:
        db.add(Room(
            code=code, name=name, building="Главный корпус",
            floor=floor, capacity=cap,
            room_type_id=rt_map[rtype].room_type_id,
        ))
    db.commit()

    # ── 10. TEACHER SUBJECTS ────────────────────────────────────────
    print(">> teacher_subjects...")
    ts_links = [
        ("T004","Высшая математика",True),  ("T011","Высшая математика",False),
        ("T014","Высшая математика",False), ("T042","Высшая математика",False),
        ("T021","Физика",True),             ("T037","Физика",False),
        ("T003","Основы алгоритмизации",True), ("T023","Основы алгоритмизации",False),
        ("T045","Основы алгоритмизации",False),
        ("T015","Базы данных (SQL)",True),  ("T016","Базы данных (SQL)",False),
        ("T019","Базы данных (SQL)",False), ("T028","Базы данных (SQL)",False),
        ("T002","Веб-разработка",True),     ("T010","Веб-разработка",False),
        ("T013","Веб-разработка",False),    ("T036","Веб-разработка",False),
        ("T040","Веб-разработка",False),    ("T049","Веб-разработка",False),
        ("T008","История Казахстана",True), ("T009","История Казахстана",False),
        ("T048","История Казахстана",False),
        ("T007","Английский язык",True),    ("T017","Английский язык",False),
        ("T032","Английский язык",False),   ("T044","Английский язык",False),
        ("T046","Английский язык",False),
        ("T001","Физкультура",True),        ("T026","Физкультура",False),
        ("T030","Физкультура",False),       ("T035","Физкультура",False),
        ("T050","Физкультура",False),
        ("T012","Операционные системы",True),  ("T018","Операционные системы",False),
        ("T024","Операционные системы",False), ("T025","Операционные системы",False),
        ("T029","Операционные системы",False), ("T047","Операционные системы",False),
        ("T033","Компьютерные сети",True),  ("T039","Компьютерные сети",False),
        ("T005","Философия",True),          ("T006","Философия",False),
        ("T020","Философия",False),         ("T022","Философия",False),
        ("T027","Философия",False),         ("T031","Философия",False),
        ("T041","Философия",False),         ("T043","Философия",False),
        ("T034","Информационная безопасность",True),
        ("T038","Информационная безопасность",False),
    ]
    for emp, subj_name, is_primary in ts_links:
        db.add(TeacherSubject(
            teacher_id=t_map[emp].teacher_id,
            subject_id=subj_map[subj_name].subject_id,
            is_primary=is_primary,
        ))
    db.commit()

    # ── 11. GROUP SUBJECT LOAD (учебный план) ───────────────────────
    print(">> group_subject_load...")
    load_data = [
        ("ИС-24-1",  "Высшая математика",          "T011",6, "LECTURE"),
        ("ИС-24-1",  "Английский язык",             "T017",3, "PRACTICE"),
        ("ИС-24-1",  "Основы алгоритмизации",       "T045",3, "PRACTICE"),
        ("ИС-24-1",  "Операционные системы",        "T047",6, "PRACTICE"),
        ("СЕТИ-22-1","Базы данных (SQL)",            "T028",10,"PRACTICE"),
        ("СЕТИ-22-1","Веб-разработка",              "T049",6, "PRACTICE"),
        ("СЕТИ-22-1","Компьютерные сети",           "T033",2, "PRACTICE"),
        ("ПРОГ-25-1","Высшая математика",           "T004",4, "LECTURE"),
        ("ПРОГ-25-1","Основы алгоритмизации",       "T003",6, "PRACTICE"),
        ("ПРОГ-25-1","Английский язык",             "T007",3, "PRACTICE"),
        ("ПРОГ-25-1","История Казахстана",          "T009",2, "LECTURE"),
        ("ВЕБ-22-1", "Операционные системы",        "T025",6, "PRACTICE"),
        ("ВЕБ-22-1", "Веб-разработка",              "T002",10,"PRACTICE"),
        ("ВЕБ-22-1", "История Казахстана",          "T048",2, "LECTURE"),
        ("ИС-22-3",  "Информационная безопасность", "T034",8, "PRACTICE"),
        ("ИС-22-3",  "Компьютерные сети",           "T033",4, "PRACTICE"),
        ("ИС-22-3",  "Философия",                   "T022",2, "LECTURE"),
        ("БД-25-2",  "Основы алгоритмизации",       "T023",6, "PRACTICE"),
        ("БД-25-2",  "Высшая математика",            "T042",4, "LECTURE"),
        ("БД-25-2",  "Английский язык",              "T017",3, "PRACTICE"),
        ("ИС-24-2",  "Операционные системы",        "T012",6, "PRACTICE"),
        ("ИС-24-2",  "Базы данных (SQL)",            "T015",4, "PRACTICE"),
        ("ИС-24-2",  "Английский язык",             "T032",3, "PRACTICE"),
        ("СЕТИ-23-3","Компьютерные сети",           "T033",8, "PRACTICE"),
        ("СЕТИ-23-3","Операционные системы",        "T018",4, "PRACTICE"),
        ("СЕТИ-23-3","Философия",                   "T027",2, "LECTURE"),
        ("ВЕБ-25-1", "Веб-разработка",              "T036",8, "PRACTICE"),
        ("ВЕБ-25-1", "Основы алгоритмизации",       "T003",4, "PRACTICE"),
        ("ВЕБ-25-1", "История Казахстана",          "T008",2, "LECTURE"),
        ("БД-23-3",  "Базы данных (SQL)",            "T016",8, "PRACTICE"),
        ("БД-23-3",  "Веб-разработка",              "T013",4, "PRACTICE"),
        ("БД-23-3",  "Философия",                   "T006",2, "LECTURE"),
        ("БД-23-1",  "Базы данных (SQL)",            "T015",8, "PRACTICE"),
        ("БД-23-1",  "Операционные системы",        "T029",4, "PRACTICE"),
        ("БД-23-1",  "Философия",                   "T041",2, "LECTURE"),
        ("СЕТИ-24-1","Компьютерные сети",           "T039",6, "PRACTICE"),
        ("СЕТИ-24-1","Операционные системы",        "T024",4, "PRACTICE"),
        ("СЕТИ-24-1","Английский язык",             "T044",3, "PRACTICE"),
        ("ПРОГ-25-3","Высшая математика",           "T004",4, "LECTURE"),
        ("ПРОГ-25-3","Основы алгоритмизации",       "T045",6, "PRACTICE"),
        ("ПРОГ-25-3","Английский язык",             "T007",3, "PRACTICE"),
        ("ИС-25-1",  "Высшая математика",           "T011",4, "LECTURE"),
        ("ИС-25-1",  "Основы алгоритмизации",       "T023",4, "PRACTICE"),
        ("ИС-25-1",  "Английский язык",             "T046",3, "PRACTICE"),
        ("ИС-25-1",  "История Казахстана",          "T009",2, "LECTURE"),
        ("СЕТИ-25-3","Основы алгоритмизации",       "T003",4, "PRACTICE"),
        ("СЕТИ-25-3","Высшая математика",            "T014",4, "LECTURE"),
        ("СЕТИ-25-3","Английский язык",             "T017",3, "PRACTICE"),
        ("ВЕБ-23-1", "Веб-разработка",              "T010",8, "PRACTICE"),
        ("ВЕБ-23-1", "Операционные системы",        "T047",4, "PRACTICE"),
        ("ВЕБ-23-1", "Философия",                   "T005",2, "LECTURE"),
        ("ПРОГ-22-2","Информационная безопасность", "T038",6, "PRACTICE"),
        ("ПРОГ-22-2","Компьютерные сети",           "T039",4, "PRACTICE"),
        ("ПРОГ-22-2","Философия",                   "T031",2, "LECTURE"),
        ("ВЕБ-23-3", "Веб-разработка",              "T040",6, "PRACTICE"),
        ("ВЕБ-23-3", "Операционные системы",        "T012",4, "PRACTICE"),
        ("ВЕБ-23-3", "Философия",                   "T022",2, "LECTURE"),
        ("БД-25-3",  "Основы алгоритмизации",       "T045",6, "PRACTICE"),
        ("БД-25-3",  "Высшая математика",            "T014",4, "LECTURE"),
        ("БД-25-3",  "Английский язык",             "T032",3, "PRACTICE"),
        ("ПРОГ-24-2","Операционные системы",        "T025",6, "PRACTICE"),
        ("ПРОГ-24-2","Компьютерные сети",           "T033",4, "PRACTICE"),
        ("ПРОГ-24-2","Философия",                   "T020",2, "LECTURE"),
        ("ВЕБ-22-3", "Информационная безопасность", "T034",6, "PRACTICE"),
        ("ВЕБ-22-3", "Веб-разработка",              "T002",6, "PRACTICE"),
        ("ВЕБ-22-3", "Философия",                   "T043",2, "LECTURE"),
        ("БД-22-2",  "Информационная безопасность", "T038",6, "PRACTICE"),
        ("БД-22-2",  "Базы данных (SQL)",            "T019",6, "PRACTICE"),
        ("БД-22-2",  "Философия",                   "T006",2, "LECTURE"),
        ("БД-24-1",  "Базы данных (SQL)",            "T028",8, "PRACTICE"),
        ("БД-24-1",  "Операционные системы",        "T018",4, "PRACTICE"),
        ("БД-24-1",  "Английский язык",             "T007",3, "PRACTICE"),
    ]
    pe_teachers = ["T001","T026","T030","T035","T050"]
    for i, grp_code in enumerate(sorted(g_map.keys())):
        emp = pe_teachers[i % 5]
        load_data.append((grp_code, "Физкультура", emp, 2, "PE"))

    for grp_code, subj_name, emp, ppw, lt_code in load_data:
        if grp_code not in g_map or subj_name not in subj_map or emp not in t_map:
            continue
        db.add(Curriculum(
            academic_period_id=ap.academic_period_id,
            group_id=g_map[grp_code].group_id,
            subject_id=subj_map[subj_name].subject_id,
            lesson_type_id=lt_map[lt_code].lesson_type_id,
            planned_weekly_hours=float(ppw * 2),
            total_hours=float(ppw * 2 * 16),
            preferred_teacher_id=t_map[emp].teacher_id,
            is_mandatory=True,
        ))
    db.commit()

    # ── 12. ADMIN USER ──────────────────────────────────────────────
    print(">> admin user...")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    db.add(User(
        username="990101000001",
        password_hash=get_password_hash(admin_password),
        role=UserRole.ADMIN,
        full_name="Администратор",
        is_not_student=True,
    ))
    db.commit()
    print(f"  Логин: 990101000001 / Пароль: {admin_password}")


def main():
    print(f"\n=== Инициализация БД: {DB_PATH} ===\n")
    backup_existing()
    recreate_tables()

    from sqlalchemy.orm import Session as S
    with S(engine) as db:
        seed_all(db)

    print("\nOK: База данных успешно инициализирована!\n")
    print("Итог:")
    with S(engine) as db:
        from app.models.models import Teacher, Group, Subject, Room, Curriculum, TimeSlot
        print(f"  Преподаватели:  {db.query(Teacher).count()}")
        print(f"  Группы:         {db.query(Group).count()}")
        print(f"  Дисциплины:     {db.query(Subject).count()}")
        print(f"  Кабинеты:       {db.query(Room).count()}")
        print(f"  Учебный план:   {db.query(Curriculum).count()} записей")
        print(f"  Слоты времени:  {db.query(TimeSlot).count()}")


if __name__ == "__main__":
    main()
