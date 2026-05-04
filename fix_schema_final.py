import re

with open('college_schedule_production_schema.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# 1. Заменяем определения первичных ключей: "table_id BIGINT ..." -> "id BIGINT ..."
# Ищем паттерн внутри CREATE TABLE
sql = re.sub(r'(\s+)([a-zA-Z0-9_]+)_id(\s+BIGINT\s+GENERATED)', r'\1id\3', sql)

# 2. Заменяем ссылки во внешних ключах: "REFERENCES table(table_id)" -> "REFERENCES table(id)"
sql = re.sub(r'REFERENCES\s+([a-zA-Z0-9_]+)\s*\(\s*[a-zA-Z0-9_]+_id\s*\)', r'REFERENCES \1(id)', sql)

# 3. Заменяем имена столбцов в операторах INSERT: "INSERT INTO table (table_id, ...)" -> "INSERT INTO table (id, ...)"
# Это сложнее, так как нужно попасть именно в первый столбец, если он совпадает с именем таблицы
def fix_insert(match):
    table_name = match.group(1)
    # Если столбец называется table_id (или очень похоже), меняем на id
    # Но в скрипте они обычно называются именно так
    return f'INSERT INTO {table_name} (id,'

sql = re.sub(r'INSERT INTO ([a-zA-Z0-9_]+) \([a-zA-Z0-9_]+_id,', fix_insert, sql)

with open('college_schedule_production_schema_v3.sql', 'w', encoding='utf-8') as f:
    f.write(sql)

print("Скрипт версии v3 создан. Столбцы переименованы в 'id'.")
