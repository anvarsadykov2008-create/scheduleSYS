DO $$ BEGIN
    CREATE TYPE userrole_new AS ENUM ('ADMIN', 'DISPATCHER', 'TEACHER', 'STUDENT', 'MANAGEMENT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- If the type already exists, we might need to use its name.
-- But the existing script had 'STUDENT', 'TEACHER', 'ADMIN', 'DISPATCHER', 'MANAGEMENT' (uppercase).
-- Wait, let's check what's in the DB now.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'STUDENT',
    teacher_id BIGINT REFERENCES teachers(id) ON DELETE SET NULL,
    group_id BIGINT REFERENCES groups(id) ON DELETE SET NULL,
    full_name VARCHAR(200),
    is_not_student BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(50) PRIMARY KEY,
    value VARCHAR(255),
    description VARCHAR(200)
);
