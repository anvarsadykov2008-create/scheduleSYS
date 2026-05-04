import re

file_path = 'app/models/models.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace primary keys: *_id = Column(BigInteger, primary_key=True
text = re.sub(r'(\w+_id)\s*=\s*Column\(BigInteger, primary_key=True', r'\1 = Column("id", BigInteger, primary_key=True', text)
text = re.sub(r'(\w+_id)\s*=\s*Column\(Integer, primary_key=True', r'\1 = Column("id", Integer, primary_key=True', text)

# Replace Foreign Keys
text = re.sub(r'ForeignKey\("([^"]+)\.\w+_id"\)', r'ForeignKey("\1.id")', text)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Models patched successfully.")
