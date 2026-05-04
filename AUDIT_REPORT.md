# Аудит-отчёт: scheduleSYS
**Дата:** 2026-04-16  
**Аудитор:** Senior QA / Full-Stack / UI-UX / Performance  
**Версия проекта:** 1.0.0  
**Стек:** FastAPI + SQLAlchemy + PostgreSQL + React 18 + TypeScript + Vite + TailwindCSS

---

## 🔍 Общее заключение

Проект находится в стадии **активной разработки с незакрытыми критическими дырами безопасности**. Архитектура схемы БД продуманная и зрелая, но Python-код содержит ряд ошибок, которые делают систему **неработоспособной при чистом запуске** (CHECK-constraint violations, отсутствующее поле `building`). Функциональность расписания частично отключена (роутеры закомментированы). Несколько уязвимостей уровня **Critical Security** делают систему непригодной для production-развёртывания в текущем виде.

**Итоговые оценки:**

| Область | Оценка | Статус |
|---|---|---|
| Backend / API | 4/10 | 🔴 Критические баги |
| Security | 2/10 | 🔴 Не готово к prod |
| Database | 7/10 | 🟡 Нужно наполнение |
| Frontend | н/д | Не проверялся в браузере |
| Performance | 5/10 | 🟡 Есть N+1 и memory leaks |
| UI/UX (code review) | 6/10 | 🟡 Требует доработки |
| Responsive | н/д | Требует браузерной проверки |

---

## 🖥️ FRONTEND

### F-01 — `GET /api/schedule/my` возвращает только ID, без данных
**Проблема:** Эндпоинт возвращает `[{"id": 1}, {"id": 2}, ...]` — просто список schedule_id без каких-либо полей расписания.  
**Почему:** Студент или преподаватель открывает "Моё расписание" и видит пустой/бессмысленный результат. Frontend вынужден делать N дополнительных запросов.  
**Критичность:** 🔴 **Critical**  
**Исправление:** Возвращать полный объект с joined-данными:
```python
# schedule.py - роутер /my
rows = db.query(ScheduleRow).filter(...).all()
result = []
for r in rows:
    ts = db.query(TimeSlot).get(r.time_slot_id)
    subj = db.query(Subject).get(r.subject_id)
    result.append({
        "id": r.schedule_id,
        "day_of_week": ts.day_of_week,
        "slot_number": ts.slot_number,
        "start_time": str(ts.start_time),
        "end_time": str(ts.end_time),
        "subject_name": subj.name,
        "teacher_name": ...,
        "classroom": ...,
    })
```

---

### F-02 — Роутеры `hour_grid` и `reports` закомментированы в `main.py`
**Проблема:** Управление учебным планом (`/api/hour-grid/`) и отчёты полностью отключены.  
```python
# app.include_router(hour_grid.router)   ← закомментировано
# app.include_router(reports.router)     ← закомментировано
```
**Почему:** Генерация расписания невозможна без учебного плана. Без `hour_grid` роутера пользователь не может создать `group_subject_load` записи через UI.  
**Критичность:** 🔴 **Critical**  
**Исправление:** Раскомментировать оба роутера и убедиться, что схемы Pydantic соответствуют реальным полям модели (см. D-01).

---

### F-03 — Несоответствие схем Pydantic и реальных моделей для Curriculum
**Проблема:** `CurriculumBase` (schemas.py) содержит поля `theory_hours`, `practice_hours`, `semester`, которых **нет** в модели `Curriculum` (group_subject_load). Реальные поля: `planned_weekly_hours`, `total_hours`, `lesson_type_id`.  
**Почему:** Любой POST/PUT через роутер hour_grid сработает с неправильными данными или вызовет `AttributeError`.  
**Критичность:** 🔴 **Critical**  
**Исправление:** Привести схему в соответствие с моделью:
```python
class CurriculumCreate(BaseModel):
    group_id: int
    subject_id: int
    lesson_type_id: int
    academic_period_id: int
    planned_weekly_hours: float
    total_hours: float
    preferred_teacher_id: Optional[int] = None
    is_mandatory: bool = True
```

