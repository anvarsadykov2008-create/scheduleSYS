import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Modal from '../components/ui/Modal';
import {
  Play, Download, Trash2, CheckCircle, Globe, Archive,
  Info, MapPin, Users, Clock, AlertTriangle, ExternalLink,
  LayoutGrid, TableProperties, MoveRight, Ban, Pencil
} from 'lucide-react';

interface Semester { id: number; number: number; academic_year?: { name: string } }
interface Version { id: number; status: string; created_at: string; description: string | null }
interface Group { id: number; name: string }
interface Subject { id: number; name: string }
interface ScheduleEntry {
  id: number;
  day_of_week: number;
  time_slot_number: number;
  start_time: string;
  end_time: string;
  subject_name: string;
  teacher_name: string;
  teacher_id?: number | null;
  classroom_name: string;
  classroom_id?: number | null;
  week_type: string;
  lesson_type: string;
  is_locked: boolean;
  group_name?: string;
  group_id?: number;
}
interface Teacher { id: number; full_name: string }
interface Classroom { id: number; name: string }
interface GenResult {
  version_id: number;
  placed_count: number;
  total_count: number;
  unplaced: { group: string; subject: string; teacher: string; lesson_type: string; reason: string }[];
  warnings: string[];
}

const DAY_NAMES_RU = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
const TIME_SLOTS = [
  { num: 1, label: '08:00 – 09:30' },
  { num: 2, label: '09:35 – 11:05' },
  { num: 3, label: '11:20 – 12:50' },
  { num: 4, label: '13:10 – 14:40' },
];

