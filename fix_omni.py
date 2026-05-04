import re
import os

fname = os.path.join("c:\\Projects\\scheduleSYS\\омни", "Обновленная главная бдшка.sql")
with open(fname, 'r', encoding='utf-8') as f:
    sql = f.read()

# Find all subject names expected
subjects_expected = set(re.findall(r"SELECT id FROM subjects WHERE name='([^']+)'", sql))

# Find the existing INSERT INTO subjects block
match = re.search(r"INSERT INTO subjects \(id, name\) VALUES(.+?);", sql, re.DOTALL)
if match:
    values_block = match.group(1)
    # Find existing names
    existing = set(re.findall(r"\(\d+,\s*'([^']+)'\)", values_block))
    
    missing = subjects_expected - existing
    print(f"Missing subjects: {len(missing)}")
    
    if missing:
        # Find the max ID
        ids = [int(i) for i in re.findall(r"\((\d+),", values_block)]
        next_id = max(ids) + 1 if ids else 1
        
        new_lines = []
        for m in sorted(list(missing)):
            new_lines.append(f"({next_id}, '{m}')")
            next_id += 1
            
        modified_block = values_block.rstrip()
        # insert a comma before appending
        modified_block += ",\n" + ",\n".join(new_lines)
        
        new_sql = sql.replace(match.group(0), f"INSERT INTO subjects (id, name) VALUES{modified_block};")
        
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(new_sql)
        print("Fixed sql.")
else:
    print("Could not find subjects INSERT statement.")