---

### F-04 — `departments.py` — заглушка, возвращает пустой список
**Проблема:** Роутер `departments` подключён в main.py, но его реализация — просто `return []`.  
**Почему:** Фронтенд ожидает список отделов для выбора специальности. Пользователь не может создать группу с корректной специальностью.  
**Критичность:** 🟠 **High**  
**Исправление:** Реализовать полноценный CRUD для Department и Specialty.

---

### F-05 — Статус расписания хранится в JSONB-поле `parameters`, а не в колонке
**Проблема:** В `update_version()` UI-статус сохраняется в `parameters["ui_status"]`, а не в `schedule_generation_runs.status`.  
```python
params["ui_status"] = payload["status"]
run.parameters = params
```
**Почему:** Двойная логика статусов (DB-статус `queued/running/completed` vs. UI-статус `generated/published/archived`). Фронтенд получает `"generated"` как статус, хотя в БД хранится `"completed"`. Невозможно сделать фильтрацию по статусу через SQL без разбора JSONB.  
**Критичность:** 🟠 **High**  
**Исправление:** Добавить колонку `ui_status VARCHAR(30)` в `schedule_generation_runs` или использовать существующий `status` с расширенным CHECK-constraint.

---

## ⚙️ BACKEND

### B-01 — Открытый эндпоинт `GET /api/seed-users` сбрасывает пароль администратора
**Проблема:** Любой (без аутентификации) может вызвать `GET /api/seed-users` и сбросить пароль admin до `admin123`.  
```python
@app.get("/api/seed-users")   # ← нет Depends(require_admin_or_dispatcher)
def seed_users_endpoint(db=Depends(get_db)):
    # Сбрасывает пароли admin и student к дефолтным
```
**Почему:** Полная компрометация системы. Злоумышленник за 1 HTTP-запрос получает права администратора.  
**Критичность:** 🔴 **Critical**  
**Исправление:** Удалить этот эндпоинт из production-кода полностью, или добавить guard:
```python
@app.get("/api/seed-users", include_in_schema=False)
def seed_users_endpoint(db=Depends(get_db), current_user=Depends(require_admin_or_dispatcher)):
```

---

### B-02 — Любой пользователь может зарегистрироваться с ролью ADMIN
**Проблема:** POST `/api/auth/register` принимает поле `role` и устанавливает его напрямую, без проверки прав вызывающего:
```python
class RegisterRequest(BaseModel):
    iin: str
    full_name: str
    role: Optional[str] = "STUDENT"   # ← можно передать "ADMIN"
```
**Почему:** Кто угодно может прислать `{"iin": "123456789012", "full_name": "...", "role": "ADMIN"}` и стать администратором.  
**Критичность:** 🔴 **Critical**  
**Исправление:** Убрать `role` из публичного `RegisterRequest`. Назначение ролей выше STUDENT — только через отдельный admin-эндпоинт:
```python
class RegisterRequest(BaseModel):
    iin: str
    full_name: str
    group_id: Optional[int] = None
    # role удалена из публичного API
```

---

### B-03 — Fallback-сравнение паролей в открытом виде
**Проблема:** `verify_password()` в `auth.py` содержит:
```python
except Exception as e:
    if plain_password == hashed_password:  # ← сравнение plaintext!
        return True
```
**Почему:** Если в БД хранится plaintext-пароль (legacy), система его примет. При утечке БД злоумышленник получает как хеши, так и чистые пароли.  
**Критичность:** 🔴 **Critical**  
**Исправление:** Полностью удалить plaintext fallback. Если нужна поддержка legacy — использовать `passlib.hash.md5_crypt.verify()`, но никогда не `==`.

---