export default function Schedule() {
  const { t, lang } = useLang();
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [selectedSem, setSelectedSem] = useState<number | ''>('');
  const [selectedGroup, setSelectedGroup] = useState<number | ''>('');
  const [selectedSubject, setSelectedSubject] = useState<number | ''>('');
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [entries, setEntries] = useState<ScheduleEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [showGenModal, setShowGenModal] = useState(false);
  const [genResult, setGenResult] = useState<GenResult | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  
  // Edit State
  const [editingEntry, setEditingEntry] = useState<ScheduleEntry | null>(null);
  const [editFormData, setEditFormData] = useState<{ teacher_id?: number; room_id?: number; day_of_week?: number; slot_number?: number }>({});
  const [editSaving, setEditSaving] = useState(false);

  // Context menu state
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; entry: ScheduleEntry } | null>(null);
  const ctxMenuRef = useRef<HTMLDivElement>(null);

  // Move modal state
  const [moveEntry, setMoveEntry] = useState<ScheduleEntry | null>(null);
  const [moveFormData, setMoveFormData] = useState<{ day_of_week: number; slot_number: number }>({ day_of_week: 1, slot_number: 1 });
  const [moveSaving, setMoveSaving] = useState(false);
  const [moveError, setMoveError] = useState<string | null>(null);

  // Edit modal error
  const [editError, setEditError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient.get<Semester[]>('/semesters'),
      apiClient.get<Group[]>('/groups'),
      apiClient.get<Subject[]>('/subjects'),
      apiClient.get<Teacher[]>('/teachers'),
      apiClient.get<Classroom[]>('/classrooms'),
    ]).then(([sems, grps, subs, tchs, cls]) => {
      setSemesters(sems);
      setGroups(grps);
      setSubjects(subs);
      setTeachers(tchs);
      setClassrooms(cls);
      if (sems.length > 0) setSelectedSem(sems[0].id);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedSem) { setVersions([]); setSelectedVersionId(null); return; }
    apiClient.get<Version[]>(`/schedule/versions?semester_id=${selectedSem}`).then(vList => {
      setVersions(vList);
      if (vList.length > 0 && !selectedVersionId) setSelectedVersionId(vList[0].id);
    }).catch(() => {});
  }, [selectedSem]);

  // Close context menu on outside click
  useEffect(() => {
    if (!ctxMenu) return;
    const handler = (e: MouseEvent) => {
      if (ctxMenuRef.current && !ctxMenuRef.current.contains(e.target as Node)) {
        setCtxMenu(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [ctxMenu]);

  useEffect(() => {
    if (!selectedVersionId) { setEntries([]); return; }
    // Fetch ALL entries for the version (for table view) — group/subject filtering done client-side
    apiClient.get<ScheduleEntry[]>(`/schedule/versions/${selectedVersionId}/entries/detailed`)
      .then(setEntries)
      .catch(() => setEntries([]));
  }, [selectedVersionId]);

  // ── Derived data ────────────────────────────────────────────────────────────

  // Filter entries for card/single-group view
  const filteredEntries = useMemo(() => {
    let e = entries;
    if (selectedGroup) e = e.filter(x => x.group_id === selectedGroup || x.group_name === groups.find(g => g.id === selectedGroup)?.name);
    if (selectedSubject) e = e.filter(x => x.subject_name === subjects.find(s => s.id === selectedSubject)?.name);
    return e;
  }, [entries, selectedGroup, selectedSubject, groups, subjects]);

  // Group names that appear in the entries (for table columns)
  const activeGroupNames = useMemo(() => {
    const names = new Set(entries.map(e => e.group_name || '').filter(Boolean));
    // Sort by groups list order
    return groups.filter(g => names.has(g.name)).map(g => g.name);
  }, [entries, groups]);

  // Build lookup: (day, slot, groupName) -> entry
  const entryMap = useMemo(() => {
    const map = new Map<string, ScheduleEntry>();
    entries.forEach(e => {
      const key = `${e.day_of_week}-${e.time_slot_number}-${e.group_name}`;
      map.set(key, e);
    });
    return map;
  }, [entries]);

  // Groups to show in table (filtered if selectedGroup)
  const tableGroups = useMemo(() => {
    if (selectedGroup) {
      const g = groups.find(x => x.id === selectedGroup);
      return g ? [g.name] : activeGroupNames;
    }
    return activeGroupNames;
  }, [selectedGroup, groups, activeGroupNames]);

  // ── Actions ──────────────────────────────────────────────────────────────────

  const handleGenerate = async () => {
    if (!selectedSem) return;
    setGenerating(true);
    try {
      const result = await apiClient.post<GenResult>(`/schedule/generate`, {
        semester_id: selectedSem,
        description: `Generated on ${new Date().toLocaleString()}`
      });
      setGenResult(result);
      setShowGenModal(true);
      const up = await apiClient.get<Version[]>(`/schedule/versions?semester_id=${selectedSem}`);
      setVersions(up);
      setSelectedVersionId(result.version_id);
    } catch { alert(t.errorGenerate); }
    finally { setGenerating(false); }
  };

  const updateStatus = async (id: number, status: string) => {
    try {
      await apiClient.put(`/schedule/versions/${id}`, { status });
      const up = await apiClient.get<Version[]>(`/schedule/versions?semester_id=${selectedSem}`);
      setVersions(up);
    } catch { alert(t.errorChangeStatus); }
  };

  const handleExport = async (id: number) => {
    setExporting(true);
    try {
      const blob = await apiClient.fetchBlob(`/schedule/versions/${id}/export`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `schedule_v${id}.xlsx`;
      document.body.appendChild(a); a.click(); a.remove();
    } catch { alert(t.errorExport); }
    finally { setExporting(false); }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm(t.confirmDeleteVersion)) {
      try {
        await apiClient.delete(`/schedule/versions/${id}`);
        setVersions(versions.filter(v => v.id !== id));
      } catch { alert(t.error); }
    }
  };

  const handleCellClick = (dayNum: number, slotNum: number, groupName: string, entry?: ScheduleEntry) => {
    if (!entry) return; // Currently only editing existing entries is supported
    setEditingEntry(entry);
    setEditFormData({
      teacher_id: entry.teacher_id || undefined,
      room_id: entry.classroom_id || undefined,
      day_of_week: entry.day_of_week,
      slot_number: entry.time_slot_number,
    });
  };

  const handleSaveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEntry) return;
    setEditSaving(true);
    setEditError(null);
    try {
      await apiClient.put(`/schedule/entries/${editingEntry.id}`, editFormData);
      const newEntries = await apiClient.get<ScheduleEntry[]>(`/schedule/versions/${selectedVersionId}/entries/detailed`);
      setEntries(newEntries);
      setEditingEntry(null);
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : 'Ошибка сохранения');
    } finally {
      setEditSaving(false);
    }
  };

  const handleEntryDrop = async (entryId: number, targetDay: number, targetSlot: number, _targetGroupName: string) => {
    try {
      await apiClient.put(`/schedule/entries/${entryId}`, {
        day_of_week: targetDay,
        slot_number: targetSlot,
      });
      const newEntries = await apiClient.get<ScheduleEntry[]>(`/schedule/versions/${selectedVersionId}/entries/detailed`);
      setEntries(newEntries);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Ошибка при перемещении занятия';
      alert(msg);
    }
  };

  const handleDeleteEntry = async () => {
    if (!editingEntry || !window.confirm('Точно удалить запись?')) return;
    setEditSaving(true);
    try {
      await apiClient.delete(`/schedule/entries/${editingEntry.id}`);
      setEntries(entries.filter(e => e.id !== editingEntry.id));
      setEditingEntry(null);
    } catch {
      alert(t.error);
    } finally {
      setEditSaving(false);
    }
  };

  const handleContextMenu = useCallback((e: React.MouseEvent, entry: ScheduleEntry) => {
    e.preventDefault();
    e.stopPropagation();
    setCtxMenu({ x: e.clientX, y: e.clientY, entry });
  }, []);

  const openMoveModal = (entry: ScheduleEntry) => {
    setCtxMenu(null);
    setMoveEntry(entry);
    setMoveFormData({ day_of_week: entry.day_of_week, slot_number: entry.time_slot_number });
  };

  const handleMoveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!moveEntry) return;
    setMoveSaving(true);
    setMoveError(null);
    try {
      await apiClient.put(`/schedule/entries/${moveEntry.id}`, moveFormData);
      const newEntries = await apiClient.get<ScheduleEntry[]>(`/schedule/versions/${selectedVersionId}/entries/detailed`);
      setEntries(newEntries);
      setMoveEntry(null);
    } catch (err: unknown) {
      setMoveError(err instanceof Error ? err.message : 'Ошибка при перемещении');
    } finally {
      setMoveSaving(false);
    }
  };

  const handleCancelEntry = async (entry: ScheduleEntry) => {
    setCtxMenu(null);
    if (!window.confirm(`Отменить занятие "${entry.subject_name}" для ${entry.group_name}?`)) return;
    try {
      await apiClient.delete(`/schedule/entries/${entry.id}`);
      setEntries(prev => prev.filter(e => e.id !== entry.id));
    } catch {
      alert('Ошибка при отмене занятия');
    }
  };

  const currentVersion = versions.find(v => v.id === selectedVersionId);

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-museum-text">{t.scheduleTitle}</h1>
          <p className="text-sm text-museum-text-muted">{t.scheduleSubtitle}</p>
        </div>
        <Button onClick={handleGenerate} loading={generating} disabled={!selectedSem}>
          <Play className="h-4 w-4 mr-2" />{t.generateSchedule}
        </Button>
      </div>

      {loading && (
        <div className="flex justify-center p-12 text-museum-accent animate-pulse">
          <Clock className="h-8 w-8" />
        </div>
      )}

      {/* Filters */}
      <div className="bg-museum-surface border border-museum-border rounded-museum-md p-6 shadow-sm overflow-visible relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <Select label={t.semesterLabel} value={selectedSem}
            onChange={e => { setSelectedSem(Number(e.target.value)); setSelectedVersionId(null); }}>
            <option value="">{t.selectSemester}</option>
            {semesters.map(s => (
              <option key={s.id} value={s.id}>{s.academic_year?.name} - {s.number} {t.semSuffix}</option>
            ))}
          </Select>
          <Select label={t.versionN} value={selectedVersionId || ''}
            onChange={e => setSelectedVersionId(Number(e.target.value))} disabled={versions.length === 0}>
            <option value="">{versions.length === 0 ? t.noData : t.open}</option>
            {versions.map(v => (
              <option key={v.id} value={v.id}>v{v.id} ({v.status}) - {new Date(v.created_at).toLocaleDateString()}</option>
            ))}
          </Select>
          <Select label={t.groupFilter} value={selectedGroup}
            onChange={e => setSelectedGroup(e.target.value ? Number(e.target.value) : '')}>
            <option value="">{t.allGroups}</option>
            {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
          </Select>
          <Select label={t.subjectFullName} value={selectedSubject}
            onChange={e => setSelectedSubject(e.target.value ? Number(e.target.value) : '')}>
            <option value="">{t.all}</option>
            {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </Select>
        </div>

        {selectedVersionId && currentVersion && (
          <div className="mt-6 pt-6 border-t border-museum-border flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 mr-auto">
              <span className={`px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider ${
                currentVersion.status === 'published' ? 'bg-museum-success/10 text-museum-success' :
                currentVersion.status === 'approved' ? 'bg-blue-100 text-blue-600' :
                'bg-museum-bg text-museum-text-secondary'}`}>
                {currentVersion.status === 'published' ? t.statusPublished :
                 currentVersion.status === 'approved' ? t.statusApproved :
                 currentVersion.status === 'archived' ? t.statusArchive : t.statusDraft}
              </span>
              <span className="text-xs text-museum-text-muted">
                {new Date(currentVersion.created_at).toLocaleString(lang === 'ru' ? 'ru-RU' : 'kk-KZ')}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {/* View toggle */}
              <div className="flex items-center border border-museum-border rounded-museum-sm overflow-hidden">
                <button
                  onClick={() => setViewMode('table')}
                  className={`px-3 py-1.5 text-xs font-bold flex items-center gap-1.5 transition-colors ${
                    viewMode === 'table' ? 'bg-museum-accent text-white' : 'text-museum-text-muted hover:bg-museum-surface-hover'}`}>
                  <TableProperties className="h-3.5 w-3.5" /> Таблица
                </button>
                <button
                  onClick={() => setViewMode('cards')}
                  className={`px-3 py-1.5 text-xs font-bold flex items-center gap-1.5 transition-colors ${
                    viewMode === 'cards' ? 'bg-museum-accent text-white' : 'text-museum-text-muted hover:bg-museum-surface-hover'}`}>
                  <LayoutGrid className="h-3.5 w-3.5" /> Карточки
                </button>
              </div>

              <Button variant="ghost" size="sm" onClick={() => handleExport(selectedVersionId)} loading={exporting}>
                <Download className="h-4 w-4 mr-2" />{t.exportExcel}
              </Button>
              {currentVersion.status === 'generated' && (
                <Button variant="ghost" size="sm" onClick={() => updateStatus(selectedVersionId, 'approved')}>
                  <CheckCircle className="h-4 w-4 mr-2 text-blue-500" />{t.approve}
                </Button>
              )}
              {currentVersion.status === 'approved' && (
                <Button variant="ghost" size="sm" onClick={() => updateStatus(selectedVersionId, 'published')}>
                  <Globe className="h-4 w-4 mr-2 text-museum-success" />{t.publish}
                </Button>
              )}
              {currentVersion.status === 'published' && (
                <Button variant="ghost" size="sm" onClick={() => updateStatus(selectedVersionId, 'archived')}>
                  <Archive className="h-4 w-4 mr-2" />{t.toArchive}
                </Button>
              )}
              <Button variant="ghost" size="sm" className="text-museum-danger hover:bg-museum-danger-soft"
                onClick={() => handleDelete(selectedVersionId)}>
                <Trash2 className="h-4 w-4" />
              </Button>
              <a href="/classrooms" target="_blank" rel="noreferrer"
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-bold text-museum-text-secondary hover:text-museum-accent transition-colors">
                <ExternalLink className="h-4 w-4" />{t.checkFreeClassrooms}
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Schedule display */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-museum-text">{t.scheduleVersions}</h2>
          <div className="text-xs text-museum-text-muted">
            {entries.length} {t.lessons} · {tableGroups.length} групп
          </div>
        </div>

        {!selectedVersionId ? (
          <div className="flex flex-col items-center justify-center py-20 bg-museum-surface border border-dashed border-museum-border rounded-museum-md text-museum-text-muted">
            <Info className="h-12 w-12 mb-4 opacity-20" />
            <p className="max-w-xs text-center">{t.selectSemesterHint}</p>
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-20 bg-museum-surface border border-museum-border rounded-museum-md">
            <p className="text-museum-text font-bold text-lg">{t.noEntriesForDisplay}</p>
            <p className="text-sm text-museum-text-muted mt-2">{t.tryAnotherGroup}</p>
          </div>
        ) : viewMode === 'table' ? (
          /* ═══ TABLE VIEW (как в оригинальном Excel) ══════════════════════ */
          <ScheduleTable
            tableGroups={tableGroups}
            entryMap={entryMap}
            onCellClick={handleCellClick}
            onEntryDrop={handleEntryDrop}
            onEntryContextMenu={handleContextMenu}
          />
        ) : (
          /* ═══ CARD VIEW (существующий) ═══════════════════════════════════ */
          <CardView entries={filteredEntries} t={t} />
        )}
      </div>

      {/* Generation Results Modal */}
      <Modal isOpen={showGenModal} onClose={() => setShowGenModal(false)} title={t.statusGenerated} size="lg">
        {genResult && (
          <div className="space-y-6">
            <div className="flex items-center justify-around p-6 bg-museum-accent/5 border border-museum-accent/10 rounded-museum-md">
              <div className="text-center">
                <div className="text-3xl font-black text-museum-accent">{genResult.placed_count}</div>
                <div className="text-[10px] uppercase font-bold text-museum-text-muted tracking-wider">{t.placed}</div>
              </div>
              <div className="h-10 w-[1px] bg-museum-border" />
              <div className="text-center">
                <div className="text-3xl font-black text-museum-text">{genResult.total_count}</div>
                <div className="text-[10px] uppercase font-bold text-museum-text-muted tracking-wider">{t.all}</div>
              </div>
              <div className="h-10 w-[1px] bg-museum-border" />
              <div className="text-center">
                <div className={`text-3xl font-black ${genResult.unplaced.length > 0 ? 'text-museum-danger' : 'text-museum-success'}`}>
                  {genResult.unplaced.length}
                </div>
                <div className="text-[10px] uppercase font-bold text-museum-text-muted tracking-wider">{t.unplacedLessons}</div>
              </div>
            </div>

            {genResult.unplaced.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-museum-danger flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />{t.unplacedLessons}
                </h3>
                <div className="max-h-60 overflow-y-auto border border-museum-border rounded-museum-md">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-museum-bg text-museum-text-muted uppercase text-[9px] font-bold">
                      <tr>
                        <th className="px-3 py-2">{t.dashboardGroups}</th>
                        <th className="px-3 py-2">{t.dashboardSubjects}</th>
                        <th className="px-3 py-2">{t.dashboardTeachers}</th>
                        <th className="px-3 py-2">Причина</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-museum-border">
                      {genResult.unplaced.map((u, i) => (
                        <tr key={i} className="hover:bg-museum-surface-hover">
                          <td className="px-3 py-2 font-bold">{u.group}</td>
                          <td className="px-3 py-2">{u.subject} ({u.lesson_type})</td>
                          <td className="px-3 py-2">{u.teacher}</td>
                          <td className="px-3 py-2 text-museum-danger">{u.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {genResult.warnings.length > 0 && (
              <div className="space-y-2 p-4 bg-yellow-50 border border-yellow-100 rounded-museum-md">
                <h4 className="text-xs font-bold text-yellow-700 uppercase flex items-center gap-2">
                  <Info className="h-3.5 w-3.5" />Предупреждения
                </h4>
                <ul className="text-xs text-yellow-600 list-disc list-inside space-y-1">
                  {genResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            <Button className="w-full" onClick={() => setShowGenModal(false)}>{t.close}</Button>
          </div>
        )}
      </Modal>

      {/* Context Menu */}
      {ctxMenu && (
        <div
          ref={ctxMenuRef}
          className="fixed z-[200] bg-museum-surface border border-museum-border rounded-museum-md shadow-2xl py-1 min-w-[190px] text-sm"
          style={{ left: ctxMenu.x, top: ctxMenu.y }}
        >
          <div className="px-3 py-2 border-b border-museum-border">
            <div className="font-bold text-museum-text text-[12px] leading-tight truncate max-w-[170px]">{ctxMenu.entry.subject_name}</div>
            <div className="text-[10px] text-museum-text-muted truncate max-w-[170px]">{ctxMenu.entry.group_name} · {ctxMenu.entry.lesson_type}</div>
          </div>
          <button
            className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-museum-accent/10 text-museum-text transition-colors"
            onClick={() => { setCtxMenu(null); const e = ctxMenu.entry; setEditingEntry(e); setEditFormData({ teacher_id: e.teacher_id || undefined, room_id: e.classroom_id || undefined, day_of_week: e.day_of_week, slot_number: e.time_slot_number }); }}
          >
            <Pencil className="h-3.5 w-3.5 text-museum-accent" />
            Редактировать
          </button>
          <button
            className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-blue-500/10 text-museum-text transition-colors"
            onClick={() => openMoveModal(ctxMenu.entry)}
          >
            <MoveRight className="h-3.5 w-3.5 text-blue-500" />
            Переместить
          </button>
          <div className="border-t border-museum-border mt-1 pt-1">
            <button
              className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-museum-danger/10 text-museum-danger transition-colors"
              onClick={() => handleCancelEntry(ctxMenu.entry)}
            >
              <Ban className="h-3.5 w-3.5" />
              Отменить занятие
            </button>
          </div>
        </div>
      )}

      {/* Move Entry Modal */}
      <Modal isOpen={!!moveEntry} onClose={() => { setMoveEntry(null); setMoveError(null); }} title="Переместить занятие" size="sm">
        {moveEntry && (
          <form className="space-y-4" onSubmit={handleMoveEntry}>
            <div className="p-3 bg-museum-bg rounded-museum-sm border border-museum-border">
              <p className="text-sm font-bold text-museum-text">{moveEntry.subject_name}</p>
              <p className="text-xs text-museum-text-muted mt-0.5">{moveEntry.group_name} · {moveEntry.lesson_type}</p>
              <p className="text-xs text-museum-text-muted">
                Сейчас: {DAY_NAMES_RU[moveEntry.day_of_week - 1]}, пара {moveEntry.time_slot_number} ({moveEntry.start_time}–{moveEntry.end_time})
              </p>
            </div>

            {moveError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-museum-sm text-red-700 text-xs">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-red-500" />
                <span>{moveError}</span>
              </div>
            )}

            <Select
              label="День недели"
              value={moveFormData.day_of_week}
              onChange={e => { setMoveError(null); setMoveFormData(prev => ({ ...prev, day_of_week: Number(e.target.value) })); }}
            >
              {DAY_NAMES_RU.map((n, i) => <option key={i + 1} value={i + 1}>{n}</option>)}
            </Select>
            <Select
              label="Слот времени"
              value={moveFormData.slot_number}
              onChange={e => { setMoveError(null); setMoveFormData(prev => ({ ...prev, slot_number: Number(e.target.value) })); }}
            >
              {TIME_SLOTS.map(s => <option key={s.num} value={s.num}>{s.num} пара · {s.label}</option>)}
            </Select>
            <div className="flex justify-end gap-3 pt-2 border-t border-museum-border">
              <Button type="button" variant="secondary" onClick={() => { setMoveEntry(null); setMoveError(null); }} disabled={moveSaving}>
                Отмена
              </Button>
              <Button type="submit" loading={moveSaving} icon={MoveRight}>
                Переместить
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Edit Entry Modal */}
      <Modal isOpen={!!editingEntry} onClose={() => { setEditingEntry(null); setEditError(null); }} title="Изменить ячейку">
        {editingEntry && (
          <form className="space-y-4" onSubmit={handleSaveEntry}>
            <div>
              <p className="text-sm font-bold text-museum-text">{editingEntry.subject_name}</p>
              <p className="text-xs text-museum-text-muted">{editingEntry.group_name} • {editingEntry.lesson_type}</p>
            </div>

            {editError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-museum-sm text-red-700 text-xs">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-red-500" />
                <span>{editError}</span>
              </div>
            )}
            
            <Select
              label="Преподаватель"
              value={editFormData.teacher_id || ''}
              onChange={e => { setEditError(null); setEditFormData({ ...editFormData, teacher_id: Number(e.target.value) }); }}
            >
              <option value="">Без преподавателя</option>
              {teachers.map(t => <option key={t.id} value={t.id}>{t.full_name}</option>)}
            </Select>

            <Select
              label="Аудитория"
              value={editFormData.room_id || ''}
              onChange={e => { setEditError(null); setEditFormData({ ...editFormData, room_id: Number(e.target.value) }); }}
            >
              <option value="">Без аудитории</option>
              {classrooms.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>

            <div className="grid grid-cols-2 gap-4">
              <Select
                label="День недели"
                value={editFormData.day_of_week || ''}
                onChange={e => setEditFormData({ ...editFormData, day_of_week: Number(e.target.value) })}
              >
                {DAY_NAMES_RU.map((n, i) => <option key={i+1} value={i+1}>{n}</option>)}
              </Select>

              <Select
                label="Слот времени"
                value={editFormData.slot_number || ''}
                onChange={e => setEditFormData({ ...editFormData, slot_number: Number(e.target.value) })}
              >
                {TIME_SLOTS.map(t => <option key={t.num} value={t.num}>{t.label}</option>)}
              </Select>
            </div>

            <div className="flex justify-between mt-6 pt-4 border-t border-museum-border">
              <Button type="button" variant="danger" icon={Trash2} onClick={handleDeleteEntry} loading={editSaving}>
                Удалить
              </Button>
              <div className="space-x-3 flex">
                <Button type="button" variant="secondary" onClick={() => setEditingEntry(null)} disabled={editSaving}>
                  {t.cancel}
                </Button>
                <Button type="submit" loading={editSaving}>
                  {t.save}
                </Button>
              </div>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}

// ─── Table View Component ──────────────────────────────────────────────────────
function ScheduleTable({
  tableGroups,
  entryMap,
  onCellClick,
  onEntryDrop,
  onEntryContextMenu,
}: {
  tableGroups: string[];
  entryMap: Map<string, ScheduleEntry>;
  onCellClick: (dayNum: number, slotNum: number, groupName: string, entry?: ScheduleEntry) => void;
  onEntryDrop: (entryId: number, targetDay: number, targetSlot: number, targetGroupName: string) => void;
  onEntryContextMenu: (e: React.MouseEvent, entry: ScheduleEntry) => void;
}) {
  if (tableGroups.length === 0) {
    return (
      <div className="text-center py-10 text-museum-text-muted text-sm">
        Нет данных для отображения
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-museum-border shadow-lg">
      <table className="border-collapse text-xs" style={{ minWidth: `${tableGroups.length * 200 + 240}px` }}>
        <thead>
          <tr className="bg-museum-surface border-b-2 border-museum-border">
            <th className="sticky left-0 z-20 bg-museum-surface border-r-2 border-museum-border px-3 py-3 text-left font-bold text-museum-text-muted uppercase tracking-wider text-[10px] whitespace-nowrap w-28">
              День
            </th>
            <th className="sticky left-28 z-20 bg-museum-surface border-r border-museum-border px-3 py-3 text-left font-bold text-museum-text-muted uppercase tracking-wider text-[10px] whitespace-nowrap w-10">
              №
            </th>
            <th className="sticky left-[160px] z-20 bg-museum-surface border-r-2 border-museum-border px-3 py-3 text-left font-bold text-museum-text-muted uppercase tracking-wider text-[10px] whitespace-nowrap w-28">
              Время
            </th>
            {tableGroups.map(gName => (
              <th key={gName}
                className="border-r border-museum-border px-3 py-3 text-center font-bold text-museum-accent text-[11px] uppercase tracking-wider min-w-[180px] max-w-[220px]">
                {gName}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[1, 2, 3, 4, 5, 6].map(dayNum => {
            const isSat = dayNum === 6;
            return TIME_SLOTS.map((slot, si) => {
              const isFirstSlot = si === 0;
              return (
                <tr key={`${dayNum}-${slot.num}`}
                  className={`border-b border-museum-border/60 hover:bg-museum-surface-hover/40 transition-colors ${
                    isSat ? 'bg-red-950/10' : si % 2 === 0 ? 'bg-museum-surface/40' : ''
                  } ${isFirstSlot ? 'border-t-2 border-t-museum-border' : ''}`}>

                  {/* Day cell - only for first slot */}
                  {isFirstSlot ? (
                    <td rowSpan={TIME_SLOTS.length}
                      className={`sticky left-0 z-10 border-r-2 border-museum-border text-center align-middle font-bold text-[11px] uppercase tracking-wider px-2 py-1 ${
                        isSat
                          ? 'bg-red-900/30 text-red-400'
                          : 'bg-museum-surface text-museum-text-muted'
                      }`}
                      style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', height: `${TIME_SLOTS.length * 68}px` }}>
                      {DAY_NAMES_RU[dayNum - 1]}
                    </td>
                  ) : null}

                  {/* Slot number */}
                  <td className="sticky left-28 z-10 bg-museum-surface border-r border-museum-border text-center font-black text-museum-accent text-[13px] px-2 py-2 w-10 align-top">
                    {slot.num}
                  </td>

                  {/* Time */}
                  <td className={`sticky left-[160px] z-10 border-r-2 border-museum-border px-3 py-2 font-mono text-[11px] font-semibold whitespace-nowrap align-top ${
                    isSat ? 'bg-red-950/20 text-red-400/70' : 'bg-museum-surface text-museum-text-muted'}`}>
                    {slot.label}
                  </td>

                  {tableGroups.map(gName => {
                    const entry = entryMap.get(`${dayNum}-${slot.num}-${gName}`);
                    return (
                      <td key={gName} 
                        className={`border-r border-museum-border/50 px-3 py-2 align-top min-w-[180px] max-w-[220px] transition-colors ${entry ? 'cursor-pointer hover:bg-museum-accent/10' : ''}`}
                        onClick={entry ? () => onCellClick(dayNum, slot.num, gName, entry) : undefined}
                        onDragOver={e => e.preventDefault()}
                        onDrop={e => {
                          e.preventDefault();
                          const entryIdStr = e.dataTransfer.getData('text/plain');
                          if (entryIdStr) {
                            onEntryDrop(Number(entryIdStr), dayNum, slot.num, gName);
                          }
                        }}
                      >
                        {entry ? (
                          <div
                            draggable
                            onDragStart={e => e.dataTransfer.setData('text/plain', entry.id.toString())}
                            onContextMenu={e => onEntryContextMenu(e, entry)}
                            title="ЛКМ — редактировать · ПКМ — контекстное меню · Перетащить — переместить"
                            className="space-y-1 bg-white hover:shadow-md cursor-grab active:cursor-grabbing p-1.5 rounded-md border border-museum-border/50 select-none"
                          >
                            <div className="font-semibold text-museum-text leading-tight text-[12px]">
                              {entry.subject_name}
                            </div>
                            {entry.classroom_name && entry.classroom_name !== '—' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">
                                <MapPin className="h-2.5 w-2.5" />
                                {entry.classroom_name}
                              </span>
                            )}
                            {entry.teacher_name && entry.teacher_name !== '—' && (
                              <div className="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/8 rounded px-1.5 py-0.5">
                                <Users className="h-2.5 w-2.5 shrink-0" />
                                <span className="leading-tight">{entry.teacher_name}</span>
                              </div>
                            )}
                            {entry.lesson_type && (
                              <span className="inline-block text-[9px] font-bold uppercase tracking-wider text-museum-accent/70 bg-museum-accent/8 px-1.5 py-0.5 rounded">
                                {entry.lesson_type}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-museum-text-muted/30 text-[11px]">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            });
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Card View Component (existing style) ────────────────────────────────────
function CardView({ entries, t }: { entries: ScheduleEntry[]; t: Record<string, string> }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[1, 2, 3, 4, 5, 6].map(dayNum => {
        const dayLessons = entries
          .filter(s => s.day_of_week === dayNum)
          .sort((a, b) => a.time_slot_number - b.time_slot_number);
        if (dayLessons.length === 0) return null;
        const dayNames = [t.monday, t.tuesday, t.wednesday, t.thursday, t.friday, t.saturday];
        return (
          <div key={dayNum} className="bg-museum-surface border border-museum-border rounded-museum-md overflow-hidden shadow-sm flex flex-col">
            <div className="bg-museum-accent px-4 py-2 text-white font-bold uppercase tracking-wider text-sm flex justify-between items-center">
              <span>{dayNames[dayNum - 1]}</span>
              <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded">{dayLessons.length}</span>
            </div>
            <div className="divide-y divide-museum-border/40 flex-1">
              {dayLessons.map((l, i) => (
                <div key={i} className={`p-4 hover:bg-museum-surface-hover transition-colors ${l.is_locked ? 'bg-museum-bg/30' : ''}`}>
                  <div className="flex items-start justify-between mb-2">
                    <span className="flex items-center gap-1.5 text-xs font-bold text-museum-accent bg-museum-accent-soft px-2 py-0.5 rounded">
                      {l.time_slot_number} {t.pair}
                    </span>
                    <span className="text-[10px] text-museum-text-muted font-bold font-mono flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" />
                      {l.start_time} - {l.end_time}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-museum-text mb-1 leading-tight line-clamp-2 min-h-[2.5rem]">
                    {l.subject_name}
                  </h3>
                  <div className="space-y-1.5">
                    <p className="text-xs text-museum-text-secondary flex items-center gap-1.5">
                      <Users className="h-3 w-3 text-museum-text-muted" /> {l.teacher_name}
                    </p>
                    <p className="text-xs text-museum-text-secondary flex items-center gap-1.5 font-bold">
                      <MapPin className="h-3 w-3 text-museum-text-accent" /> {l.classroom_name}
                    </p>
                  </div>
                  <div className="mt-3 flex items-center gap-1.5">
                    {l.week_type !== 'обе' && (
                      <span className="text-[9px] font-bold uppercase py-0.5 px-1.5 bg-museum-surface-light border border-museum-border rounded">
                        {l.week_type === 'числитель' ? t.weekNumerator : t.weekDenominator}
                      </span>
                    )}
                    <span className="text-[9px] font-bold uppercase py-0.5 px-1.5 bg-museum-accent-soft text-museum-accent border border-museum-accent/20 rounded">
                      {l.lesson_type}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
