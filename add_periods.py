from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:87474981272@localhost:5432/schedulesysss')
engine.execute("INSERT INTO academic_periods (code, name, academic_year, term_no, start_date, end_date, weeks_in_period) VALUES ('2025-2026-S1', '1 семестр', '2025-2026', 1, '2025-09-01', '2025-12-31', 16), ('2025-2026-S2', '2 семестр', '2025-2026', 2, '2026-01-15', '2026-06-15', 18)")
print("Inserted successfully")