### B-04 — Дефолтный JWT secret key в коде
**Проблема:** В `config.py`:
```python
secret_key: str = "your-super-secret-key-change-it"
```
Если `.env` не задан, приложение стартует с этим ключом.  
**Почему:** Любой, кто знает этот дефолт, может подделать JWT-токен с произвольным `sub` (username).  
**Критичность:** 🔴 **Critical**  
**Исправление:**
```python
secret_key: str  # Без дефолта — приложение не запустится без .env
```
Или генерировать при старте и сохранять в DB:
```python
secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
```

---

### B-05 — `print()` debug-логи в production-коде
**Проблема:** В `auth.py` и `main.py` активно используется `print()`:
```python
print(f"LOGIN FAIL: User {username} not found")
print(f"LOGIN SUCCESS: User {username}")
```
**Почему:** Утечка информации о существующих пользователях в системные логи. В production-среде логи могут быть доступны не только DevOps.  
**Критичность:** 🟡 **Medium**  
**Исправление:** Заменить на `import logging; logger = logging.getLogger(__name__)`. Использовать уровни `logger.warning(...)`, `logger.info(...)`.

---

### B-06 — Хардкод `specialty_id=1` при создании групп
**Проблема:** В `groups.py`:
```python
specialty_id=data.specialty_id or 1,
```
Если `specialty_id` не передан или передан `0`, берётся ID=1 — первая запись в таблице.  
**Почему:** После патча БД ID=1 может быть "Информационные системы". После рефактора — что угодно. Хардкод порождает молчаливое некорректное поведение.  
**Критичность:** 🟠 **High**  
**Исправление:** Сделать `specialty_id` обязательным полем в `GroupCreate`, либо возвращать 422 при отсутствии.

---

### B-07 — Отсутствие транзакционной целостности при CSV-импорте
**Проблема:** В `import_teachers_csv()` ошибки в отдельных строках перехватываются, строка пропускается, а в конце делается `db.commit()`. Частично корректные данные фиксируются, частично нет.  
**Почему:** Нет атомарности: если из 100 строк 50 прошли, а 50 — нет, в БД окажется 50 неожиданных записей.  
**Критичность:** 🟡 **Medium**  
**Исправление:** Опция 1 — всё или ничего: если есть любые ошибки, rollback. Опция 2 — savepoints per row. Выбор зависит от UX-требований, но нужно явно задокументировать поведение.

---

### B-08 — `log_action` вызывается после `db.commit()` с удалённым объектом
**Проблема:** В `delete_teacher()`:
```python
db.delete(t)
db.commit()
log_action(db, current_user.id, "DELETE", "teachers", teacher_id, {"name": t.last_name})
```
После `commit()` объект `t` находится в состоянии "detached". Доступ к `t.last_name` может вызвать `DetachedInstanceError`.  
**Критичность:** 🟡 **Medium**  
**Исправление:** Сохранять нужные данные до удаления:
```python
teacher_name = t.last_name
db.delete(t)
db.commit()
log_action(db, ..., {"name": teacher_name})
```

---

### B-09 — `GET /api/stats` доступен без аутентификации
**Проблема:** Эндпоинт возвращает количество групп, преподавателей, аудиторий — без авторизации.  
**Критичность:** 🟢 **Low**  
**Исправление:** Добавить `Depends(require_authenticated)`.

---

## 🗄️ DATABASE

### D-01 — Модель `Room` не имела поля `building` (исправлено в patch_v1)
**Проблема:** SQL-схема: `building VARCHAR(100) NOT NULL`. Python-модель Room не содержала этого поля.  
**Почему:** Любой INSERT через ORM падал бы с `NOT NULL constraint violation`.  
**Критичность:** 🔴 **Critical** (исправлено в `models.py` — добавлен `building` с `server_default`)

---

