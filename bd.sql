-- ==============================================================================
-- 1. СОЗДАНИЕ СТРУКТУРЫ БАЗЫ ДАННЫХ (ТАБЛИЦЫ И СВЯЗИ)
-- ==============================================================================

-- Таблица сотрудников (преподавателей)
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50)
);

-- Таблица аудиторного фонда (кабинеты и лаборатории)
CREATE TABLE classrooms (
    classroom_id SERIAL PRIMARY KEY,
    room_number VARCHAR(50),
    floor VARCHAR(50),
    capacity INT,
    room_type VARCHAR(100),
    subject_name VARCHAR(255),
    head_employee_id INT REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- Таблица учебных групп и контингента студентов
CREATE TABLE student_groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(50) NOT NULL UNIQUE,
    course_number INT,
    total_students INT,
    budget_students INT,
    paid_9_students INT,
    paid_11_students INT,
    male_students INT,
    female_students INT
);

-- Сводная таблица (Many-to-Many) для связи Групп и Кураторов
CREATE TABLE group_curators (
    group_id INT REFERENCES student_groups(group_id) ON DELETE CASCADE,
    employee_id INT REFERENCES employees(employee_id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, employee_id)
);


-- ==============================================================================
-- 2. ЗАПОЛНЕНИЕ ТАБЛИЦЫ СОТРУДНИКОВ
-- ==============================================================================
-- 
INSERT INTO employees (employee_id, full_name, phone_number) VALUES
(1, 'Абдуллина Нурия Фаиковна', NULL),
(2, 'Абишев Нурдаулет Ерасылович', '+7 7081780078'),
(3, 'Авакри Адылжан Имиржанұлы', NULL),
(4, 'Адамбаева Жанна Сериковна', NULL),
(5, 'Акынова Айзада Айдаркызы', NULL),
(6, 'Аликберова Надежда Александровна', NULL),
(7, 'Алимкулова Азиза Юнусқызы', NULL),
(8, 'Алгуватова Асия Тимуркызы', NULL),
(9, 'Аяпбергенова Айгуль Хаирберлыевна', NULL),
(10, 'Аманкулова Гулфия Ахметовна', NULL),
(11, 'Атыханов Талгат Атыханович', NULL),
(12, 'Ахметжанова Жайляугайша Кабировна', NULL),
(13, 'Бегалиев Нуракын Жамишович', NULL),
(14, 'Бекен Алуа Думанкызы', NULL),
(15, 'Белгожаева Турсунхан Шареновна', NULL),
(16, 'Бидахметов Агзам Канатович', NULL),
(17, 'Галпай Ұлжан Әсенқызы', '87472726604'),
(18, 'Даукенов Максат Ерболұлы', '87475894123'),
(19, 'Даулетқызы Ақнұр', NULL),
(21, 'Джакуржеков Бахыт Сарсебекович', NULL),
(22, 'Диханбаева Динара Жекебатыровна', NULL),
(23, 'Ерназар Перизат Галымбеккызы', NULL),
(24, 'Есеналиева Меруерт Бакытжанкызы', NULL),
(25, 'Есимхан Аянай Даулеткызы', '87083213814'),
(26, 'Естаев Данат Болатович', NULL),
(27, 'Жакупова Айгуль Спатаевна', NULL),
(28, 'Жанабил Жулдыз Жумабайкызы', '87075497975'),
(29, 'Жеткiзгенкызы Гулсая', NULL),
(30, 'Жолымбекова Айдана Сайлаубеккызы', NULL),
(31, 'Жузбаева Бахытгуль Алимхановна', NULL),
(32, 'Жулкашева Индира Абайкызы', '87785704859'),
(33, 'Зинуллина Ару Елеусиновна', NULL),
(34, 'Ибрагимов Ринат Ришатович', NULL),
(35, 'Искакова Аружан Дидаровна', NULL),
(36, 'Кабдулова Айзат Кабдулкызы', NULL),
(37, 'Кабымбаева Жансулу Мураткалиевна', NULL),
(38, 'Кадиров Максат Даржибаевич', NULL),
(39, 'Кайырбаева Раушан Елтаевна', NULL),
(40, 'Каким Айдина Дидаркызы', NULL),
(41, 'Калабаева Гульжамал Калдыбековна', NULL),
(42, 'Кален Жаксылык Манатулы', NULL),
(43, 'Камабекова Динара Оразхановна', NULL),
(44, 'Камалбеков Мади Куттыбекович', NULL),
(45, 'Конысбаева Райхан Махмутовна', NULL),
(46, 'Куангалиева Улпан Сериккаликызы', NULL),
(47, 'Кузенбай Толганай Мураткызы', '87479979491'),
(48, 'Курмангалиева Алма Болатбековна', NULL),
(49, 'Мамытаев Осет Дюсекулы', NULL),
(50, 'Мантай Әсемгул Шаймерденкызы', NULL),
(51, 'Маратов Диас Ермекович', '87078372070'),
(52, 'Масягина Наталия Геннадиевна', NULL),
(53, 'Муканбеков Кайрат Избасарович', NULL),
(54, 'Муратова Мединә Мергенбайкызы', NULL),
(55, 'Муталиева Адеми Алдабергеновна', '87773968998'),
(56, 'Мышан Әділет Берікұлы', NULL),
(57, 'Мырзакан Гулнауат Бериккызы', '87471068381'),
(58, 'Нариманова Актоты Жардемгалиева', '87474020447'),
(59, 'Ниталиева Айнур Анатольевна', NULL),
(60, 'Нургалиева Назгул Советовна', '87770205744'),
(61, 'Онгарова Акмарал', NULL),
(62, 'Распутько Кирилл Денисович', NULL),
(63, 'Рахан Шынгысхан Кайратулы', '87051331319'),
(64, 'Рахимов Артур Джумагалиевич', '87077449678'),
(65, 'Саметова Кульпан Толыбаевна', NULL),
(66, 'Сардарова Зарина Исмаиловна', NULL),
(67, 'Сарина Самал Галымовна', '87078891585'),
(68, 'Сатан Бекзат Серикулы', NULL),
(69, 'Сейтбекова Асем Кайратовна', NULL),
(70, 'Сәкен Әсем Мураткызы', NULL),
(71, 'Сетербаева Гульназ Мухамедханова', NULL),
(72, 'Серикбаева Аружан Жанаткызы', NULL),
(73, 'Тайкпанова Данара Абдибаевна', NULL),
(74, 'Тен Ирина Анатольевна', NULL),
(75, 'Тулеубаева Динара Тургалиқызы', NULL),
(76, 'Усенгаликызы Алия', NULL),
(77, 'Халилов Канат Турсунбаевич', NULL),
(78, 'Шоманова Ботагоз Курбановна', NULL),
(79, 'Ынтымак Рыскелді Серікбайуһұлы', NULL),
(80, 'Юнусова Кулзира Аштаевна', NULL),
(81, 'Деева Юлия Васильевна', NULL),
(82, 'Азизов З.Т.', NULL),
(83, 'Уалиев Н.А.', NULL);

