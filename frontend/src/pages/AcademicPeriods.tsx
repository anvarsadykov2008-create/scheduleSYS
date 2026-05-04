import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import { Plus, Pencil, Trash2, CheckCircle, XCircle } from 'lucide-react';

interface AcademicPeriod {
  id: number;
  name: string;
  code: string;
  academic_year: string;
  term_no: number;
  is_active: boolean;
}

export default function AcademicPeriods() {
  const [periods, setPeriods] = useState<AcademicPeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [current, setCurrent] = useState<Partial<AcademicPeriod>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetch = async () => {
    setLoading(true);
    try { setPeriods(await apiClient.get<AcademicPeriod[]>('/academic-periods')); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetch(); }, []);

  const openCreate = () => {
    setCurrent({ name: '', code: '', academic_year: '2025-2026', term_no: 1, is_active: true });
    setError('');
    setModal(true);
  };

  const openEdit = (p: AcademicPeriod) => {
    setCurrent({ ...p });
    setError('');
    setModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!current.name) { setError('Введите название'); return; }
    setSaving(true);
    setError('');
    try {
      const payload = {
        name: current.name,
        code: current.code || current.name,
        academic_year: current.academic_year || '',
        term_no: Number(current.term_no) || 1,
      };
      if (current.id) {
        await apiClient.put(`/academic-periods/${current.id}`, { name: current.name, is_active: current.is_active });
      } else {
        await apiClient.post('/academic-periods', payload);
      }
      setModal(false);
      fetch();
    } catch (err: any) {
      setError(err.message || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Удалить учебный период?')) return;
    try { await apiClient.delete(`/academic-periods/${id}`); fetch(); }
    catch (err: any) { alert(err.message); }
  };

  const columns = [
    { key: 'name', header: 'Название' },
    { key: 'code', header: 'Код', render: (p: AcademicPeriod) => <span className="font-mono text-xs">{p.code}</span> },
    { key: 'academic_year', header: 'Учебный год' },
    { key: 'term_no', header: 'Семестр', render: (p: AcademicPeriod) => `${p.term_no} семестр` },
    {
      key: 'is_active', header: 'Статус',
      render: (p: AcademicPeriod) => p.is_active
        ? <span className="flex items-center gap-1 text-museum-success text-xs font-bold"><CheckCircle className="h-3 w-3" />Активный</span>
        : <span className="flex items-center gap-1 text-museum-text-muted text-xs"><XCircle className="h-3 w-3" />Неактивный</span>,
    },
    {
      key: 'actions', header: 'Действия', className: 'w-24 text-right',
      render: (p: AcademicPeriod) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => openEdit(p)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(p.id)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-museum-text">Учебные периоды</h1>
          <p className="text-sm text-museum-text-muted mt-1">Семестры для привязки нагрузки и расписания</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" /> Добавить период
        </Button>
      </div>

      <DataTable columns={columns} data={periods} loading={loading} />

      <Modal isOpen={modal} onClose={() => setModal(false)}
        title={current.id ? 'Редактировать период' : 'Новый учебный период'}>
        <form onSubmit={handleSave} className="space-y-4">
          <Input label="Название (напр. «1 семестр 2025-2026»)" value={current.name || ''} required
            onChange={e => setCurrent({ ...current, name: e.target.value })} />
          <Input label="Код (напр. 2025-1)" value={current.code || ''}
            onChange={e => setCurrent({ ...current, code: e.target.value })} />
          <Input label="Учебный год (напр. 2025-2026)" value={current.academic_year || ''}
            onChange={e => setCurrent({ ...current, academic_year: e.target.value })} />
          <div>
            <label className="block text-sm font-bold text-museum-text mb-1">Номер семестра</label>
            <select
              className="w-full border border-museum-border rounded-museum-sm px-3 py-2 bg-museum-bg text-museum-text text-sm"
              value={current.term_no || 1}
              onChange={e => setCurrent({ ...current, term_no: Number(e.target.value) })}
            >
              <option value={1}>1 семестр</option>
              <option value={2}>2 семестр</option>
            </select>
          </div>
          {current.id && (
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={current.is_active ?? true}
                onChange={e => setCurrent({ ...current, is_active: e.target.checked })}
                className="w-4 h-4 accent-museum-accent" />
              <span className="text-sm font-bold text-museum-text">Активный</span>
            </label>
          )}
          {error && <p className="text-sm text-museum-danger">{error}</p>}
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" type="button" onClick={() => setModal(false)}>Отмена</Button>
            <Button type="submit" loading={saving}>Сохранить</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