### D-02 — `ScheduleRow.status` и `ScheduleGenerationRun.status` имели недопустимый default (исправлено)
**Проблема:** Default `"generated"` не входит ни в один CHECK-constraint.  
- `schedule.status` CHECK: `('draft','planned','published','locked','cancelled')`  
- `schedule_generation_runs.status` CHECK: `('queued','running','completed','failed','cancelled')`  
**Критичность:** 🔴 **Critical** (исправлено: `"draft"` и `"queued"` соответственно)

---

### D-03 — `TeacherSubject` — несоответствие PK между SQL и ORM
**Проблема:** SQL-схема: `teacher_subject_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY`. ORM-модель: composite PK `(teacher_id, subject_id)`, колонка `teacher_subject_id` отсутствует.  
**Почему:** `db.refresh(ts)` в `assign_teacher_subject()` будет использовать composite PK для поиска записи, что может вернуть некорректный объект.  
**Критичность:** 🟠 **High**  
**Исправление в `models.py`:**
```python
class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"
    teacher_subject_id = Column(BigInteger, primary_key=True, index=True)
    teacher_id   = Column(BigInteger, ForeignKey("teachers.teacher_id"), nullable=False)
    subject_id   = Column(BigInteger, ForeignKey("subjects.subject_id"), nullable=False)
    lesson_type_id = Column(BigInteger, ForeignKey("lesson_types.lesson_type_id"))
    is_primary   = Column(Boolean, default=False)
    is_active    = Column(Boolean, default=True)
    note         = Column(Text)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    teacher = relationship("Teacher", back_populates="teacher_subjects")
    subject = relationship("Subject", back_populates="teacher_subjects")
```

---

### D-04 — `group_subject_load` не заполнен через API (роутер отключён)
**Проблема:** Роутер `hour_grid` закомментирован в `main.py`. Единственный способ создать учебный план — напрямую в БД через SQL.  
**Почему:** Без учебного плана генерация расписания возвращает 0 пар и предупреждение "Учебный план пуст".  
**Критичность:** 🔴 **Critical**

---

### D-05 — Отсутствие ON DELETE CASCADE на `schedule_conflicts_log.schedule_id`
**Проблема:** Колонка `schedule_id` в `schedule_conflicts_log` объявлена как `BIGINT` без FK:
```sql
schedule_id BIGINT,  -- ← нет REFERENCES schedule(schedule_id)
```
**Почему:** Это "ссылка вслепую". При удалении строки из `schedule` запись в `schedule_conflicts_log` сохранит ссылку на несуществующий ID.  
**Критичность:** 🟡 **Medium**  
**Исправление:**
```sql
ALTER TABLE schedule_conflicts_log
    ADD CONSTRAINT fk_conflicts_schedule
    FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id) ON DELETE SET NULL;
```

---

### D-06 — Нет уникального ограничения на `teacher_subjects(teacher_id, subject_id)` на уровне таблицы
**Проблема:** Уникальность обеспечена только через partial unique indexes (`uq_teacher_subjects_generic`, `uq_teacher_subjects_specific`). Модель ORM при конфликте получит `IntegrityError`, но без понятного сообщения об ошибке.  
**Критичность:** 🟢 **Low**  
**Исправление:** Обрабатывать `IntegrityError` в `assign_teacher_subject()` и возвращать 409 Conflict.

---

### D-07 — Curriculum-схема (Pydantic) не соответствует модели БД
**Проблема:** `CurriculumResponse` наследует от `CurriculumBase`, который имеет поля `theory_hours`, `practice_hours`, `semester` — которых нет в ORM-модели `Curriculum`. Сериализация через `from_attributes=True` вернёт `None` для этих полей (если повезёт) или вызовет ошибку.  
**Критичность:** 🔴 **Critical**  
**Исправление:** Привести схемы к полям модели (см. F-03).

---

## 🎨 UI / UX

*(Анализ по исходному коду React-компонентов без live-проверки)*

