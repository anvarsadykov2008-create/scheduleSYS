"""
Финальная очистка БД — использует точные ID из вывода check_db_data.py.
Таблица: hour_grids (не hour_grid!), teacher_subjects.
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# ─────────────────────────────────────────────────────────────
# СЛИЯНИЯ ПРЕДМЕТОВ: (keep_id, remove_id, описание)
# ─────────────────────────────────────────────────────────────
SUBJECT_MERGES = [
    # keep_id, remove_id
    (29,  124,  "алгоритмизация и программирование/программирования"),
    (40,   41,  "управление контентом web-ресурсов / web - контентом"),
    (45,  123,  "Проверка рефакторинга программного кода / рефакторинга"),
    (43,  122,  "Составление алгоритма ...на основе спецификации / короткий"),
    (33,  118,  "Жергілікті желілер длинный / короткий"),
    (36,   55,  "Кәсіби қызметте алгоритмдеу длинный / короткий"),
    (62,   58,  "Жабдық / Оборудование"),
    (76,   83,  "Салаттар / Приготовление салатов"),
    (75,   82,  "Балық / Приготовление рыбы"),
    (77,   84,  "Жұмыртқа / Приготовление яиц"),
    (74,   81,  "Көкөністер / Приготовление овощей"),
    (78,   85,  "Ұлттық тағамдар / Приготовление нац.блюд"),
    (73,   80,  "Санитарлық / Соблюдение санитарных требований"),
    (79,   86,  "Банкет казахский / Организация банкетов"),
    (116, 117,  "Кредиттік каз / Осуществление рус"),
    (112, 115,  "Ұйымдардың каз / Проведение комплексного анализа рус"),
    (111, 114,  "Қаржылық есептілікті жасауға / Участие в составлении"),
    (53,   91,  "Бағдарламалық жасақтаманы каз / Расчет показателей рус"),
    (35,  120,  "Серверлік ...виртуалдандыру длинный / Виртуалдандыру технологиялары"),
]

# Предметы для полного удаления (нет в источнике)
SUBJECTS_DELETE = [
    (119, "Серверлік операциялық жүйелер — дубль длинного"),
    (121, "Бағдарламалық қамтамасыз ету — не из источника"),
    (101, "Экономикалық информатика — не из источника"),
    (108, "Экономикалық талдау — не из источника"),
    (102, "Ақша, қаржы, несие — не из источника"),
    (99,  "Аудит — не из источника"),
    (104, "Бюджет және бюджет жүйесі — не из источника"),
    (107, "Бюджеттік есеп — не из источника"),
    (103, "Банк ісі — не из источника"),
    (94,  "Материалдық қорлардың есебін жүргізу — не из источника"),
    (57,  "Сырье и материалы — не из источника"),
]

# ─────────────────────────────────────────────────────────────
# СЛИЯНИЕ ПРЕПОДАВАТЕЛЕЙ
# keep=43 (Кабдолова А.Қ.), remove=44 (Қабдулова А.Қ.)
# ─────────────────────────────────────────────────────────────
TEACHER_MERGE = (43, 44)  # keep, remove


def merge_subject(keep_id, remove_id, note):
    print(f"  → [{remove_id}] → [{keep_id}]  ({note})")
    try:
        # Перенести hour_grids
        db.execute(text("""
            UPDATE hour_grids SET subject_id = :keep
            WHERE subject_id = :remove
              AND (group_id, semester_id) NOT IN (
                  SELECT group_id, semester_id FROM hour_grids WHERE subject_id = :keep
              )
        """), {"keep": keep_id, "remove": remove_id})
        db.execute(text("DELETE FROM hour_grids WHERE subject_id = :remove"), {"remove": remove_id})

        # Перенести teacher_subjects
        db.execute(text("""
            UPDATE teacher_subjects SET subject_id = :keep
            WHERE subject_id = :remove
              AND (teacher_id, group_id) NOT IN (
                  SELECT teacher_id, group_id FROM teacher_subjects WHERE subject_id = :keep
              )
        """), {"keep": keep_id, "remove": remove_id})
        db.execute(text("DELETE FROM teacher_subjects WHERE subject_id = :remove"), {"remove": remove_id})

        db.execute(text("DELETE FROM subjects WHERE id = :remove"), {"remove": remove_id})
        print(f"    ✓ Удалён предмет id={remove_id}")
    except Exception as e:
        print(f"    ✗ Ошибка: {e}")
        db.rollback()


def delete_subject(sid, note):
    print(f"  🗑  [{sid}] {note}")
    try:
        db.execute(text("DELETE FROM hour_grids WHERE subject_id = :sid"), {"sid": sid})
        db.execute(text("DELETE FROM teacher_subjects WHERE subject_id = :sid"), {"sid": sid})
        db.execute(text("DELETE FROM subjects WHERE id = :sid"), {"sid": sid})
        print(f"    ✓ Удалён")
    except Exception as e:
        print(f"    ✗ Ошибка: {e}")
        db.rollback()


# ─── Запуск ───

print("=" * 55)
print("  СЛИЯНИЕ ДУБЛЕЙ ПРЕДМЕТОВ")
print("=" * 55)
for keep_id, remove_id, note in SUBJECT_MERGES:
    merge_subject(keep_id, remove_id, note)

print("\n" + "=" * 55)
print("  УДАЛЕНИЕ ЛИШНИХ ПРЕДМЕТОВ")
print("=" * 55)
for sid, note in SUBJECTS_DELETE:
    delete_subject(sid, note)

print("\n" + "=" * 55)
print("  СЛИЯНИЕ ПРЕПОДАВАТЕЛЕЙ")
print("=" * 55)
keep_tid, remove_tid = TEACHER_MERGE
print(f"  → [{remove_tid}] Қабдулова → [{keep_tid}] Кабдолова")
try:
    db.execute(text("""
        UPDATE teacher_subjects SET teacher_id = :keep
        WHERE teacher_id = :remove
          AND (subject_id, group_id) NOT IN (
              SELECT subject_id, group_id FROM teacher_subjects WHERE teacher_id = :keep
          )
    """), {"keep": keep_tid, "remove": remove_tid})
    db.execute(text("DELETE FROM teacher_subjects WHERE teacher_id = :remove"), {"remove": remove_tid})
    db.execute(text("DELETE FROM teachers WHERE id = :remove"), {"remove": remove_tid})
    print(f"  ✓ Слито")
except Exception as e:
    print(f"  ✗ Ошибка: {e}")
    db.rollback()

db.commit()

count_s = db.execute(text("SELECT COUNT(*) FROM subjects")).scalar()
count_t = db.execute(text("SELECT COUNT(*) FROM teachers")).scalar()
print(f"\n{'='*55}")
print(f"  ✅ Готово!")
print(f"  Преподавателей: {count_t}  (было 94, ожидается 93)")
print(f"  Предметов:      {count_s}  (было 124, ожидается ~93)")
print(f"{'='*55}")
db.close()
