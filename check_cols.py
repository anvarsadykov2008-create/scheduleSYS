from sqlalchemy import text
from backend.app.database import engine

with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'schedule'"))
    cols = [r[0] for r in res]
    print('schedule columns:', cols)
