# -*- coding: utf-8 -*-
import json, re, sys, io

with open('C:/Users/user/Desktop/scheduleSYS/schedule_data.json', encoding='utf-8') as f:
    data = json.load(f)

DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
TIMES = ['08.00-09.30', '09.35- 11.05', '11.20-12.50', '13.10-14.40']
TIME_LABELS = ['08:00–09:30', '09:35–11:05', '11:20–12:50', '13:10–14:40']
PERIOD_NUMS = ['1', '2', '3', '4']

def normalize_time(t):
    if not t:
        return None
    t = str(t).strip()
    for ref in TIMES:
        if t[:5] == ref[:5]:
            return ref
    return None

def parse_sheet(sheet_rows):
    all_pairs = []
    g1 = g2 = None
    current_day = current_time = None

    for row in sheet_rows:
        def c(i):
            try:
                v = row[i]
                return str(v).strip() if v is not None else None
            except:
                return None

        col1, col2, col5, col6, col7, col8 = c(0), c(1), c(4), c(5), c(6), c(7)

        # New group pair header
        if col1 in DAYS and col2 == 'Расписание звонков':
            if g1 is not None:
                all_pairs.append((g1, g2))
            g1 = {'name': col5 or '—', 'days': {d: {t: [] for t in TIMES} for d in DAYS}}
            g2 = {'name': col7 or '—', 'days': {d: {t: [] for t in TIMES} for d in DAYS}}
            current_day = 'Понедельник'
            current_time = None
            continue

        if g1 is None:
            continue

        # Day + time on same row
        if col1 in DAYS:
            current_day = col1
            t = normalize_time(col2)
            if t:
                current_time = t
                g1['days'][current_day][current_time].append({'subj': col5, 'room': col6, 'teacher': None})
                g2['days'][current_day][current_time].append({'subj': col7, 'room': col8, 'teacher': None})
            else:
                current_time = None
            continue

        # Time slot only
        t = normalize_time(col2)
        if t and col1 is None:
            current_time = t
            if (col5 or col7) and current_day:
                g1['days'][current_day][current_time].append({'subj': col5, 'room': col6, 'teacher': None})
                g2['days'][current_day][current_time].append({'subj': col7, 'room': col8, 'teacher': None})
            continue

        # Continuation row
        if col1 is None and col2 is None and current_day and current_time:
            slot1 = g1['days'][current_day][current_time]
            slot2 = g2['days'][current_day][current_time]
            if col5:
                if slot1 and slot1[-1]['teacher'] is None:
                    slot1[-1]['teacher'] = col5
                else:
                    slot1.append({'subj': col5, 'room': col6, 'teacher': None})
            if col7:
                if slot2 and slot2[-1]['teacher'] is None:
                    slot2[-1]['teacher'] = col7
                else:
                    slot2.append({'subj': col7, 'room': col8, 'teacher': None})

    if g1 is not None:
        all_pairs.append((g1, g2))
    return all_pairs

# Parse all sheets, keep pairs together
all_pairs = []
for sheet_name in ['Лист1 (3)', 'Лист1 (2)', 'Лист1']:
    if sheet_name in data:
        pairs = parse_sheet(data[sheet_name])
        for p in pairs:
            if p[0]['name'] and p[0]['name'] != 'None':
                all_pairs.append(p)

print(f"Total pairs: {len(all_pairs)}")
for g1, g2 in all_pairs:
    print(f"  {g1['name']} | {g2['name']}")

# ─── HTML GENERATION ─────────────────────────────────────────────────────────
def esc(s):
    if not s:
        return ''
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def make_lesson_block(lessons):
    if not lessons:
        return '<div class="empty-slot">—</div>'
    parts = []
    for ln in lessons:
        subj = esc(ln.get('subj') or '')
        room = esc(ln.get('room') or '')
        teacher = esc(ln.get('teacher') or '')
        if not subj:
            continue
        block = f'<div class="lesson">'
        block += f'<div class="lesson-subj">{subj}</div>'
        if room:
            block += f'<span class="lesson-room">🚪 {room}</span>'
        if teacher:
            block += f'<div class="lesson-teacher">👤 {teacher}</div>'
        block += '</div>'
        parts.append(block)
    return ''.join(parts) if parts else '<div class="empty-slot">—</div>'