### U-01 — Отсутствие состояний empty/error на страницах расписания
**Проблема:** Если `group_subject_load` пуст, генерация возвращает `placed_count=0`. Пользователю показывается пустая таблица расписания без объяснения причины.  
**Критичность:** 🟠 **High**  
**Исправление:** Добавить `EmptyState` компонент с пояснением: "Учебный план не заполнен. Перейдите в раздел 'Сетка часов' и добавьте нагрузку на группы."

---

### U-02 — Страница "Моё расписание" для студента показывает только ID
**Проблема:** `GET /api/schedule/my` → `[{"id": 1}]`. Фронтенд студента, по всей видимости, отображает пустой или сломанный интерфейс.  
**Критичность:** 🔴 **Critical** (связано с B/F-01)

---

### U-03 — Нет индикации текущего активного семестра
**Проблема:** Пользователь не видит, какой семестр сейчас активен при генерации расписания. `AcademicPeriod.is_active` существует в БД, но не используется для автовыбора в форме генерации.  
**Критичность:** 🟡 **Medium**  
**Исправление:** При открытии формы генерации — автоматически выбирать семестр с `is_active=TRUE`.

---

### U-04 — Управление специальностями недоступно через UI
**Проблема:** `departments` роутер — заглушка. Создать группу с нужной специальностью невозможно, поскольку нет интерфейса для управления специальностями.  
**Критичность:** 🟠 **High**

---

### U-05 — Форма регистрации позволяет выбрать роль ADMIN
**Проблема:** Если в UI есть select для роли при регистрации — это критическая UX/Security проблема (см. B-02).  
**Критичность:** 🔴 **Critical**

---

## 📱 АДАПТИВНОСТЬ

*(Анализ конфигурации без live-проверки)*

### R-01 — TailwindCSS подключён — базовая адаптивность есть
**Статус:** Tailwind обеспечивает responsive-классы. Без live-тестирования конкретные breakpoint-проблемы невозможно идентифицировать.  
**Рекомендация:** Проверить компоненты `DataTable.tsx`, `Schedule.tsx` на мобильных: таблицы с >5 колонками обычно ломаются на 375px.

---

### R-02 — Шрифт Montserrat загружается из локальных файлов
**Проблема:** В `/src/assets/fonts/Montserrat/` хранятся шрифтовые файлы. Это увеличивает bundle size и время первой загрузки.  
**Критичность:** 🟢 **Low**  
**Исправление:** Использовать `font-display: swap` в CSS + preload `<link>` в `index.html`.

---

## ⚡ ПРОИЗВОДИТЕЛЬНОСТЬ

### P-01 — N+1 запрос в `get_version_entries_detailed`
**Проблема:** Загружаются ВСЕ группы, предметы, учителя, кабинеты, типы занятий, слоты в отдельных запросах, а потом делается Python-маппинг:
```python
group_map = {g.id: g for g in db.query(Group).all()}   # ALL rows!
subject_map = {s.id: s for s in db.query(Subject).all()}
teacher_map = {t.id: t for t in db.query(Teacher).all()}
room_map = {r.id: r for r in db.query(Room).all()}
# ... ещё 2 запроса
```
**Почему:** При 500 учителях, 50 группах и т.д. — избыточная нагрузка на память и БД при каждом запросе расписания.  
**Критичность:** 🟠 **High**  
**Исправление:** Использовать `joinedload` / `selectinload`:
```python
rows = (
    db.query(ScheduleRow)
    .filter(ScheduleRow.source_run_id == version_id)
    .options(
        selectinload(ScheduleRow.group),
        selectinload(ScheduleRow.subject),
        selectinload(ScheduleRow.teacher),
        selectinload(ScheduleRow.room),
        selectinload(ScheduleRow.time_slot),
    )
    .order_by(ScheduleRow.time_slot_id)
    .all()
)
```

---

