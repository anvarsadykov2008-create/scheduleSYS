import re
import os

fname = os.path.join("c:\\Projects\\scheduleSYS\\омни", "Обновленная главная бдшка.sql")
with open(fname, 'r', encoding='utf-8') as f:
    sql = f.read()

match = re.search(r"INSERT INTO curriculum \(group_id, subject_id, theory_hours, practice_hours, semester\) VALUES(.+?);", sql, re.DOTALL)

if match:
    block = match.group(0)
    if "ON CONFLICT DO NOTHING" not in block:
        new_block = block[:-1] + "\nON CONFLICT DO NOTHING;"
        sql = sql.replace(block, new_block)
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(sql)
        print("Added ON CONFLICT DO NOTHING to curriculum insert.")
    else:
        print("Already has ON CONFLICT.", "Found:")
else:
    print("Could not find curriculum INSERT block.")
