import re
with open('college_schedule_production_schema.sql', 'r', encoding='utf-8') as f:
    orig = f.read()

# 1. Replace PK definitions
new_content = re.sub(r'(?<=^\s{4})\w+_id(?=\s+BIGINT\s+GENERATED)', 'id', orig, flags=re.MULTILINE)

# 2. Replace REFERENCES tablename(table_id) with REFERENCES tablename(id)
# This includes ON DELETE cascades etc.
new_content = re.sub(r'REFERENCES\s+([a-zA-Z0-9_]+)\(\w+_id\)', r'REFERENCES \1(id)', new_content)

print(f'PK changes: {len(re.findall(r"(?<=^\s{4})\w+_id(?=\s+BIGINT\s+GENERATED)", orig, flags=re.MULTILINE))}')
print(f'FK changes: {len(re.findall(r"REFERENCES\s+([a-zA-Z0-9_]+)\(\w+_id\)", orig))}')

with open('college_schedule_production_schema_v2.sql', 'w', encoding='utf-8') as f:
    f.write(new_content)