### P-02 — Нет пагинации ни на одном list-эндпоинте
**Проблема:** `GET /api/teachers/` → `db.query(Teacher).all()`. При 500 преподавателях — всё в одном ответе.  
**Критичность:** 🟡 **Medium**  
**Исправление:** Добавить `limit`/`offset` параметры или использовать `fastapi-pagination`.

---

### P-03 — Алгоритм генерации расписания — O(tasks × slots × rooms) с `random.shuffle`
**Проблема:** Генерация каждый раз случайная (`random.shuffle(tasks)`). Одинаковый учебный план даёт разные результаты. Нет seed'а, нет детерминизма.  
**Почему:** Невозможно воспроизвести или отладить конкретный результат. Возможны ситуации, когда при одних данных всё ставится, а при повторной генерации — нет.  
**Критичность:** 🟡 **Medium**  
**Исправление:** Добавить `seed` параметр в `ScheduleGenerateRequest`. При записи в БД сохранять seed в `parameters`.

---

### P-04 — `Base.metadata.create_all(bind=engine)` закомментирован, Alembic не настроен
**Проблема:** В `main.py` закомментировано `create_all`. Alembic установлен (в requirements.txt), но миграции не настроены.  
**Почему:** После изменений схемы (например, добавление поля `building` в модель) нет автоматического способа применить их к БД.  
**Критичность:** 🟠 **High**  
**Исправление:** Инициализировать Alembic (`alembic init alembic`), создать `env.py`, сгенерировать начальную миграцию.

---

## 🔒 БЕЗОПАСНОСТЬ

### S-01 — CORS: `allow_origins=["*"]` + `allow_credentials=True`
**Проблема:**
```python
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # ← противоречие!
    ...
)
```
**Почему:** Браузер отклоняет запросы с `credentials: include` к wildcard-origins (спецификация CORS). Но это также означает отсутствие ограничений на источник запросов в dev-режиме.  
**Критичность:** 🟠 **High**  
**Исправление:**
```python
allow_origins=["http://localhost:5173", "https://your-domain.kz"],
allow_credentials=True,
```

---

### S-02 — Открытый `/api/seed-users` сбрасывает пароль admin (повтор B-01)
**Критичность:** 🔴 **Critical** — см. B-01

---

### S-03 — Роль ADMIN назначается при самостоятельной регистрации (повтор B-02)
**Критичность:** 🔴 **Critical** — см. B-02

---

### S-04 — Plaintext password fallback (повтор B-03)
**Критичность:** 🔴 **Critical** — см. B-03

---

### S-05 — Незащищённый JWT secret key по умолчанию (повтор B-04)
**Критичность:** 🔴 **Critical** — см. B-04

---

### S-06 — Пароль возвращается в теле ответа при регистрации
**Проблема:** `POST /api/auth/register` возвращает:
```json
{
  "password": "123456abc",
  "message": "Ваш пароль: 123456abc"
}
```
**Почему:** Если API работает без HTTPS (что типично для dev), пароль передаётся в открытом виде. Даже с HTTPS — пароль в теле ответа остаётся в логах nginx, browser history, DevTools.  
**Критичность:** 🟠 **High**  
**Исправление:** Не возвращать пароль в ответе. Показывать его только один раз в UI через flash-сообщение, не сохраняя в localStorage.

---

