/**
 * Schedule Controller
 */
const Schedule = {
  versions: [],
  groups: [],
  currentData: [],

  async init() {
    this.setupListeners();
    await this.loadFilters();
  },

  setupListeners() {
    document.getElementById('btn-load-schedule')?.addEventListener('click', () => this.loadSchedule());
  },

  async loadFilters() {
    try {
      // Parallel fetch
      const [versions, groups] = await Promise.all([
        window.api.getPublicVersions(),
        window.api.getGroups()
      ]);
      
      this.versions = versions;
      this.groups = [...groups].sort((a,b) => a.name.localeCompare(b.name));

      // Populate versions dropdown
      const versionSelect = document.getElementById('filter-version');
      if (versionSelect) {
        versionSelect.innerHTML = versions.length 
          ? versions.map(v => `<option value="${v.id}">${v.name} (${new Date(v.created_at).toLocaleDateString()})</option>`).join('')
          : '<option value="">Нет активных расписаний</option>';
      }

      // Populate groups dropdown
      const groupSelect = document.getElementById('filter-group');
      if (groupSelect) {
        groupSelect.innerHTML = '<option value="">Все группы</option>' + 
          this.groups.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
      }

    } catch (error) {
      console.error('Failed to load filters', error);
      ui.showToast('Ошибка загрузки данных', 'error');
    }
  },

  async loadSchedule() {
    const versionId = document.getElementById('filter-version')?.value;
    const groupId = document.getElementById('filter-group')?.value;
    const weekType = document.getElementById('filter-week')?.value;
    
    if (!versionId) {
      ui.showToast('Выберите версию расписания', 'error');
      return;
    }
    
    if (!groupId) {
      ui.showToast('Выберите группу для просмотра', 'info');
      // Could show all, but usually too much data. Enforce group selection for now.
      return;
    }

    const container = document.getElementById('schedule-container');
    const btn = document.getElementById('btn-load-schedule');
    
    ui.setLoading(btn, true);
    
    try {
      // 1. Fetch entries
      const allEntries = await window.api.getScheduleEntries(Number(versionId), Number(groupId));
      
      // 2. Filter by week if selected
      const filteredEntries = weekType 
        ? allEntries.filter(e => e.week_type === 'любая' || e.week_type === weekType)
        : allEntries;
      
      this.currentData = filteredEntries;
      this.renderSchedule(filteredEntries, container);
      
    } catch (error) {
      ui.showToast(error.message || 'Ошибка загрузки расписания', 'error');
    } finally {
      ui.setLoading(btn, false);
    }
  },

  renderSchedule(entries, container) {
    if (!entries || entries.length === 0) {
      container.innerHTML = `
        <div class="schedule-empty animate-entrance">
          <div class="empty-icon" aria-hidden="true">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </div>
          <p class="empty-title">Нет занятий</p>
          <p class="empty-desc">Для выбранной группы нет расписания в этой версии.</p>
        </div>
      `;
      return;
    }

    // Days mapping
    const daysMap = {
      1: 'Понедельник',
      2: 'Вторник',
      3: 'Среда',
      4: 'Четверг',
      5: 'Пятница',
      6: 'Суббота'
    };

    // Group by day -> sort by time_slot
    const byDay = {};
    entries.forEach(e => {
      if (!byDay[e.day_of_week]) byDay[e.day_of_week] = [];
      byDay[e.day_of_week].push(e);
    });

    let html = '<div class="days-container" style="display: flex; flex-direction: column; gap: var(--space-6);">';
    
    // Render loop
    let animDelay = 0;
    
    for (let i = 1; i <= 6; i++) {
        if (!byDay[i]) continue;
        
        const dayEntries = byDay[i].sort((a,b) => a.time_slot_number - b.time_slot_number);
        
        html += `
        <div class="day-section animate-entrance" style="animation-delay: ${animDelay}ms">
            <h3 style="display:flex; align-items:center; gap:8px; border-bottom: 1px solid var(--color-border-glass-strong); padding-bottom:var(--space-2)">
              <span style="background:var(--grad-primary); border-radius: var(--radius-sm); width:24px; height:24px; display:inline-flex; align-items:center; justify-content:center; color:white; font-size:12px">${i}</span>
              ${daysMap[i]}
            </h3>
            <div class="day-cards" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-4); margin-top: var(--space-4);">
        `;
        
        dayEntries.forEach(entry => {
            const badgeClass = entry.lesson_type === 'лекция' ? 'badge-blue' : 
                               entry.lesson_type === 'практика' ? 'badge-green' : 'badge-purple';
                               
            html += `
              <div class="glass-card-xs" style="padding: var(--space-4); position: relative; overflow: hidden; transition: transform 0.2s">
                <div style="position:absolute; top:0; left:0; width:4px; height:100%; background:var(--color-primary)"></div>
                
                <div style="display:flex; justify-content:space-between; margin-bottom:var(--space-2)">
                  <span style="font-weight:600; color:var(--color-text-inverse)">${entry.start_time} - ${entry.end_time}</span>
                  <span class="badge ${badgeClass}">${entry.lesson_type}</span>
                </div>
                
                <h4 style="margin:0; margin-bottom:var(--space-2); font-size:var(--text-base); line-height:var(--leading-snug)">${entry.subject_name}</h4>
                
                <div style="display:flex; flex-direction:column; gap:4px; font-size:var(--text-sm); color:var(--color-text-muted)">
                   <div style="display:flex; align-items:center; gap:6px">
                     <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>
                     ${entry.teacher_name}
                   </div>
                   <div style="display:flex; align-items:center; gap:6px">
                     <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5z" clip-rule="evenodd"/></svg>
                     Каб: <strong style="color:var(--color-text-main)">${entry.classroom_name}</strong>
                   </div>
                </div>
                
                ${entry.subgroup_name ? `<div style="margin-top:var(--space-2); font-size:11px; padding:2px 6px; background:rgba(255,255,255,0.05); border-radius:4px; display:inline-block">Подгруппа: ${entry.subgroup_name}</div>` : ''}
                ${entry.week_type !== 'любая' ? `<div style="position:absolute; bottom:var(--space-2); right:var(--space-2); font-size:10px; opacity:0.5">${entry.week_type}</div>` : ''}
              </div>
            `;
        });
        
        html += `</div></div>`;
        animDelay += 100;
    }
    
    html += '</div>';
    container.innerHTML = html;
  }
};
