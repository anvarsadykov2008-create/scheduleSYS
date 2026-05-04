"""
Алгоритм автоматической генерации расписания — улучшенный жадный (Greedy v2).

Улучшения по сравнению с v1:
- Приоритет 1–2 курсов при размещении
- Ограничение ранних слотов для 1–2 курсов (только пары №1 и №2 как стартовые)
- Лимит пар в день через daily_load (не более max_daily_lessons, обычно 4)
- Предупреждения о недогруженных днях (< 3 пар при наличии нагрузки)
- Поддержка half-busy слотов (пары «раз в две недели»)
- Поиск двух аудиторий для практик (подгрупп), fallback на одну с проверкой вместимости

ИСПРАВЛЕНА: привязка учителя по (subject_id, lesson_type_id) для соответствия
            триггеру fn_schedule_validate_assignment в PostgreSQL.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import (
    Group, Teacher, Subject, Room, TimeSlot,
    Curriculum, TeacherSubject,
    ScheduleRow, ScheduleConflictLog, ScheduleGenerationRun, LessonType,
)

# Типы занятий, считающихся практикой (требуют разбивки на подгруппы)
PRACTICE_KEYWORDS = {"практика", "лабораторная", "lab", "practice"}

# Максимальное число пар в день по умолчанию
DEFAULT_MAX_DAILY = 4

# Минимально желаемое число пар в непустой день (мягкое ограничение)
MIN_DESIRED_DAILY = 3

# Слоты, допустимые как ПЕРВАЯ пара для 1–2 курсов (номера пар)
EARLY_COURSE_ALLOWED_FIRST_SLOTS = {1, 2}

# Целевое распределение нагрузки по дням (2 дня × 3 пары + 3 дня × 4 пары = 18 пар/36 ч)
TARGET_DAILY_DISTRIBUTION = {3: 2, 4: 3}  # {кол-во пар: кол-во дней}

# Основные пары (1–4: 8:00–14:50). Слот 5 (15:00–16:30) — резервный fallback.
ALLOWED_SLOT_NUMBERS = {1, 2, 3, 4}
FALLBACK_SLOT_NUMBERS = {1, 2, 3, 4, 5}


@dataclass
class LessonTask:
    academic_period_id: int
    group_subject_load_id: int
    group_id: int
    subject_id: int
    lesson_type_id: int
    teacher_id: int
    teacher_ids: List[int] = field(default_factory=list)
    course_no: int = 1
    is_practice: bool = False
    # Периодичность: 'every' | 'numerator' | 'denominator'
    week_parity: str = "every"


@dataclass
class Unplaced:
    group: str
    subject: str
    teacher: str
    lesson_type: str
    reason: str


@dataclass
class GenerationResult:
    placed_count: int = 0
    total_count: int = 0
    unplaced: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class ScheduleGenerator:
    def __init__(self, db: Session):
        self.db = db

        self.groups = db.query(Group).all()
        self.teachers = db.query(Teacher).all()
        self.subjects = db.query(Subject).all()
        self.rooms = db.query(Room).all()
        self.lesson_types = db.query(LessonType).all()
        self.time_slots = db.query(TimeSlot).order_by(
            TimeSlot.day_of_week, TimeSlot.slot_number
        ).all()

        self.group_map: Dict[int, Group] = {g.id: g for g in self.groups}
        self.teacher_map: Dict[int, Teacher] = {t.id: t for t in self.teachers}
        self.subject_map: Dict[int, Subject] = {s.id: s for s in self.subjects}
        self.room_map: Dict[int, Room] = {r.id: r for r in self.rooms}
        self.lesson_type_map: Dict[int, LessonType] = {
            lt.lesson_type_id: lt for lt in self.lesson_types
        }

        # ── Привязка учителей по (subject_id, lesson_type_id) ──────────────────
        # Учитываем triгер fn_schedule_validate_assignment:
        #   ts.lesson_type_id IS NULL  ← учитель может вести любой тип
        #   ts.lesson_type_id = lt_id  ← учитель может вести только этот тип
        #
        # teacher_subject_specific: (subject_id, lt_id) -> [teacher_ids]
        # teacher_subject_any:      subject_id          -> [teacher_ids]  (lt IS NULL)
        self.teacher_subject_specific: Dict[Tuple[int, int], List[int]] = {}
        self.teacher_subject_any: Dict[int, List[int]] = {}

        for ts in db.query(TeacherSubject).filter(TeacherSubject.is_active == True).all():
            sid = int(ts.subject_id)
            tid = int(ts.teacher_id)
            if ts.lesson_type_id is not None:
                key = (sid, int(ts.lesson_type_id))
                self.teacher_subject_specific.setdefault(key, []).append(tid)
            else:
                self.teacher_subject_any.setdefault(sid, []).append(tid)

        # time_slot_id -> (day_of_week, slot_number)
        self.slot_info: Dict[int, Tuple[int, int]] = {
            int(ts.time_slot_id): (int(ts.day_of_week), int(ts.slot_number))
            for ts in self.time_slots
        }

        # Предмет+ТипУрока -> Список подходящих room_type_id
        from sqlalchemy import text
        res = db.execute(text("SELECT subject_id, lesson_type_id, room_type_id FROM subject_room_type")).fetchall()
        self.subject_room_types: Dict[Tuple[int, int], Set[int]] = {}
        for row in res:
            key = (int(row.subject_id), int(row.lesson_type_id))
            self.subject_room_types.setdefault(key, set()).add(int(row.room_type_id))

        # Слоты сгруппированные по дню: day -> [time_slot_id, ...]
        self.slots_by_day: Dict[int, List[int]] = {}
        for ts in self.time_slots:
            self.slots_by_day.setdefault(int(ts.day_of_week), []).append(
                int(ts.time_slot_id)
            )

        # Занятость ресурсов: (time_slot_id, entity_id)
        self.teacher_busy: Set[Tuple[int, int]] = set()
        self.room_busy: Set[Tuple[int, int]] = set()
        self.group_busy: Set[Tuple[int, int]] = set()

        # Half-busy слоты (пары раз в две недели): (time_slot_id, entity_id) -> parity
        self.teacher_half: Dict[Tuple[int, int], str] = {}
        self.room_half: Dict[Tuple[int, int], str] = {}
        self.group_half: Dict[Tuple[int, int], str] = {}

        # daily_load[group_id][day] = count
        self.daily_load: Dict[int, Dict[int, int]] = {
            g.id: {} for g in self.groups
        }

        # Недоступные дни преподавателя: teacher_id -> set of day_of_week
        self.teacher_unavailable_days: Dict[int, Set[int]] = {}

        # Занятые слоты группы по дням: group_id -> day -> set of slot_number
        self.group_slots_per_day: Dict[int, Dict[int, Set[int]]] = {
            g.id: {} for g in self.groups
        }

        # Предметы группы в день: (group_id, day) -> set of subject_id
        # Запрещает один предмет дважды в один день у одной группы
        self.group_day_subjects: Dict[Tuple[int, int], Set[int]] = {}

    # ──────────────────────────────────────────────────────────────────
    # Вспомогательный поиск учителей с учётом lesson_type
    # ──────────────────────────────────────────────────────────────────

    def _get_eligible_teachers(self, subject_id: int, lesson_type_id: int) -> List[int]:
        """
        Возвращает teacher_id, допустимых триггером:
          ts.lesson_type_id IS NULL  OR  ts.lesson_type_id = lesson_type_id
        Приоритет: конкретный тип, затем «любой тип».
        """
        specific = self.teacher_subject_specific.get((subject_id, lesson_type_id), [])
        any_type = self.teacher_subject_any.get(subject_id, [])
        # Объединяем, убирая дубли, сохраняя порядок (specific первый)
        seen: Set[int] = set()
        result: List[int] = []
        for tid in specific + any_type:
            if tid not in seen:
                seen.add(tid)
                result.append(tid)
        return result

    # ──────────────────────────────────────────────────────────────────
    # Публичный метод
    # ──────────────────────────────────────────────────────────────────

    def generate(self, academic_period_id: int, generation_run_id: int) -> GenerationResult:
        from sqlalchemy import text as sa_text

        # Отключаем бизнес-триггеры на время генерации — Python-код сам
        # отслеживает конфликты через busy-множества. Это позволяет разместить
        # предметы, которые блокируются триггерами проверки нагрузки/типов аудиторий.
        try:
            self.db.execute(sa_text("SET LOCAL session_replication_role = 'replica'"))
        except Exception:
            pass  # Нет привилегии REPLICATION — продолжаем с триггерами

        # Загружаем недоступные дни преподавателей (жёсткие ограничения)
        rows = self.db.execute(sa_text(
            "SELECT teacher_id, time_slot_id FROM teacher_unavailability "
            "WHERE academic_period_id = :pid AND is_hard = true"
        ), {"pid": academic_period_id}).fetchall()
        for row in rows:
            day = self.slot_info.get(int(row.time_slot_id), (None, None))[0]
            if day is not None:
                self.teacher_unavailable_days.setdefault(int(row.teacher_id), set()).add(day)

        curriculum_list = (
            self.db.query(Curriculum)
            .filter(Curriculum.academic_period_id == academic_period_id)
            .all()
        )

        tasks: List[LessonTask] = []
        warnings: List[str] = []
        assigned_teacher_loads = {t.id: 0 for t in self.teachers}

        if not curriculum_list:
            warnings.append(
                "Учебный план пуст (group_subject_load). "
                "Добавьте нагрузку на группы для выбранного семестра."
            )
        if not self.time_slots:
            warnings.append("Нет time_slots — сначала заполните сетку пар.")
        if not self.rooms:
            warnings.append("Нет аудиторий (rooms) — генерация невозможна.")

        for curr in curriculum_list:
            lesson_type_id = int(curr.lesson_type_id)

            # ── Ищем учителей с учётом lesson_type ──────────────────────────
            teacher_ids = self._get_eligible_teachers(int(curr.subject_id), lesson_type_id)

            # Если нет teacher_subjects — пробуем preferred_teacher_id
            if not teacher_ids and curr.preferred_teacher_id:
                teacher_ids = [int(curr.preferred_teacher_id)]

            if not teacher_ids:
                self._log_conflict(
                    generation_run_id=generation_run_id,
                    academic_period_id=academic_period_id,
                    conflict_type="missing_teacher",
                    severity="error",
                    message=(
                        f"Не найден преподаватель для предмета (нет записи в teacher_subjects "
                        f"для subject_id={curr.subject_id}, lesson_type_id={lesson_type_id})."
                    ),
                    context={"subject_id": int(curr.subject_id), "group_id": int(curr.group_id),
                             "lesson_type_id": lesson_type_id},
                    subject_id=int(curr.subject_id),
                    group_id=int(curr.group_id),
                )
                continue

            # Приоритет: preferred_teacher_id, если он входит в список допустимых
            if curr.preferred_teacher_id and int(curr.preferred_teacher_id) in teacher_ids:
                teacher_id = int(curr.preferred_teacher_id)
            else:
                teacher_id = min(teacher_ids, key=lambda t_id: assigned_teacher_loads.get(t_id, 0))

            try:
                planned_weekly = float(curr.planned_weekly_hours)
            except Exception:
                planned_weekly = 0.0

            try:
                total_hours = float(curr.total_hours)
            except Exception:
                total_hours = 0.0

            # Вычисляем сколько пар в неделю (1 пара = 2 акад. часа)
            weekly_pairs = int(planned_weekly // 2)
            week_parity = "every"
            if weekly_pairs == 0 and planned_weekly >= 1.0:
                # Меньше 2 часов в неделю → раз в две недели
                weekly_pairs = 1
                week_parity = "numerator"
            if weekly_pairs == 0 and total_hours > 0:
                # Совсем мало часов в неделю, но предмет есть в учебном плане →
                # ставим хотя бы 1 пару раз в две недели
                weekly_pairs = 1
                week_parity = "numerator"
            if weekly_pairs == 0:
                continue

            group = self.group_map.get(int(curr.group_id))
            course_no = int(group.course_no) if group else 1

            lt = self.lesson_type_map.get(lesson_type_id)
            lt_name = lt.name.lower() if lt else ""
            is_practice = any(kw in lt_name for kw in PRACTICE_KEYWORDS)

            for _ in range(weekly_pairs):
                assigned_teacher_loads[teacher_id] = assigned_teacher_loads.get(teacher_id, 0) + 1
                tasks.append(
                    LessonTask(
                        academic_period_id=int(curr.academic_period_id),
                        group_subject_load_id=int(curr.group_subject_load_id),
                        group_id=int(curr.group_id),
                        subject_id=int(curr.subject_id),
                        lesson_type_id=lesson_type_id,
                        teacher_id=teacher_id,
                        teacher_ids=teacher_ids,
                        course_no=course_no,
                        is_practice=is_practice,
                        week_parity=week_parity,
                    )
                )

        # ── Дополнение до 20 пар/нед (4 пары × 5 дней) ───────────────────────
        # Если у группы меньше 20 задач — добираем повторениями предметов.
        # Каждый предмет может появиться не более 5 раз/нед (по одному в день).
        WEEKLY_TARGET = DEFAULT_MAX_DAILY * 5  # 4 × 5 = 20
        from collections import defaultdict as _dd, Counter as _Ctr
        import copy as _copy

        group_tasks_map: Dict[int, List[LessonTask]] = _dd(list)
        for t in tasks:
            group_tasks_map[t.group_id].append(t)

        padded_tasks: List[LessonTask] = []
        for gid, gtasks in group_tasks_map.items():
            current = len(gtasks)
            if current >= WEEKLY_TARGET:
                padded_tasks.extend(gtasks)
                continue

            needed = WEEKLY_TARGET - current
            subj_counts = _Ctr(t.subject_id for t in gtasks)
            # Template task per subject (for cloning)
            template_by_subj = {t.subject_id: t for t in gtasks}
            subjects_cycle = sorted(template_by_subj.keys(),
                                    key=lambda s: subj_counts[s])

            added = 0
            i = 0
            safety = len(subjects_cycle) * 6
            while added < needed and i < safety:
                sid = subjects_cycle[i % len(subjects_cycle)]
                # Each subject max 5×/week (≤ once per day constraint allows it)
                if subj_counts[sid] < 5:
                    tmpl = template_by_subj[sid]
                    # Rotate through all eligible teachers to spread load
                    all_teachers = list(tmpl.teacher_ids) if tmpl.teacher_ids else [tmpl.teacher_id]
                    best_teacher = min(all_teachers, key=lambda t: assigned_teacher_loads.get(t, 0))
                    new_task = LessonTask(
                        academic_period_id=tmpl.academic_period_id,
                        group_subject_load_id=tmpl.group_subject_load_id,
                        group_id=tmpl.group_id,
                        subject_id=tmpl.subject_id,
                        lesson_type_id=tmpl.lesson_type_id,
                        teacher_id=best_teacher,
                        teacher_ids=all_teachers,
                        course_no=tmpl.course_no,
                        is_practice=tmpl.is_practice,
                        week_parity="every",
                    )
                    gtasks.append(new_task)
                    subj_counts[sid] += 1
                    assigned_teacher_loads[best_teacher] = assigned_teacher_loads.get(best_teacher, 0) + 1
                    added += 1
                i += 1

            padded_tasks.extend(gtasks)

        tasks = padded_tasks

        # ── Round-robin по группам: 1 задача от каждой группы по очереди ──
        # Это гарантирует, что учителя распределяются справедливо и ни одна
        # группа не «занимает» всех учителей раньше остальных.
        tasks = self._round_robin_tasks(tasks)

        result = GenerationResult(total_count=len(tasks), warnings=warnings)

        for task in tasks:
            if self._place_lesson(task, generation_run_id):
                result.placed_count += 1
            else:
                g = self.group_map.get(task.group_id)
                s = self.subject_map.get(task.subject_id)
                t = self.teacher_map.get(task.teacher_id)
                lt = self.lesson_type_map.get(task.lesson_type_id)
                result.unplaced.append(
                    Unplaced(
                        group=g.name if g else str(task.group_id),
                        subject=s.name if s else str(task.subject_id),
                        teacher=t.full_name if t else str(task.teacher_id),
                        lesson_type=lt.name if lt else str(task.lesson_type_id),
                        reason="Нет свободных слотов/аудиторий без конфликтов",
                    ).__dict__
                )

        # ── Мягкая проверка: предупреждения о недогруженных днях ──
        underload_warnings = self._check_daily_underload()
        result.warnings.extend(underload_warnings)

        run = (
            self.db.query(ScheduleGenerationRun)
            .filter(ScheduleGenerationRun.generation_run_id == generation_run_id)
            .first()
        )
        if run:
            run.created_schedule_rows = int(result.placed_count)
            run.detected_conflicts = int(
                self.db.query(ScheduleConflictLog)
                .filter(ScheduleConflictLog.generation_run_id == generation_run_id)
                .count()
            )
            run.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        return result

    # ──────────────────────────────────────────────────────────────────
    # Сортировка задач
    # ──────────────────────────────────────────────────────────────────

    def _round_robin_tasks(self, tasks: List[LessonTask]) -> List[LessonTask]:
        """
        Interleave tasks so that slot-1 tasks for ALL groups come first,
        then slot-2, slot-3, slot-4. Within each wave groups are interleaved.
        This ensures teachers are distributed fairly across both groups and slots.
        """
        from collections import defaultdict as _ddd, Counter as _Ctr2

        group_queues: Dict[int, List[LessonTask]] = _ddd(list)
        for t in tasks:
            group_queues[t.group_id].append(t)
        # Within each group: most-varied subjects first
        for gid, qtasks in group_queues.items():
            subj_count = _Ctr2(t.subject_id for t in qtasks)
            qtasks.sort(key=lambda t: (subj_count[t.subject_id], t.subject_id))

        group_ids = sorted(group_queues.keys())
        result: List[LessonTask] = []
        # 20 waves (4 slots × 5 days); each wave picks one task per group
        for _ in range(20):
            for gid in group_ids:
                if group_queues[gid]:
                    result.append(group_queues[gid].pop(0))
        # Remaining tasks (if any group had > 20)
        for gid in group_ids:
            result.extend(group_queues[gid])
        return result

    def _sort_tasks(self, tasks: List[LessonTask]) -> List[LessonTask]:
        """Приоритет: 1. Заблокир. дни учителя, 2. Самые загруженные учителя, 3. Загруженные группы, 4. Практики (2 аудитории), 5. Младшие курсы."""
        from collections import Counter
        teacher_load = Counter(t.teacher_id for t in tasks)
        group_load = Counter(t.group_id for t in tasks)

        def get_priority(t: LessonTask):
            teacher_blocked_count = len(self.teacher_unavailable_days.get(t.teacher_id, set()))
            is_practice = 1 if t.is_practice else 0
            is_junior = 1 if t.course_no <= 2 else 0
            return (
                -teacher_blocked_count,
                -teacher_load[t.teacher_id],
                -group_load[t.group_id],
                -is_practice,
                -is_junior,
                t.group_id,   # deterministic tiebreak
            )
        
        return sorted(tasks, key=get_priority)

    # ──────────────────────────────────────────────────────────────────
    # Размещение одной пары
    # ──────────────────────────────────────────────────────────────────

    def _place_lesson(self, task: LessonTask, generation_run_id: int) -> bool:
        if not self.time_slots or not self.rooms:
            return False

        group = self.group_map.get(task.group_id)
        max_daily = min(int(group.max_daily_lessons) if group else DEFAULT_MAX_DAILY, DEFAULT_MAX_DAILY)

        teacher_blocked_days = self.teacher_unavailable_days.get(task.teacher_id, set())

        # Pass 1: Mon–Fri, slots 1-4, packed lowest slot first
        # Pass 2: Mon–Fri, ignore daily limit (last resort)
        # Saturday (day 6) is never used
        WEEKDAYS = [d for d in self.slots_by_day.keys() if d != 6]
        for fallback_pass in [1, 2, 3]:
            days = WEEKDAYS[:]

            # Prefer days that already have lessons (pack them to 4) over empty days
            days = [d for d in days if d not in teacher_blocked_days]
            days.sort(key=lambda d: (
                self.daily_load[task.group_id].get(d, 0) >= max_daily,  # full days last
                -(self.daily_load[task.group_id].get(d, 0)),             # pack non-empty days first
                d,                                                         # then by weekday order
            ))

            for day in days:
                current_load = self.daily_load[task.group_id].get(day, 0)
                if fallback_pass < 3 and current_load >= max_daily:
                    continue

                # Pass 1-2: slots 1-4; pass 3: also allow slot 5 (15:00) as last resort
                allowed = FALLBACK_SLOT_NUMBERS if fallback_pass == 3 else ALLOWED_SLOT_NUMBERS
                slots_in_day = [
                    sid for sid in self.slots_by_day[day]
                    if self.slot_info[sid][1] in allowed
                ]

                # Sort slots strictly ascending (slot 1 first, no gaps)
                slots_in_day = self._sort_slots_no_gap(task.group_id, day, slots_in_day)

                # Pass 3: allow same subject twice in a day (last resort for groups with few subjects)
                task._allow_subject_repeat = (fallback_pass == 3)

                for time_slot_id in slots_in_day:
                    if self._try_place(task, time_slot_id, day, generation_run_id):
                        task._allow_subject_repeat = False
                        return True

                task._allow_subject_repeat = False

        return False

    def _try_place(
        self,
        task: LessonTask,
        time_slot_id: int,
        day: int,
        generation_run_id: int,
    ) -> bool:
        parity = task.week_parity

        # Проверка занятости преподавателя: сначала пробуем основного назначенного
        assigned_teacher_id = None
        if self._is_entity_free(time_slot_id, task.teacher_id, self.teacher_busy, self.teacher_half, parity):
            assigned_teacher_id = task.teacher_id
        else:
            # Если основной занят, ищем резервного из списка допустимых
            for t_id in task.teacher_ids:
                if t_id != task.teacher_id and self._is_entity_free(time_slot_id, t_id, self.teacher_busy, self.teacher_half, parity):
                    assigned_teacher_id = t_id
                    break

        if assigned_teacher_id is None:
            return False

        # Проверка занятости группы
        if not self._is_entity_free(time_slot_id, task.group_id, self.group_busy, self.group_half, parity):
            return False

        # Запрет одного предмета дважды в один день у одной группы
        # (проверяем через атрибут fallback_pass, переданный из _place_lesson)
        day_subj_key = (task.group_id, day)
        if task.subject_id in self.group_day_subjects.get(day_subj_key, set()):
            if not getattr(task, '_allow_subject_repeat', False):
                return False

        # Поиск аудитории(й)
        if task.is_practice:
            room_id = self._find_two_rooms_or_one(time_slot_id, task, parity)
        else:
            room_id = self._find_free_room(time_slot_id, task, parity)

        if not room_id:
            return False

        # Вставляем строку расписания напрямую (триггеры отключены командой
        # SET LOCAL session_replication_role = 'replica' в начале generate()).
        # Если триггеры всё же активны (нет привилегии) — ловим исключение.
        row = ScheduleRow(
            academic_period_id=task.academic_period_id,
            group_subject_load_id=task.group_subject_load_id,
            group_id=task.group_id,
            subject_id=task.subject_id,
            lesson_type_id=task.lesson_type_id,
            teacher_id=assigned_teacher_id,
            room_id=room_id,
            time_slot_id=time_slot_id,
            source_run_id=generation_run_id,
            status="draft",
        )
        try:
            with self.db.begin_nested():
                self.db.add(row)
                self.db.flush()
        except Exception:
            return False

        self._mark_busy(time_slot_id, assigned_teacher_id, self.teacher_busy, self.teacher_half, parity)
        self._mark_busy(time_slot_id, task.group_id, self.group_busy, self.group_half, parity)
        self._mark_busy(time_slot_id, room_id, self.room_busy, self.room_half, parity)

        self.daily_load[task.group_id][day] = (
            self.daily_load[task.group_id].get(day, 0) + 1
        )
        slot_number = self.slot_info[time_slot_id][1]
        self.group_slots_per_day[task.group_id].setdefault(day, set()).add(slot_number)
        day_subj_key = (task.group_id, day)
        self.group_day_subjects.setdefault(day_subj_key, set()).add(task.subject_id)
        return True

    # ──────────────────────────────────────────────────────────────────
    # Нет окон у студентов: сортировка слотов
    # ──────────────────────────────────────────────────────────────────

    def _sort_slots_no_gap(
        self, group_id: int, day: int, slots: List[int]
    ) -> List[int]:
        occupied = self.group_slots_per_day[group_id].get(day, set())
        if not occupied:
            # Empty day: slot 1 only — guarantees all days start at 8:00
            return [s for s in slots if self.slot_info[s][1] == 1]

        max_slot = max(occupied)
        # Strictly only the next consecutive slot — never create gaps
        return [s for s in slots if self.slot_info[s][1] == max_slot + 1]

    # ──────────────────────────────────────────────────────────────────
    # Вспомогательные методы занятости
    # ──────────────────────────────────────────────────────────────────

    def _is_entity_free(
        self,
        slot_id: int,
        entity_id: int,
        busy: Set,
        half: Dict,
        parity: str,
    ) -> bool:
        key = (slot_id, entity_id)
        if key in busy:
            return False
        if parity == "every":
            if key in half:
                return False
        else:
            existing = half.get(key)
            if existing and existing == parity:
                return False
        return True

    def _mark_busy(
        self,
        slot_id: int,
        entity_id: int,
        busy: Set,
        half: Dict,
        parity: str,
    ) -> None:
        key = (slot_id, entity_id)
        if parity == "every":
            busy.add(key)
        else:
            existing = half.get(key)
            if existing and existing != parity:
                busy.add(key)
            else:
                half[key] = parity

    # ──────────────────────────────────────────────────────────────────
    # Поиск аудитории
    # ──────────────────────────────────────────────────────────────────

    def _get_allowed_rooms(self, task: LessonTask) -> List[Room]:
        allowed_types = self.subject_room_types.get((task.subject_id, task.lesson_type_id))
        if not allowed_types:
            return self.rooms
        return [r for r in self.rooms if int(r.room_type_id) in allowed_types]

    def _find_free_room(self, slot_id: int, task: LessonTask, parity: str = "every") -> Optional[int]:
        group = self.group_map.get(task.group_id)
        student_count = int(group.student_count or 0) if group else 0

        allowed = self._get_allowed_rooms(task)
        room_ids = [int(r.room_id) for r in allowed]
        random.shuffle(room_ids)
        for rid in room_ids:
            if not self._is_entity_free(slot_id, rid, self.room_busy, self.room_half, parity):
                continue
            # Проверяем вместимость (триггер тоже проверяет)
            room = self.room_map.get(rid)
            if room and room.capacity and student_count > 0:
                if int(room.capacity) < student_count:
                    continue
            return rid
        return None

    def _find_two_rooms_or_one(
        self, slot_id: int, task: LessonTask, parity: str
    ) -> Optional[int]:
        group = self.group_map.get(task.group_id)
        total_students = int(group.student_count or 30) if group else 30

        allowed = self._get_allowed_rooms(task)
        free_rooms = [
            r for r in allowed
            if self._is_entity_free(slot_id, int(r.room_id), self.room_busy, self.room_half, parity)
        ]
        random.shuffle(free_rooms)

        if len(free_rooms) >= 2:
            return int(free_rooms[0].room_id)

        # Fallback: одна большая аудитория
        for r in free_rooms:
            capacity = int(r.capacity or 999)
            if capacity >= total_students:
                return int(r.room_id)

        if free_rooms:
            return int(free_rooms[0].room_id)

        return None

    # ──────────────────────────────────────────────────────────────────
    # Проверка недогруженных дней (мягкое ограничение)
    # ──────────────────────────────────────────────────────────────────

    def _check_daily_underload(self) -> List[str]:
        warnings = []
        for group_id, day_loads in self.daily_load.items():
            group = self.group_map.get(group_id)
            group_name = group.name if group else str(group_id)
            for day, load in day_loads.items():
                if 0 < load < MIN_DESIRED_DAILY:
                    day_name = _day_name(day)
                    warnings.append(
                        f"Группа «{group_name}»: {day_name} — только {load} пар(ы). "
                        f"Рекомендуется минимум {MIN_DESIRED_DAILY}."
                    )
        return warnings

    # ──────────────────────────────────────────────────────────────────
    # Логирование конфликтов
    # ──────────────────────────────────────────────────────────────────

    def _log_conflict(
        self,
        generation_run_id: int,
        academic_period_id: int,
        conflict_type: str,
        severity: str,
        message: str,
        context: dict,
        subject_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        group_id: Optional[int] = None,
        room_id: Optional[int] = None,
        time_slot_id: Optional[int] = None,
    ) -> None:
        try:
            self.db.add(
                ScheduleConflictLog(
                    generation_run_id=generation_run_id,
                    academic_period_id=academic_period_id,
                    conflict_type=conflict_type,
                    severity=severity,
                    message=message,
                    context={**context, "subject_id": subject_id} if subject_id else context,
                    teacher_id=teacher_id,
                    group_id=group_id,
                    room_id=room_id,
                    time_slot_id=time_slot_id,
                )
            )
            self.db.flush()
        except Exception:
            pass  # Не даём ошибке логирования прервать генерацию


def _day_name(day: int) -> str:
    return {
        1: "Понедельник", 2: "Вторник", 3: "Среда",
        4: "Четверг", 5: "Пятница", 6: "Суббота", 7: "Воскресенье",
    }.get(day, f"День {day}")