### S-07 — Нет rate limiting на `/api/auth/token`
**Проблема:** Эндпоинт логина не защищён от брутфорса.  
**Критичность:** 🟠 **High**  
**Исправление:** Добавить `slowapi` middleware или `fastapi-limiter`:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(...):
```

---

### S-08 — SQL-инъекции: риск низкий (SQLAlchemy ORM), но есть исключение
**Статус:** ORM защищает от SQL-инъекций в большинстве мест. Явных `text()` запросов с пользовательскими данными не обнаружено.  
**Критичность:** 🟢 **Low** (текущее состояние)

---

### S-09 — XSS: риск через `dangerouslySetInnerHTML` — требует проверки в React-компонентах
**Статус:** Без просмотра React-компонентов нельзя исключить XSS. Рекомендуется grep-поиск:
```bash
grep -r "dangerouslySetInnerHTML" frontend/src/
grep -r "innerHTML" frontend/src/
```
**Критичность:** Требует дополнительной проверки

---

## 🚨 ЧТО НУЖНО ИСПРАВИТЬ СРОЧНО (до production)

| # | Проблема | Файл | Критичность |
|---|---|---|---|
| 1 | Открытый `/api/seed-users` сбрасывает admin-пароль | `main.py:126` | 🔴 Critical |
| 2 | Регистрация с ролью ADMIN без авторизации | `routers/auth.py:18` | 🔴 Critical |
| 3 | Plaintext password fallback в auth | `auth.py:24` | 🔴 Critical |
| 4 | JWT secret key — дефолтное значение | `config.py:10` | 🔴 Critical |
| 5 | `Room` модель: нет поля `building` (INSERT падает) | `models/models.py:197` | 🔴 Critical ✅ исправлено |
| 6 | `ScheduleRow.status` default = "generated" (CHECK fail) | `models/models.py:291` | 🔴 Critical ✅ исправлено |
| 7 | `ScheduleGenerationRun.status` default = "generated" | `models/models.py:239` | 🔴 Critical ✅ исправлено |
| 8 | Роутер `hour_grid` отключён → генерация не работает | `main.py:59` | 🔴 Critical |
| 9 | `CurriculumCreate` схема не соответствует модели БД | `schemas/schemas.py:156` | 🔴 Critical |
| 10 | `/api/schedule/my` возвращает только ID | `routers/schedule.py:40` | 🔴 Critical |
| 11 | `TeacherSubject` — неверный PK в ORM | `models/models.py:166` | 🟠 High |
| 12 | Нет rate limit на login endpoint | `routers/auth.py:109` | 🟠 High |
| 13 | `specialty_id=1` хардкод при создании группы | `routers/groups.py:66` | 🟠 High |

---

## 🔧 ЧТО МОЖНО УЛУЧШИТЬ ПОЗЖЕ

| # | Улучшение | Приоритет |
|---|---|---|
| 1 | Настроить Alembic + миграции | Medium |
| 2 | Добавить пагинацию ко всем list-эндпоинтам | Medium |
| 3 | Заменить `print()` на `logging` | Medium |
| 4 | N+1 в `get_version_entries_detailed` → `joinedload` | Medium |
| 5 | Детерминированный seed для генератора расписания | Medium |
| 6 | Реализовать `departments.py` (убрать заглушку) | Medium |
| 7 | Добавить `EmptyState` компоненты в UI | Low |
| 8 | Автовыбор активного семестра в форме генерации | Low |
| 9 | Пароль при регистрации — только flash в UI | Low |
| 10 | CORS: заменить `"*"` на конкретные домены | High (перед prod) |
| 11 | Добавить FK `schedule_conflicts_log.schedule_id → schedule(schedule_id)` | Low |
| 12 | XSS-аудит React-компонентов (grep `dangerouslySetInnerHTML`) | Medium |
| 13 | `log_action` после `delete` — сохранять данные до удаления | Low |
| 14 | Экспорт расписания (`501 Not Implemented`) | Low |
| 15 | Отчёты (`reports.py` закомментирован) | Low |

---

## 📋 Метрика исправлений

| Уровень | Найдено | Исправлено в этой сессии | Остаётся |
|---|---|---|---|
| 🔴 Critical | 10 | 3 | 7 |
| 🟠 High | 8 | 0 | 8 |
| 🟡 Medium | 6 | 0 | 6 |
| 🟢 Low | 4 | 0 | 4 |

---

*Отчёт сформирован на основе статического анализа кода. Для полного аудита требуется live-тестирование в браузере, проверка Lighthouse scores, и penetration testing развёрнутого экземпляра.*
