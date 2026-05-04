import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import { Plus, Pencil, Trash2 } from 'lucide-react';

interface LessonType {
  id: number;
  code: string;
  name: string;
  is_lab: boolean;
  requires_room_match: boolean;
  is_active: boolean;
}

export default function LessonTypes() {
  const [items, setItems] = useState<LessonType[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [current, setCurrent] = useState<Partial<LessonType>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetch = async () => {
    setLoading(true);
    try { setItems(await apiClient.get<LessonType[]>('/lesson-types')); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetch(); }, []);

  const openCreate = () => {
    setCurrent({ code: '', name: '', is_lab: false, requires_room_match: true });
    setError('');
    setModal(true);
  };

  const openEdit = (lt: LessonType) => {
    setCurrent({ ...lt });
    setError('');
    setModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!current.code || !current.name) { setError('Заполните код и название'); return; }
    setSaving(true);
    setError('');
    try {
      if (current.id) {
        await apiClient.put(`/lesson-types/${current.id}`, {
          code: current.code, name: current.name,
          is_lab: current.is_lab, requires_room_match: current.requires_room_match,
        });
      } else {
        await apiClient.post('/lesson-types', {
          code: current.code, name: current.name,
          is_lab: current.is_lab ?? false,
          requires_room_match: current.requires_room_match ?? true,
        });
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
    if (!window.confirm('Удалить вид занятий?')) return;
    try { await apiClient.delete(`/lesson-types/${id}`); fetch(); }
    catch (err: any) { alert(err.message); }
  };

  const columns = [
    { key: 'code', header: 'Код', render: (lt: LessonType) => <span className="font-mono font-bold text-xs bg-museum-bg border border-museum-border px-1.5 py-0.5 rounded">{lt.code}</span> },
    { key: 'name', header: 'Название' },
    {
      key: 'is_lab', header: 'Лаб. занятие',
      render: (lt: LessonType) => lt.is_lab
        ? <span className="text-xs font-bold text-blue-500">Да</span>
        : <span className="text-xs text-museum-text-muted">Нет</span>,
    },
    {
      key: 'requires_room_match', header: 'Соответствие аудитории',
      render: (lt: LessonType) => lt.requires_room_match
        ? <span className="text-xs font-bold text-museum-success">Да</span>
        : <span className="text-xs text-museum-text-muted">Нет</span>,
    },
    {
      key: 'actions', header: 'Действия', className: 'w-24 text-right',
      render: (lt: LessonType) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => openEdit(lt)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(lt.id)}>
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
          <h1 className="text-2xl font-bold text-museum-text">Виды занятий</h1>
          <p className="text-sm text-museum-text-muted mt-1">Лекция, практика, лабораторная и т.д.</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" /> Добавить
        </Button>
      </div>

      <DataTable columns={columns} data={items} loading={loading} />

      <Modal isOpen={modal} onClose={() => setModal(false)}
        title={current.id ? 'Редактировать вид занятий' : 'Новый вид занятий'}>
        <form onSubmit={handleSave} className="space-y-4">
          <Input label="Код (напр. LEC, LAB, PRAC)" value={current.code || ''} required
            onChange={e => setCurrent({ ...current, code: e.target.value.toUpperCase() })} />
          <Input label="Название (напр. Лекция)" value={current.name || ''} required
            onChange={e => setCurrent({ ...current, name: e.target.value })} />
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={current.is_lab ?? false}
              onChange={e => setCurrent({ ...current, is_lab: e.target.checked })}
              className="w-4 h-4 accent-museum-accent" />
            <span className="text-sm font-bold text-museum-text">Лабораторное занятие</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={current.requires_room_match ?? true}
              onChange={e => setCurrent({ ...current, requires_room_match: e.target.checked })}
              className="w-4 h-4 accent-museum-accent" />
            <span className="text-sm font-bold text-museum-text">Требует соответствия типа аудитории</span>
          </label>
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
