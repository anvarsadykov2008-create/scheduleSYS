import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import { Plus, Pencil, Trash2, Upload, RefreshCw } from 'lucide-react';

interface Group { id: number; name: string; code: string; }
interface Subject { id: number; name: string; code: string; }
interface Teacher { id: number; full_name: string; }
interface AcademicPeriod { id: number; name: string; term_no: number; }

interface HourGridEntry {
  id: number;
  group_id: number;
  subject_id: number;
  lesson_type_id: number;
  academic_period_id: number;
  planned_weekly_hours: number;
  total_hours: number;
  preferred_teacher_id: number | null;
  is_mandatory: boolean;
  notes: string | null;
}
interface LessonType { id: number; code: string; name: string; }

export default function HourGrid() {
  const [entries, setEntries] = useState<HourGridEntry[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [periods, setPeriods] = useState<AcademicPeriod[]>([]);
  const [lessonTypes, setLessonTypes] = useState<LessonType[]>([]);
  const [loading, setLoading] = useState(false);

  const [filterGroup, setFilterGroup] = useState('');
  const [filterPeriod, setFilterPeriod] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [current, setCurrent] = useState<Partial<HourGridEntry> | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<string | null>(null);
  const [importPeriod, setImportPeriod] = useState('');
  const [importGroup, setImportGroup] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([
      apiClient.get<Group[]>('/groups'),
      apiClient.get<Subject[]>('/subjects'),
      apiClient.get<Teacher[]>('/teachers'),
      apiClient.get<AcademicPeriod[]>('/academic-periods'),
      apiClient.get<LessonType[]>('/lesson-types'),
    ]).then(([g, s, t, p, lt]) => {
      setGroups(g);
      setSubjects(s);
      setTeachers(t);
      setPeriods(p);
      setLessonTypes(lt);
      if (p.length) setImportPeriod(String(p[0].id));
    });
  }, []);

  const fetchEntries = async () => {
    if (!filterGroup && !filterPeriod) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterGroup) params.set('group_id', filterGroup);
      if (filterPeriod) params.set('academic_period_id', filterPeriod);
      const data = await apiClient.get<HourGridEntry[]>(`/hour-grid?${params}`);
      setEntries(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEntries(); }, [filterGroup, filterPeriod]);

  const subjectMap = Object.fromEntries(subjects.map(s => [s.id, s.name]));
  const teacherMap = Object.fromEntries(teachers.map(t => [t.id, t.full_name]));
  const groupMap = Object.fromEntries(groups.map(g => [g.id, g.name]));

  const openCreate = () => {
    setCurrent({
      group_id: filterGroup ? Number(filterGroup) : undefined,
      academic_period_id: filterPeriod ? Number(filterPeriod) : undefined,
      lesson_type_id: 1,
      planned_weekly_hours: 2,
      total_hours: 36,
      is_mandatory: true,
    });
    setError('');
    setIsModalOpen(true);
  };

  const openEdit = (e: HourGridEntry) => {
    setCurrent({ ...e });
    setError('');
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Удалить запись?')) return;
    try {
      await apiClient.delete(`/hour-grid/${id}`);
      fetchEntries();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Ошибка');
    }
  };

  const handleSave = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!current?.group_id || !current?.subject_id || !current?.academic_period_id) {
      setError('Заполните группу, предмет и семестр');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const payload = {
        group_id: Number(current.group_id),
        subject_id: Number(current.subject_id),
        lesson_type_id: Number(current.lesson_type_id ?? 1),
        academic_period_id: Number(current.academic_period_id),
        planned_weekly_hours: Number(current.planned_weekly_hours),
        total_hours: Number(current.total_hours),
        preferred_teacher_id: current.preferred_teacher_id ? Number(current.preferred_teacher_id) : null,
        is_mandatory: current.is_mandatory ?? true,
        notes: current.notes ?? null,
      };
      if (current.id) {
        await apiClient.put(`/hour-grid/${current.id}`, payload);
      } else {
        await apiClient.post('/hour-grid', payload);
      }
      setIsModalOpen(false);
      fetchEntries();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleImport = async (ev: React.ChangeEvent<HTMLInputElement>) => {
    const f = ev.target.files?.[0];
    if (!f) return;
    setImporting(true);
    setImportResult(null);
    try {
      const form = new FormData();
      form.append('file', f);
      const token = localStorage.getItem('token') || sessionStorage.getItem('token') || '';
      const groupParam = importGroup ? `&group_id=${importGroup}` : '';
      const res = await fetch(
        `/api/hour-grid/import-file?academic_period_id=${importPeriod}&weeks=18${groupParam}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка');
      setImportResult(`✓ ${data.message}${data.errors?.length ? '\nПредупреждения:\n' + data.errors.join('\n') : ''}`);
      fetchEntries();
    } catch (e) {
      setImportResult(`Ошибка: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-museum-text">Сетка часов</h1>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Добавить
        </Button>
      </div>

      {/* Фильтры */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          className="border border-museum-border rounded-md px-3 py-2 text-sm bg-white min-w-[180px]"
          value={filterGroup}
          onChange={e => setFilterGroup(e.target.value)}
        >
          <option value="">— Все группы —</option>
          {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
        <select
          className="border border-museum-border rounded-md px-3 py-2 text-sm bg-white min-w-[200px]"
          value={filterPeriod}
          onChange={e => setFilterPeriod(e.target.value)}
        >
          <option value="">— Все семестры —</option>
          {periods.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <Button variant="ghost" onClick={fetchEntries} title="Обновить">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Импорт из файла */}
      <div className="flex items-center gap-3 mb-6 p-3 bg-museum-bg border border-museum-border rounded-lg">
        <Upload className="h-4 w-4 text-museum-muted flex-shrink-0" />
        <span className="text-sm text-museum-muted">Импорт из .docx / .xls:</span>
        <select
          className="border border-museum-border rounded px-2 py-1 text-sm bg-white"
          value={importPeriod}
          onChange={e => setImportPeriod(e.target.value)}
        >
          {periods.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <select
          className="border border-museum-border rounded px-2 py-1 text-sm bg-white min-w-[160px]"
          value={importGroup}
          onChange={e => setImportGroup(e.target.value)}
        >
          <option value="">— группа из файла —</option>
          {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
        <label className={`cursor-pointer text-sm px-3 py-1.5 rounded bg-museum-accent text-white hover:opacity-90 transition ${importing ? 'opacity-60 pointer-events-none' : ''}`}>
          {importing ? 'Загрузка...' : 'Выбрать файл'}
          <input ref={fileRef} type="file" accept=".docx,.xls,.xlsx" className="hidden" onChange={handleImport} />
        </label>
      </div>

      {importResult && (
        <pre className="mb-4 p-3 text-xs bg-museum-bg border border-museum-border rounded whitespace-pre-wrap max-h-40 overflow-auto">
          {importResult}
        </pre>
      )}

      {/* Таблица */}
      {!filterGroup && !filterPeriod ? (
        <div className="text-center text-museum-muted py-12">Выберите группу или семестр для отображения</div>
      ) : loading ? (
        <div className="text-center text-museum-muted py-12">Загрузка...</div>
      ) : entries.length === 0 ? (
        <div className="text-center text-museum-muted py-12">Нет записей</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-museum-bg border-b border-museum-border">
                <th className="text-left px-3 py-2 font-medium text-museum-muted">Группа</th>
                <th className="text-left px-3 py-2 font-medium text-museum-muted">Предмет</th>
                <th className="text-center px-3 py-2 font-medium text-museum-muted w-24">Всего ч.</th>
                <th className="text-center px-3 py-2 font-medium text-museum-muted w-28">Нед. ч.</th>
                <th className="text-left px-3 py-2 font-medium text-museum-muted">Преподаватель</th>
                <th className="w-20 text-right px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {entries.map(e => (
                <tr key={e.id} className="border-b border-museum-border hover:bg-museum-bg/50">
                  <td className="px-3 py-2">{groupMap[e.group_id] ?? e.group_id}</td>
                  <td className="px-3 py-2">{subjectMap[e.subject_id] ?? e.subject_id}</td>
                  <td className="px-3 py-2 text-center">{e.total_hours}</td>
                  <td className="px-3 py-2 text-center">{e.planned_weekly_hours}</td>
                  <td className="px-3 py-2 text-museum-muted">
                    {e.preferred_teacher_id ? teacherMap[e.preferred_teacher_id] ?? '—' : '—'}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(e)}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(e.id)}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Модальное окно */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={current?.id ? 'Редактировать запись' : 'Новая запись'}
      >
        <form onSubmit={handleSave} className="space-y-3">
          {error && (
            <div className="text-sm text-museum-danger bg-museum-danger/10 border border-museum-danger/20 rounded p-2">
              {error}
            </div>
          )}
          <Select
            label="Группа"
            value={String(current?.group_id ?? '')}
            onChange={e => setCurrent(c => ({ ...c, group_id: Number(e.target.value) }))}
            required
          >
            <option value="">— выберите —</option>
            {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
          </Select>
          <Select
            label="Семестр"
            value={String(current?.academic_period_id ?? '')}
            onChange={e => setCurrent(c => ({ ...c, academic_period_id: Number(e.target.value) }))}
            required
          >
            <option value="">— выберите —</option>
            {periods.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </Select>
          <Select
            label="Предмет"
            value={String(current?.subject_id ?? '')}
            onChange={e => setCurrent(c => ({ ...c, subject_id: Number(e.target.value) }))}
            required
          >
            <option value="">— выберите —</option>
            {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </Select>
          <Select
            label="Вид занятий"
            value={String(current?.lesson_type_id ?? '')}
            onChange={e => setCurrent(c => ({ ...c, lesson_type_id: Number(e.target.value) }))}
            required
          >
            <option value="">— выберите —</option>
            {lessonTypes.map(lt => <option key={lt.id} value={lt.id}>{lt.name}</option>)}
          </Select>
          <Select
            label="Преподаватель (желаемый)"
            value={String(current?.preferred_teacher_id ?? '')}
            onChange={e => setCurrent(c => ({ ...c, preferred_teacher_id: e.target.value ? Number(e.target.value) : null }))}
          >
            <option value="">— не указан —</option>
            {teachers.map(t => <option key={t.id} value={t.id}>{t.full_name}</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Всего часов"
              type="number"
              min="1"
              value={current?.total_hours ?? ''}
              onChange={e => setCurrent(c => ({ ...c, total_hours: Number(e.target.value) }))}
              required
            />
            <Input
              label="Часов в неделю"
              type="number"
              min="0.5"
              step="0.01"
              value={current?.planned_weekly_hours ?? ''}
              onChange={e => setCurrent(c => ({ ...c, planned_weekly_hours: Number(e.target.value) }))}
              required
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setIsModalOpen(false)}>Отмена</Button>
            <Button type="submit" loading={saving}>Сохранить</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
