
"""
SQLAlchemy-модели, соответствующие производственной схеме БД (PostgreSQL).
В PostgreSQL все PK-колонки называются "id" — Column("id", ...) правильно маппит
Python-атрибут (напр. academic_period_id) → реальную колонку id в БД.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Date,
    Text, JSON, DateTime, BigInteger, SmallInteger, Time,
    Numeric, UniqueConstraint, PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SAEnum
from datetime import datetime
import enum

from app.database import Base


# ──────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN      = "ADMIN"
    DISPATCHER = "DISPATCHER"
    TEACHER    = "TEACHER"
    STUDENT    = "STUDENT"
    MANAGEMENT = "MANAGEMENT"


# ──────────────────────────────────────────────────────────────────
# Reference catalogs
# ──────────────────────────────────────────────────────────────────

class Department(Base):
    __tablename__ = "departments"
    department_id = Column("id", BigInteger, primary_key=True, index=True)
    code          = Column(String(30), nullable=False, unique=True)
    name          = Column(String(200), nullable=False, unique=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    specialties = relationship("Specialty", back_populates="department")


class Specialty(Base):
    __tablename__ = "specialties"
    specialty_id  = Column("id", BigInteger, primary_key=True, index=True)
    department_id = Column(BigInteger, ForeignKey("departments.id"), nullable=False)
    code          = Column(String(30), nullable=False)
    name          = Column(String(200), nullable=False)
    qualification = Column(String(100))
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    department = relationship("Department", back_populates="specialties")
    groups     = relationship("Group",      back_populates="specialty")


class AcademicPeriod(Base):
    __tablename__ = "academic_periods"
    academic_period_id = Column("id", BigInteger, primary_key=True, index=True)
    code               = Column(String(50), nullable=False, unique=True)
    name               = Column(String(200), nullable=False)
    academic_year      = Column(String(20), nullable=False)
    term_no            = Column(SmallInteger, nullable=False)
    start_date         = Column(Date, nullable=False)
    end_date           = Column(Date, nullable=False)
    weeks_in_period    = Column(Numeric(6, 2), nullable=False)
    is_active          = Column(Boolean, default=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at         = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def id(self): return self.academic_period_id


class LessonType(Base):
    __tablename__ = "lesson_types"
    lesson_type_id      = Column("id", BigInteger, primary_key=True, index=True)
    code                = Column(String(20), nullable=False, unique=True)
    name                = Column(String(100), nullable=False, unique=True)
    is_lab              = Column(Boolean, default=False)
    requires_room_match = Column(Boolean, default=True)
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())


class RoomType(Base):
    __tablename__ = "room_types"
    room_type_id = Column("id", BigInteger, primary_key=True, index=True)
    code         = Column(String(30), nullable=False, unique=True)
    name         = Column(String(100), nullable=False, unique=True)
    is_lab       = Column(Boolean, default=False)
    is_active    = Column(Boolean, default=True)
    notes        = Column(Text)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


class TimeSlot(Base):
    __tablename__ = "time_slots"
    time_slot_id   = Column("id", BigInteger, primary_key=True, index=True)
    day_of_week    = Column(SmallInteger, nullable=False)
    slot_number    = Column(SmallInteger, nullable=False)
    start_time     = Column(Time, nullable=False)
    end_time       = Column(Time, nullable=False)
    academic_hours = Column(Numeric(5, 2), nullable=False, default=2.00)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("day_of_week", "slot_number", name="uq_time_slots_day_slot"),
    )

    @property
    def id(self): return self.time_slot_id


# ──────────────────────────────────────────────────────────────────
# Core entities
# ──────────────────────────────────────────────────────────────────

class Teacher(Base):
    __tablename__ = "teachers"
    teacher_id    = Column("id", BigInteger, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True)
    last_name     = Column(String(100), nullable=False)
    first_name    = Column(String(100), nullable=False)
    middle_name   = Column(String(100))
    is_active     = Column(Boolean, default=True)
    default_monthly_hour_limit  = Column(Numeric(7, 2))
    default_weekly_hour_limit   = Column(Numeric(6, 2))
    default_daily_hour_limit    = Column(Numeric(6, 2))
    default_daily_lessons_limit = Column(SmallInteger)
    notes         = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users            = relationship("User",           back_populates="teacher_rel")
    teacher_subjects = relationship("TeacherSubject", back_populates="teacher")
    teacher_rooms    = relationship("TeacherRoom",    back_populates="teacher", cascade="all, delete-orphan")

    @property
    def id(self): return self.teacher_id

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)


class Subject(Base):
    __tablename__ = "subjects"
    subject_id   = Column("id", BigInteger, primary_key=True, index=True)
    code         = Column(String(50), unique=True)
    name         = Column(String(200), nullable=False, unique=True)
    subject_kind = Column(String(30), nullable=False, default='standard')
    is_active    = Column(Boolean, default=True)
    notes        = Column(Text)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    teacher_subjects = relationship("TeacherSubject", back_populates="subject")

    @property
    def id(self): return self.subject_id


class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"
    # PK — identity-колонка 'id' в PostgreSQL
    teacher_subject_id = Column("id", BigInteger, primary_key=True, index=True)
    teacher_id    = Column(BigInteger, ForeignKey("teachers.id"), nullable=False)
    subject_id    = Column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    lesson_type_id = Column(BigInteger, ForeignKey("lesson_types.id"))
    is_primary    = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    note          = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("Teacher", back_populates="teacher_subjects")
    subject = relationship("Subject", back_populates="teacher_subjects")


class Group(Base):
    __tablename__ = "groups"
    group_id           = Column("id", BigInteger, primary_key=True, index=True)
    specialty_id       = Column(BigInteger, ForeignKey("specialties.id"), nullable=False)
    code               = Column(String(50), nullable=False, unique=True)
    name               = Column(String(100), nullable=False)
    course_no          = Column(SmallInteger, nullable=False)
    student_count      = Column(Integer)
    max_daily_lessons  = Column(SmallInteger, nullable=False, default=4)
    is_active          = Column(Boolean, default=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at         = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    specialty = relationship("Specialty", back_populates="groups")
    users     = relationship("User",      back_populates="group_rel")

    @property
    def id(self): return self.group_id


class Room(Base):
    __tablename__ = "rooms"
    room_id      = Column("id", BigInteger, primary_key=True, index=True)
    room_type_id = Column(BigInteger, ForeignKey("room_types.id"), nullable=False)
    code         = Column(String(30), nullable=False)
    name         = Column(String(100), nullable=False)
    # поле building — NOT NULL в SQL-схеме
    building     = Column(String(100), nullable=False, server_default='Главный корпус')
    floor        = Column(SmallInteger)
    capacity     = Column(Integer)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def id(self): return self.room_id


class TeacherRoom(Base):
    __tablename__ = "teacher_rooms"
    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    teacher_id = Column(BigInteger, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    room_id    = Column(BigInteger, ForeignKey("rooms.id",    ondelete="CASCADE"), nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("teacher_id", "room_id", name="uq_teacher_room"),)

    teacher = relationship("Teacher", back_populates="teacher_rooms")
    room    = relationship("Room")


class Curriculum(Base):
    """Модель для group_subject_load в новой схеме"""
    __tablename__ = "group_subject_load"
    group_subject_load_id = Column("id", BigInteger, primary_key=True, index=True)
    academic_period_id    = Column(BigInteger, ForeignKey("academic_periods.id"), nullable=False)
    group_id              = Column(BigInteger, ForeignKey("groups.id"), nullable=False)
    subject_id            = Column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    lesson_type_id        = Column(BigInteger, ForeignKey("lesson_types.id"), nullable=False)
    planned_weekly_hours  = Column(Numeric(5, 2), nullable=False)
    total_hours           = Column(Numeric(7, 2), nullable=False)
    preferred_teacher_id  = Column(BigInteger, ForeignKey("teachers.id"))
    is_mandatory          = Column(Boolean, default=True)
    notes                 = Column(Text)

    @property
    def id(self): return self.group_subject_load_id


# ──────────────────────────────────────────────────────────────────
# Schedule generation / timetable (production schema)
# ──────────────────────────────────────────────────────────────────

class ScheduleGenerationRun(Base):
    __tablename__ = "schedule_generation_runs"

    generation_run_id  = Column("id", BigInteger, primary_key=True, index=True)
    academic_period_id = Column(BigInteger, ForeignKey("academic_periods.id"), nullable=False)
    # SQL CHECK: ('queued','running','completed','failed','cancelled')
    status             = Column(String(20), nullable=False, default="queued")
    requested_by       = Column(String(100))
    generator_version  = Column(String(50))
    parameters         = Column(JSON, nullable=False, default=dict)
    created_schedule_rows = Column(Integer, nullable=False, default=0)
    detected_conflicts = Column(Integer, nullable=False, default=0)
    requested_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at         = Column(DateTime(timezone=True))
    finished_at        = Column(DateTime(timezone=True))
    notes              = Column(Text)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at         = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def id(self): return self.generation_run_id


class ScheduleConflictLog(Base):
    __tablename__ = "schedule_conflicts_log"

    schedule_conflict_id = Column("id", BigInteger, primary_key=True, index=True)
    generation_run_id    = Column(BigInteger, ForeignKey("schedule_generation_runs.id"))
    academic_period_id   = Column(BigInteger, ForeignKey("academic_periods.id"), nullable=False)
    schedule_id          = Column(BigInteger)
    conflict_type        = Column(String(50), nullable=False)
    severity             = Column(String(20), nullable=False, default="warning")
    message              = Column(Text, nullable=False)
    context              = Column(JSON, nullable=False, default=dict)
    teacher_id           = Column(BigInteger)
    group_id             = Column(BigInteger)
    room_id              = Column(BigInteger)
    time_slot_id         = Column(BigInteger)
    created_at           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @property
    def id(self): return self.schedule_conflict_id


class ScheduleRow(Base):
    __tablename__ = "schedule"

    schedule_id           = Column("id", BigInteger, primary_key=True, index=True)
    academic_period_id    = Column(BigInteger, ForeignKey("academic_periods.id"), nullable=False)
    group_subject_load_id = Column(BigInteger, ForeignKey("group_subject_load.id"), nullable=False)
    group_id              = Column(BigInteger, ForeignKey("groups.id"), nullable=False)
    subgroup_id           = Column(BigInteger)
    subject_id            = Column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    lesson_type_id        = Column(BigInteger, ForeignKey("lesson_types.id"), nullable=False)
    teacher_id            = Column(BigInteger, ForeignKey("teachers.id"), nullable=False)
    room_id               = Column(BigInteger, ForeignKey("rooms.id"), nullable=False)
    time_slot_id          = Column(BigInteger, ForeignKey("time_slots.id"), nullable=False)
    source_run_id         = Column(BigInteger, ForeignKey("schedule_generation_runs.id"))
    # SQL CHECK: ('draft','planned','published','locked','cancelled')
    status                = Column(String(20), nullable=False, default="draft")
    notes                 = Column(Text)
    created_at            = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at            = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    group      = relationship("Group")
    subject    = relationship("Subject")
    teacher    = relationship("Teacher")
    room       = relationship("Room")
    time_slot  = relationship("TimeSlot")

    @property
    def id(self): return self.schedule_id


# ──────────────────────────────────────────────────────────────────
# Auth / system
# ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    teacher_id    = Column(BigInteger, ForeignKey("teachers.id"), nullable=True)
    group_id      = Column(BigInteger, ForeignKey("groups.id"),   nullable=True)
    full_name     = Column(String(200), nullable=True)
    is_not_student = Column(Boolean, default=False)

    teacher_rel = relationship("Teacher", back_populates="users")
    group_rel   = relationship("Group",   back_populates="users")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    action    = Column(String(50), nullable=False)
    entity    = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details   = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemSetting(Base):
    __tablename__ = "app_settings"
    key         = Column(String(50), primary_key=True)
    value       = Column(String(255))
    description = Column(String(200))


# ──────────────────────────────────────────────────────────────────
# Compatibility aliases
# ──────────────────────────────────────────────────────────────────
Course    = None
Classroom = Room
HourGrid  = Curriculum
ScheduleEntry = None