-- Фиксируем sequence, чтобы избежать конфликтов при ручном вводе ID
SELECT setval('employees_employee_id_seq', (SELECT MAX(employee_id) FROM employees));


-- ==============================================================================
-- 3. ЗАПОЛНЕНИЕ КАБИНЕТОВ (с привязкой к заведующим)
-- ==============================================================================
-- 
INSERT INTO classrooms (room_number, floor, capacity, room_type, subject_name, head_employee_id) VALUES
('101', '1-й этаж', 30, 'Простой', 'Нан, макарон және кондитер өндірісінің технологиясы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сейтбекова%')),
('104', '1-й этаж', 30, 'Простой', 'Химия', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Нариманова Актоты%')),
('113', '1-й этаж', 30, 'Простой', 'Интернет технологиясы және WEB-бағдарламалау', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Муталиева%')),
('114', '1-й этаж', 32, 'Простой', 'Алғашқы әскери дайындық', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Кален%')),
('115', '1-й этаж', 30, 'Компьютерный', 'Тағам дайындау технологиясы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Саметова%')),
('116', '1-й этаж', 32, 'Простой', 'География', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жулкашева%')),
('117', '1-й этаж', 26, 'Простой', 'Қазақ тілі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Куангалиева%')),
('118', '1-й этаж', 30, 'Простой', 'Банк операциялары', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Серикбаева%')),
('120', '1-й этаж', 30, 'Компьютерный', '1 С:Бухгалтерия', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Онгарова%')),
('200', '2-й этаж', 30, 'Простой', 'Физика', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Кузенбай%')),
('201', '2-й этаж', 30, 'Простой', 'Химия', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Шоманова%')),
('203', '2-й этаж', 30, 'Простой', 'Математика', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Атыханов%')),
('208', '2-й этаж', 30, 'Простой', 'Математика', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Калабаева%')),
('209', '2-й этаж', 30, 'Простой', 'Қазақстан тарихы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Нургалиева%')),
('210', '2-й этаж', 28, 'Простой', 'Ағылшын тілі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Масягина%')),
('211', '2-й этаж', 30, 'Простой', 'Орыс тілі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сардарова%')),
('212', '2-й этаж', 30, 'Простой', 'Әлеуметтік-гуманитарлық пәндер', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Халилов%')),
('213', '2-й этаж', 30, 'Простой', 'Қазақ тілі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жузбаева%')),
('218', '2-й этаж', 30, 'Компьютерный', 'Компьютерлік графика', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жанабил%')),
('220', '2-й этаж', 30, 'Компьютерный', 'Операциялық жүйелер және қолданбалы бағдарламалық қамтамасыздандыру', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Курмангалиева%')),
('222', '2-й этаж', 30, 'Компьютерный', 'Информатика', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Юнусова%')),
('224', '2-й этаж', 30, 'Компьютерный', 'Ақпараттық-коммуникациялық және цифрлық технологияларды қолдану', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Мамытаев%')),
('300', '3-й этаж', 30, 'Простой', 'Әлеуметтік-гуманитарлық пәндер', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Белгожаева%')),
('301', '3-й этаж', 30, 'Простой', 'Менеджмент және маркетинг негіздері', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Ниталиева%')),
('302', '3-й этаж', 30, 'Простой', 'Ақша,қаржы және несие', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Адамбаева%')),
('303', '3-й этаж', 30, 'Простой', 'Банк ісі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Кайырбаева%')),
('304', '3-й этаж', 30, 'Простой', 'Сауда есептеулері', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сәкен%')),
('306', '3-й этаж', 30, 'Простой', 'Экономикалық теория негіздері', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сарина%')),
('308', '3-й этаж', 30, 'Простой', 'Кәсіпорын экономикасы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Аяпбергенова%')),
('309', '3-й этаж', 30, 'Простой', 'Қазақ тілі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Галпай%')),
('310', '3-й этаж', 30, 'Простой', 'Статистика', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Усенгаликызы%')),
('311', '3-й этаж', 16, 'Компьютерный', 'Компьютерлік желілер және телекоммуникация (зертхана)', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Рахан%')),
('312', '3-й этаж', 30, 'Простой', 'Қаржылық сауаттылық', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Абдуллина%')),
('316', '3-й этаж', 28, 'Простой', 'Ағылшын тілі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Аликберова%')),
('318', NULL, NULL, 'Компьютерный', 'Компьютерлік графика', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Абишев%')),
('320', '3-й этаж', 30, 'Компьютерный', 'Автоматтандырылған ақпараттық жүйелер', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Мырзакан%')),
('322', '3-й этаж', 30, 'Компьютерный', 'Бағдарламалау және объектіге бағытталған бағдарламалау негіздері', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Есимхан%')),
('324', '3-й этаж', 30, 'Компьютерный', 'Cisco Академиясы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Бекен%')),
('Лаб. 1', NULL, NULL, 'Зертхана', 'Кондитер өндірісі', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Муратова%')),
('Лаб. 2', NULL, NULL, 'Зертхана', 'Нан, макарон және кондитер өндірісінің технологиясы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Алгуватова%')),
('Лаб. 3', NULL, NULL, 'Зертхана', 'Өнімдерді бастапқы өңдеу цехы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Уалиев%')),
('Лаб. 4', NULL, NULL, 'Зертхана', 'Тамақ дайындау технологиясы', (SELECT employee_id FROM employees WHERE full_name ILIKE '%Акынова%'));


-- ==============================================================================
-- 4. ЗАПОЛНЕНИЕ УЧЕБНЫХ ГРУПП И КОНТИНГЕНТА
-- ==============================================================================
-- (Где данные по студентам отсутствуют в источнике, проставляется NULL)
-- [cite: 11, 26, 31]
INSERT INTO student_groups (group_name, course_number, total_students, budget_students, paid_9_students, paid_11_students, male_students, female_students) VALUES
('ОП 1-1', 1, 25, 25, 0, 0, 18, 7),
('ОП 1-2', 1, 26, 25, 1, 0, 14, 12),
('ТК 1-1', 1, 26, 25, 1, 0, 3, 23),
('ТП 1-1', 1, 25, 25, 0, 0, 16, 9),
('БД 1-1', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('БД 1-2', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('БД 1-3', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('БУХ 1-1', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('БУХ 1-2', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('БУХ 1-3', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 1-1', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 1-2', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 1-3', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('РПО 1-1', 1, NULL, NULL, NULL, NULL, NULL, NULL),
('ОП 2-1', 2, 23, 23, 0, 0, 15, 8),
('ОП 2-2', 2, 20, 20, 0, 0, 12, 8),
('ОП 2-3', 2, 26, 25, 0, 1, 19, 7),
('ТП 2-1', 2, 29, 25, 2, 2, 18, 11),
('ТК 2-1', 2, 31, 25, 0, 6, 5, 26),
('ТХ 2-1', 2, 23, 23, 0, 0, 8, 15),
('БД 2-1', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('БД 2-2', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('БУХ 2-1', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('БУХ 2-2', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('БУХ 2-3', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 2-1', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 2-2', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 2-3', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('РПО 2-1', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('ИС 2-1', 2, NULL, NULL, NULL, NULL, NULL, NULL),
('ОП 3-1', 3, 23, 21, 1, 1, 16, 7),
('ОП 3-2', 3, 25, 25, 0, 0, 16, 9),
('ОП 3-3', 3, 23, 23, 0, 0, 19, 4),
('ТК 3-1', 3, 25, 25, 0, 0, 3, 22),
('ТХ 3-1', 3, 22, 22, 0, 0, 6, 16),
('ТП 3-1', 3, 27, 25, 0, 2, 20, 7),
('БУХ 3-1', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('БУХ 3-2', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('БД 3-1', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('БД 3-2', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 3-1', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 3-2', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 3-3', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 3-4', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('WEB 3-5', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('РПО 3-1', 3, NULL, NULL, NULL, NULL, NULL, NULL),
('ТХ 4-1', 4, 23, 23, 0, 0, 5, 18),
('ТП 4-1', 4, 14, NULL, NULL, 14, 10, 4),
('ОП 4-1', 4, 25, NULL, NULL, 25, 10, 15),
('РПО 4-1', 4, NULL, NULL, NULL, NULL, NULL, NULL),
('РПО 4-2', 4, NULL, NULL, NULL, NULL, NULL, NULL);


-- ==============================================================================
-- 5. СВЯЗЫВАНИЕ КУРАТОРОВ И ГРУПП (Таблица group_curators)
-- ==============================================================================
-- [cite: 11, 14, 30]
INSERT INTO group_curators (group_id, employee_id) VALUES
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 1-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сәкен%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 1-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Кабдулова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТК 1-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жолымбекова%')),
((SELECT group_id FROM student_groups WHERE full_name ILIKE '%Зинуллина%'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Зинуллина%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БД 1-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сарина%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БД 1-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Серикбаева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БД 1-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жулкашева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 1-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сатан%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 1-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Шоманова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 1-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Аликберова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 1-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Юнусова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 1-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Маратов%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 1-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Есимхан%')),
((SELECT group_id FROM student_groups WHERE group_name = 'РПО 1-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Деева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Аманкулова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 2-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сейтбекова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 2-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Саметова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТП 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Авакри%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТК 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Есеналиева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТХ 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Муратова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БД 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жузбаева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БД 2-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Сардарова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Онгарова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 2-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Адамбаева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 2-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Абдуллина%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Кузенбай%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 2-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жанабил%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 2-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Рахимов%')),
((SELECT group_id FROM student_groups WHERE group_name = 'РПО 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Мырзакан%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ИС 2-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Галпай%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Кален%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 3-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Акынова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 3-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Конысбаева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТК 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Алгуватова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТХ 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Даулетқызы%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТП 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Бидахметов%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Ниталиева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БУХ 3-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Камабекова%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БД 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Кайырбаева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'БД 3-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Халилов%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Нургалиева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 3-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Муталиева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 3-3'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Рахан%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 3-4'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Даукенов%')),
((SELECT group_id FROM student_groups WHERE group_name = 'WEB 3-5'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Деева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'РПО 3-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Нариманова Актоты%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТХ 4-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жеткiзгенкызы%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ТП 4-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Бидахметов%')),
((SELECT group_id FROM student_groups WHERE group_name = 'ОП 4-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Жанабил%')),
((SELECT group_id FROM student_groups WHERE group_name = 'РПО 4-1'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Белгожаева%')),
((SELECT group_id FROM student_groups WHERE group_name = 'РПО 4-2'), (SELECT employee_id FROM employees WHERE full_name ILIKE '%Абишев%'));

-- ==============================================================================
-- ТАБЛИЦА ВРЕМЕННЫХ СЛОТОВ (РАСПИСАНИЕ ЗВОНКОВ)
-- ==============================================================================

CREATE TABLE time_slots (
    slot_id SERIAL PRIMARY KEY,
    slot_number INT NOT NULL UNIQUE, -- Номер пары по порядку
    start_time TIME NOT NULL,        -- Время начала
    end_time TIME NOT NULL           -- Время окончания
);

-- Заполнение таблицы расписанием звонков
INSERT INTO time_slots (slot_number, start_time, end_time) VALUES
(1, '08:00', '09:30'),
(2, '09:35', '11:05'),
(3, '11:20', '12:50'),
(4, '13:10', '14:40'),
(5, '14:50', '16:20'),
(6, '16:25', '17:55'),
(7, '18:00', '19:30');