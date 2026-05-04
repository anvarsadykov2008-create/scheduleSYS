from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

with open("export.txt", "w", encoding="utf-8") as f:
    f.write("=== ПРЕДМЕТЫ ===\n")
    rows = db.execute(text("SELECT name FROM subjects ORDER BY name")).fetchall()
    for i, r in enumerate(rows, 1):
        f.write(f"{i}. {r[0]}\n")

    f.write("\n=== ПРЕПОДАВАТЕЛИ ===\n")
    rows = db.execute(text("SELECT full_name FROM teachers ORDER BY full_name")).fetchall()
    for i, r in enumerate(rows, 1):
        f.write(f"{i}. {r[0]}\n")

    f.write("\n=== ГРУППЫ ===\n")
    rows = db.execute(text("SELECT name, course FROM groups ORDER BY name")).fetchall()
    for i, r in enumerate(rows, 1):
        f.write(f"{i}. {r[0]}  (курс {r[1]})\n")

db.close()
print("Готово! Файл: backend\\export.txt")
