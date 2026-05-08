"""
Pydantic-схемы для scheduleSYS.
Соответствуют реальной схеме БД (Обновленная главная бдшка.sql).
"""

from pydantic import BaseModel, ConfigDict
from pydantic import Field, AliasChoices
from typing import Optional, List
from datetime import time, datetime
from enum import Enum


# ──────────────────────── Enums ────────────────────────

class UserRoleEnum(str, Enum):
    ADMIN      = "ADMIN"
    DISPATCHER = "DISPATCHER"
    TEACHER    = "TEACHER"
    STUDENT    = "STUDENT"
    MANAGEMENT = "MANAGEMENT"


# ──────────────────────── Auth ────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRoleEnum
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None
    full_name: Optional[str] = None
    is_not_student: bool = False
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────── Subject ────────────────────────

class SubjectBase(BaseModel):
    name: str

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = None

class SubjectResponse(SubjectBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────── Teacher ────────────────────────

class TeacherBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    notes: Optional[str] = None
    default_weekly_hour_limit: Optional[float] = None
    default_daily_lessons_limit: Optional[int] = None

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    notes: Optional[str] = None
    default_weekly_hour_limit: Optional[float] = None
    default_daily_lessons_limit: Optional[int] = None

class TeacherResponse(TeacherBase):
    id: int
    full_name: str
    model_config = ConfigDict(from_attributes=True)


class TeacherSubjectBase(BaseModel):
    teacher_id: int
    subject_id: int

class TeacherSubjectCreate(TeacherSubjectBase):
    pass

class TeacherSubjectResponse(TeacherSubjectBase):
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────── Course ────────────────────────

class CourseResponse(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────── Group ────────────────────────

class GroupBase(BaseModel):
    name: str
    code: Optional[str] = None
    specialty_id: Optional[int] = None
    course_no: Optional[int] = None
    student_count: Optional[int] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    specialty_id: Optional[int] = None
    course_no: Optional[int] = None
    student_count: Optional[int] = None

class GroupResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    specialty_id: Optional[int] = None
    course_no: Optional[int] = None
    student_count: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────── Classroom ────────────────────────

class ClassroomBase(BaseModel):
    code: str
    name: str
    # [FIX] building добавлен — поле NOT NULL в SQL-схеме
    building: str = "Главный корпус"
    floor: Optional[int] = None
    capacity: Optional[int] = None
    room_type_id: Optional[int] = None

class ClassroomCreate(ClassroomBase):
    pass

class ClassroomUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[int] = None
    capacity: Optional[int] = None
    room_type_id: Optional[int] = None

class ClassroomResponse(BaseModel):
    id: int
    code: str
    name: str
    building: str = "Главный корпус"
    floor: Optional[int] = None
    capacity: Optional[int] = None
    room_type_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────── Curriculum / HourGrid ────────────────────────
# [FIX F-03 / D-07] Схемы приведены к реальным полям модели Curriculum (group_subject_load).
# Старые поля theory_hours / practice_hours / semester не существуют в БД.

class CurriculumBase(BaseModel):
    group_id: int
    subject_id: int
    lesson_type_id: int
    academic_period_id: int
    planned_weekly_hours: float = 2.0
    total_hours: float = 32.0
    preferred_teacher_id: Optional[int] = None
    is_mandatory: bool = True
    notes: Optional[str] = None

class CurriculumCreate(CurriculumBase):
    pass

class CurriculumUpdate(BaseModel):
    planned_weekly_hours: Optional[float] = None
    total_hours: Optional[float] = None
    preferred_teacher_id: Optional[int] = None
    is_mandatory: Optional[bool] = None
    notes: Optional[str] = None

class CurriculumResponse(BaseModel):
    id: int
    group_id: int
    subject_id: int
    lesson_type_id: int
    academic_period_id: int
    planned_weekly_hours: float
    total_hours: float
    preferred_teacher_id: Optional[int] = None
    is_mandatory: bool
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Alias для совместимости с роутером hour_grid
HourGridBase     = CurriculumBase
HourGridCreate   = CurriculumCreate
HourGridUpdate   = CurriculumUpdate
HourGridResponse = CurriculumResponse


# ──────────────────────── TimeSlot / DayOfWeek ────────────────────────

class DayOfWeekResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class TimeSlotBase(BaseModel):
    slot_number: int
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotUpdate(BaseModel):
    slot_number: Optional[int] = None
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class TimeSlotResponse(BaseModel):
    id: int
    slot_number: int
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────── Schedule ────────────────────────

class ScheduleEntryBase(BaseModel):
    group_id: int
    teacher_id: int
    subject_id: int
    classroom_id: int
    day_id: int
    slot_id: int
    version_id: int

class ScheduleEntryCreate(ScheduleEntryBase):
    pass

class ScheduleEntryUpdate(BaseModel):
    group_id: Optional[int] = None
    teacher_id: Optional[int] = None
    subject_id: Optional[int] = None
    classroom_id: Optional[int] = None
    day_id: Optional[int] = None
    slot_id: Optional[int] = None

class ScheduleEntryResponse(ScheduleEntryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ScheduleEntryDetailed(BaseModel):
    id: int
    group_name: str
    subject_name: str
    teacher_name: str
    classroom_name: str
    day_name: str
    slot_number: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class ScheduleGenerateRequest(BaseModel):
    semester_id: int = Field(validation_alias=AliasChoices("semester_id", "semester"))
    description: Optional[str] = None

class UnplacedEntry(BaseModel):
    group: str
    subject: str
    teacher: str
    lesson_type: str = ""
    reason: str

class ScheduleGenerateResponse(BaseModel):
    version_id: int
    placed_count: int
    total_count: int
    unplaced: List[UnplacedEntry] = []
    warnings: List[str] = []


# ──────────────────────── Stub schemas (referenced by old routers) ────────────────────────

class DepartmentCreate(BaseModel):
    name: str
    code: str

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

class DepartmentResponse(BaseModel):
    id: int = Field(validation_alias=AliasChoices('id', 'department_id'))
    name: str
    code: str
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SpecialtyBase(BaseModel):
    name: str
    code: str
    department_id: int

class SubgroupCreate(BaseModel):
    name: str

class SubgroupResponse(BaseModel):
    id: int
    group_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class AcademicPeriodCreate(BaseModel):
    name: str
    code: Optional[str] = None
    academic_year: Optional[str] = None
    term_no: Optional[int] = None

class AcademicPeriodUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class AcademicPeriodResponse(BaseModel):
    id: int = Field(validation_alias=AliasChoices('id', 'academic_period_id'))
    name: str
    code: Optional[str] = None
    academic_year: Optional[str] = None
    term_no: Optional[int] = None
    is_active: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class AcademicYearCreate(BaseModel):
    name: str

class AcademicYearUpdate(BaseModel):
    name: Optional[str] = None

class AcademicYearResponse(BaseModel):
    id: int
    name: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SemesterCreate(BaseModel):
    academic_year_id: int
    number: int

class SemesterUpdate(BaseModel):
    number: Optional[int] = None

class SemesterResponse(BaseModel):
    id: int
    academic_year_id: int
    number: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    academic_year: Optional[AcademicYearResponse] = None
    model_config = ConfigDict(from_attributes=True)

class ScheduleVersionCreate(BaseModel):
    semester_id: int
    description: Optional[str] = None

class ScheduleVersionUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None

class ScheduleVersionResponse(BaseModel):
    id: int
    semester_id: int
    status: str
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TeacherAvailabilityCreate(BaseModel):
    teacher_id: int
    time_slot_id: int

class TeacherAvailabilityResponse(BaseModel):
    id: int
    teacher_id: int
    model_config = ConfigDict(from_attributes=True)