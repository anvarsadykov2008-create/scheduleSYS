from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:87474981272@localhost:5432/schedulesysss')

query = """
INSERT INTO group_subject_load 
(academic_period_id, group_id, subject_id, lesson_type_id, planned_weekly_hours, total_hours, preferred_teacher_id, is_mandatory, notes)
SELECT 
    3, -- New academic_period_id (2 семестр)
    group_id, 
    subject_id, 
    lesson_type_id, 
    planned_weekly_hours, 
    total_hours, 
    preferred_teacher_id, 
    is_mandatory, 
    notes
FROM group_subject_load
WHERE academic_period_id = 1
ON CONFLICT DO NOTHING;
"""

with engine.connect() as conn:
    conn.execute(text(query))
print("Copied curriculum data to semester 2")
