import sqlite3
import os

db_path = r'c:\Projects\scheduleSYS\омни\ready_schedule.db'
if not os.path.exists(db_path):
    print('DB not found!')
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    for t in tables:
        t_name = t[0]
        cur.execute(f'SELECT count(*) FROM {t_name}')
        count = cur.fetchone()[0]
        print(f'{t_name}: {count} rows')
