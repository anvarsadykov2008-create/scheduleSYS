# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy import text

engine = create_engine('postgresql://postgres:87474981272@localhost:5432/schedulesysss')
with engine.connect() as conn:
    conn.execute(text("UPDATE academic_periods SET name='1 семестр' WHERE code='2025-2026-S1'"))
    conn.execute(text("UPDATE academic_periods SET name='2 семестр' WHERE code='2025-2026-S2'"))
print("Updated successfully")
