import re
import os

fname = os.path.join("c:\\Projects\\scheduleSYS\\омни", "Обновленная главная бдшка.sql")
with open(fname, 'r', encoding='utf-8') as f:
    sql = f.read()

# Find all group names expected
groups_expected = set(re.findall(r"SELECT id FROM groups WHERE name='([^']+)'", sql))

# Find the existing INSERT INTO groups block
match = re.search(r"INSERT INTO groups \(name, course_id\) VALUES(.+?);", sql, re.DOTALL)
if match:
    values_block = match.group(1)
    # Find existing names
    existing = set(re.findall(r"\('([^']+)',\s*\d+\)", values_block))
    
    missing = groups_expected - existing
    print(f"Missing groups: {len(missing)}")
    
    if missing:
        new_lines = []
        for m in sorted(list(missing)):
            # guess course_id from group name (e.g. 'WEB1-1' -> 1)
            course_id = 1
            cmatch = re.search(r'(\d)-', m)
            if cmatch:
                course_id = int(cmatch.group(1))
            new_lines.append(f"('{m}', {course_id})")
            
        modified_block = values_block.rstrip()
        modified_block += ",\n" + ",\n".join(new_lines)
        
        new_sql = sql.replace(match.group(0), f"INSERT INTO groups (name, course_id) VALUES{modified_block};")
        
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(new_sql)
        print("Fixed sql. Added groups:", list(missing))
else:
    print("Could not find groups INSERT statement.")