def make_pair_table(g1, g2, idx):
    name1 = esc(g1['name'])
    name2 = esc(g2['name'])
    sid1 = re.sub(r'[^\w]', '_', g1['name'])
    html = f'<section class="pair-section" id="pair-{idx}">'
    html += f'''
    <div class="pair-header">
      <div class="pair-badge">Группы</div>
      <h2 class="pair-title">
        <span class="grp-name" id="grp-{sid1}">{name1}</span>
        <span class="pair-divider">⟷</span>
        <span class="grp-name">{name2}</span>
      </h2>
    </div>
    '''
    html += '<div class="table-wrap"><table class="sched-table">'
    # Header
    html += f'''<thead>
      <tr>
        <th class="col-day">День</th>
        <th class="col-num">№</th>
        <th class="col-time">Время</th>
        <th class="col-group">{name1}</th>
        <th class="col-group">{name2}</th>
      </tr>
    </thead><tbody>'''

    for di, day in enumerate(DAYS):
        is_sat = day == 'Суббота'
        row_class = ' class="day-sat"' if is_sat else ''
        for ti, time in enumerate(TIMES):
            lessons1 = g1['days'][day][time]
            lessons2 = g2['days'][day][time]
            tr_classes = ['tr-row']
            if is_sat:
                tr_classes.append('sat-row')
            if ti == 0:
                tr_classes.append('day-first')
            html += f'<tr class="{" ".join(tr_classes)}">'
            if ti == 0:
                day_cls = 'day-cell sat-day' if is_sat else 'day-cell'
                html += f'<td class="{day_cls}" rowspan="{len(TIMES)}">{esc(day)}</td>'
            html += f'<td class="num-cell">{PERIOD_NUMS[ti]}</td>'
            html += f'<td class="time-cell">{TIME_LABELS[ti]}</td>'
            html += f'<td class="lesson-cell">{make_lesson_block(lessons1)}</td>'
            html += f'<td class="lesson-cell">{make_lesson_block(lessons2)}</td>'
            html += '</tr>'
    html += '</tbody></table></div></section>'
    return html

# Build sidebar
sidebar_html = ''
for idx, (g1, g2) in enumerate(all_pairs):
    n1 = esc(g1['name'])
    n2 = esc(g2['name'])
    sid1 = re.sub(r'[^\w]', '_', g1['name'])
    sidebar_html += f'''
    <div class="nav-pair">
      <a href="#pair-{idx}" class="nav-link">{n1}</a>
      <a href="#pair-{idx}" class="nav-link dim">{n2}</a>
    </div>'''

# Build all tables
tables_html = '\n'.join(make_pair_table(g1, g2, idx) for idx, (g1, g2) in enumerate(all_pairs))

HTML = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Расписание 1–2 курс · 2 семестр 2025–2026</title>
<meta name="description" content="Расписание занятий 1–2 курс, 2 семестр 2025–2026 учебного года"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#080b12;
  --bg2:#0d1120;
  --card:#111827;
  --card2:#161d2e;
  --border:#1e2740;
  --border2:#2a3550;
  --accent:#5b82f7;
  --accent2:#8b5cf6;
  --accent-glow:rgba(91,130,247,.18);
  --text:#dce5ff;
  --text2:#8a97bb;
  --text3:#55637f;
  --subj:#b8d0ff;
  --room:#fbbf24;
  --room-bg:rgba(251,191,36,.1);
  --teacher:#6ee7b7;
  --teacher-bg:rgba(110,231,183,.07);
  --sat:#ef4444;
  --sat-bg:rgba(239,68,68,.06);
  --radius-lg:14px;
  --radius:8px;
  --shadow:0 8px 40px rgba(0,0,0,.5);
  --shadow-sm:0 2px 12px rgba(0,0,0,.3);
}}
html{{scroll-behavior:smooth;}}
body{{
  font-family:'Inter',sans-serif;
  background:var(--bg);
  color:var(--text);
  display:flex;
  min-height:100vh;
  overflow-x:hidden;
}}

/* ─── SIDEBAR ──────────────────────────────────── */
.sidebar{{
  width:240px;
  min-width:240px;
  background:var(--bg2);
  border-right:1px solid var(--border);
  display:flex;
  flex-direction:column;
  position:fixed;
  inset:0 auto 0 0;
  overflow-y:auto;
  z-index:200;
}}
.sidebar-top{{
  padding:24px 20px 16px;
  border-bottom:1px solid var(--border);
  flex-shrink:0;
}}
.brand{{
  font-size:13px;
  font-weight:800;
  letter-spacing:.08em;
  text-transform:uppercase;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
  margin-bottom:4px;
}}
.semester-info{{
  font-size:11.5px;
  color:var(--text3);
  line-height:1.5;
}}
.search-wrap{{
  padding:12px 12px 0;
}}
.search-input{{
  width:100%;
  background:var(--card);
  border:1px solid var(--border2);
  border-radius:var(--radius);
  padding:8px 12px;
  font-size:12px;
  color:var(--text);
  font-family:inherit;
  outline:none;
  transition:border-color .2s;
}}
.search-input::placeholder{{color:var(--text3)}}
.search-input:focus{{border-color:var(--accent)}}
.nav-body{{
  flex:1;
  overflow-y:auto;
  padding:8px 8px 24px;
}}
.nav-pair{{
  margin-bottom:2px;
  border-radius:var(--radius);
  overflow:hidden;
}}
.nav-link{{
  display:block;
  padding:6px 12px;
  font-size:12.5px;
  font-weight:500;
  color:var(--text2);
  text-decoration:none;
  transition:all .15s ease;
  border-radius:var(--radius);
}}
.nav-link:hover,.nav-link.active{{
  background:var(--accent-glow);
  color:var(--accent);
}}
.nav-link.dim{{
  color:var(--text3);
  font-size:11.5px;
  padding-top:2px;
  padding-bottom:4px;
}}
.nav-link.dim:hover{{color:var(--text2)}}

/* ─── MAIN ─────────────────────────────────────── */
.main{{
  margin-left:240px;
  flex:1;
  padding:36px 40px 80px;
  min-width:0;
}}

/* ─── PAGE HEADER ──────────────────────────────── */
.page-hdr{{
  margin-bottom:40px;
}}
.page-hdr h1{{
  font-size:28px;
  font-weight:800;
  letter-spacing:-.02em;
  background:linear-gradient(135deg,#7ea8ff 0%,#a78bfa 100%);
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
}}
.page-hdr p{{
  font-size:13.5px;
  color:var(--text2);
  margin-top:6px;
}}
.stats-row{{
  display:flex;
  gap:16px;
  margin-top:20px;
  flex-wrap:wrap;
}}
.stat-chip{{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:8px 16px;
  font-size:12px;
  color:var(--text2);
}}
.stat-chip strong{{color:var(--text);font-weight:700}}

/* ─── PAIR SECTION ─────────────────────────────── */
.pair-section{{
  margin-bottom:56px;
  animation:fadeup .3s ease both;
}}
@keyframes fadeup{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}

.pair-header{{
  display:flex;
  align-items:center;
  gap:12px;
  margin-bottom:14px;
}}
.pair-badge{{
  font-size:10px;
  font-weight:700;
  letter-spacing:.1em;
  text-transform:uppercase;
  color:var(--accent);
  background:var(--accent-glow);
  border:1px solid rgba(91,130,247,.3);
  padding:3px 10px;
  border-radius:20px;
  flex-shrink:0;
}}
.pair-title{{
  font-size:17px;
  font-weight:700;
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap:wrap;
}}
.grp-name{{
  color:var(--text);
}}
.pair-divider{{
  color:var(--text3);
  font-size:13px;
}}

/* ─── SCHEDULE TABLE ───────────────────────────── */
.table-wrap{{
  overflow-x:auto;
  border-radius:var(--radius-lg);
  box-shadow:var(--shadow);
  border:1px solid var(--border);
}}
.sched-table{{
  width:100%;
  border-collapse:collapse;
  background:var(--card);
  font-size:13px;
  min-width:700px;
}}

/* Head */
.sched-table thead tr{{
  background:var(--card2);
  border-bottom:2px solid var(--border2);
}}
.sched-table thead th{{
  padding:11px 14px;
  font-size:11px;
  font-weight:700;
  text-transform:uppercase;
  letter-spacing:.07em;
  color:var(--text3);
  text-align:left;
  white-space:nowrap;
}}
.col-day{{width:80px;text-align:center!important}}
.col-num{{width:36px;text-align:center!important}}
.col-time{{width:130px}}
.col-group{{min-width:240px}}

/* Body rows */
.sched-table tbody .tr-row{{
  border-bottom:1px solid var(--border);
  transition:background .1s;
}}
.sched-table tbody .tr-row:hover{{background:var(--card2)}}
.sched-table tbody .tr-row:last-child{{border-bottom:none}}
.sched-table tbody .day-first{{border-top:2px solid var(--border2)}}

/* Day cell */
.day-cell{{
  text-align:center;
  vertical-align:middle;
  font-size:11px;
  font-weight:700;
  letter-spacing:.06em;
  text-transform:uppercase;
  color:var(--text2);
  background:var(--card2);
  border-right:2px solid var(--border2);
  padding:6px 4px;
  writing-mode:vertical-rl;
  text-orientation:mixed;
  transform:rotate(180deg);
  width:30px;
}}
.day-cell.sat-day{{color:var(--sat)}}
.sat-row .lesson-cell{{background:var(--sat-bg)}}
.sat-row .time-cell{{background:rgba(239,68,68,.03)}}

/* Num cell */
.num-cell{{
  text-align:center;
  font-size:11px;
  font-weight:700;
  color:var(--text3);
  width:36px;
  padding:8px 4px;
  border-right:1px solid var(--border);
  vertical-align:top;
}}

/* Time cell */
.time-cell{{
  padding:10px 14px;
  font-size:11.5px;
  font-weight:600;
  color:var(--text2);
  white-space:nowrap;
  border-right:1px solid var(--border);
  vertical-align:top;
  font-variant-numeric:tabular-nums;
}}

/* Lesson cell */
.lesson-cell{{
  padding:8px 14px;
  vertical-align:top;
  border-right:1px solid var(--border);
  min-width:220px;
}}
.lesson-cell:last-child{{border-right:none}}

/* Lesson block */
.lesson{{
  padding:4px 0;
}}
.lesson + .lesson{{
  border-top:1px dashed var(--border2);
  margin-top:6px;
  padding-top:8px;
}}
.lesson-subj{{
  font-weight:600;
  color:var(--subj);
  font-size:13px;
  line-height:1.4;
}}
.lesson-room{{
  display:inline-flex;
  align-items:center;
  gap:3px;
  margin-top:4px;
  background:var(--room-bg);
  color:var(--room);
  font-size:11px;
  font-weight:700;
  padding:2px 8px;
  border-radius:4px;
  letter-spacing:.02em;
}}
.lesson-teacher{{
  display:flex;
  align-items:center;
  gap:3px;
  margin-top:4px;
  color:var(--teacher);
  font-size:11.5px;
  background:var(--teacher-bg);
  padding:2px 8px;
  border-radius:4px;
  width:fit-content;
}}
.empty-slot{{
  color:var(--text3);
  font-size:12px;
  padding:2px 0;
}}

/* ─── SCROLLBAR ─────────────────────────────────── */
::-webkit-scrollbar{{width:5px;height:5px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:3px}}
::-webkit-scrollbar-thumb:hover{{background:var(--accent)}}

/* ─── RESPONSIVE ────────────────────────────────── */
@media(max-width:768px){{
  .sidebar{{transform:translateX(-100%);transition:.3s ease}}
  .main{{margin-left:0;padding:16px 12px 60px}}
  .page-hdr h1{{font-size:22px}}
}}
</style>
</head>
<body>

<nav class="sidebar" id="sidebar">
  <div class="sidebar-top">
    <div class="brand">📅 Расписание</div>
    <p class="semester-info">1–2 курс &nbsp;·&nbsp; 2 семестр<br/>2025–2026 учебный год</p>
    <div class="search-wrap">
      <input class="search-input" id="searchInput" type="text" placeholder="🔍 Поиск группы…"/>
    </div>
  </div>
  <div class="nav-body" id="navBody">
    {sidebar_html}
  </div>
</nav>

<main class="main">
  <div class="page-hdr">
    <h1>Расписание занятий</h1>
    <p>1–2 курс &nbsp;·&nbsp; 2 семестр &nbsp;·&nbsp; 2025–2026 учебный год &nbsp;·&nbsp; Начало с 26.01.2026</p>
    <div class="stats-row">
      <div class="stat-chip"><strong>{len(all_pairs) * 2}</strong> групп</div>
      <div class="stat-chip"><strong>4</strong> пары в день</div>
      <div class="stat-chip"><strong>Пн – Сб</strong> рабочие дни</div>
    </div>
  </div>

  <div id="scheduleContainer">
    {tables_html}
  </div>
</main>

<script>
// Search / filter
const searchInput = document.getElementById('searchInput');
const navLinks = document.querySelectorAll('.nav-link');
const pairs = document.querySelectorAll('.pair-section');

searchInput.addEventListener('input', function() {{
  const q = this.value.trim().toLowerCase();
  navLinks.forEach(a => {{
    const txt = a.textContent.toLowerCase();
    a.style.display = (!q || txt.includes(q)) ? '' : 'none';
  }});
  pairs.forEach(sec => {{
    const title = sec.querySelector('.pair-title')?.textContent.toLowerCase() || '';
    sec.style.display = (!q || title.includes(q)) ? '' : 'none';
  }});
}});

// Highlight active nav link on scroll
const observer = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      const id = e.target.id;
      navLinks.forEach(a => {{
        a.classList.toggle('active', a.getAttribute('href') === '#' + id);
      }});
    }}
  }});
}}, {{ threshold: 0.2 }});

pairs.forEach(sec => observer.observe(sec));
</script>
</body>
</html>'''

with open('C:/Users/user/Desktop/scheduleSYS/schedule_view.html', 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"Done! {len(all_pairs)} pairs, {len(all_pairs)*2} groups => schedule_view.html")
