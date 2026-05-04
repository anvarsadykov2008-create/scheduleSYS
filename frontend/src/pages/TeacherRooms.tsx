import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Modal from '../components/ui/Modal';
import { Plus, Trash2, ArrowLeft, Star } from 'lucide-react';

interface TeacherRoom {
  id: number;
  teacher_id: number;
  room_id: number;
  room_code: string;
  room_name: string;
  is_primary: boolean;
}

interface Room { id: number; code: string; name: string; }
interface Teacher { id: number; full_name: string; }

export default function TeacherRooms() {
  const { t } = useLang();
  const { teacherId } = useParams<{ teacherId: string }>();
  const navigate = useNavigate();

  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [links, setLinks] = useState<TeacherRoom[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRoomId, setNewRoomId] = useState(0);
  const [isPrimary, setIsPrimary] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [linksData, roomsData, teacherData] = await Promise.all([
        apiClient.get<TeacherRoom[]>(`/teachers/${teacherId}/rooms`),
        apiClient.get<Room[]>('/classrooms'),
        apiClient.get<Teacher>(`/teachers/${teacherId}`),
      ]);
      setLinks(linksData);
      setRooms(roomsData);
      setTeacher(teacherData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [teacherId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAdd = () => {
    setNewRoomId(rooms[0]?.id || 0);
    setIsPrimary(false);
    setError('');
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await apiClient.post(`/teachers/${teacherId}/rooms`, {
        room_id: Number(newRoomId),
        is_primary: isPrimary,
      });
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      setError(err.message || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (link: TeacherRoom) => {
    if (window.confirm('Удалить привязку кабинета?')) {
      try {
        await apiClient.delete(`/teachers/${link.teacher_id}/rooms/${link.room_id}`);
        fetchData();
      } catch (e) {
        console.error(e);
      }
    }
  };

  const columns = [
    {
      key: 'code',
      header: 'Кабинет',
      render: (l: TeacherRoom) => (
        <span className="font-mono font-bold text-museum-text">{l.room_code}</span>
      ),
    },
    {
      key: 'name',
      header: 'Название',
      render: (l: TeacherRoom) => l.room_name,
    },
    {
      key: 'primary',
      header: 'Основной',
      render: (l: TeacherRoom) => l.is_primary
        ? <span className="flex items-center gap-1 text-museum-accent text-xs font-bold"><Star className="h-3 w-3 fill-current" /> Основной</span>
        : <span className="text-museum-text-muted text-xs">—</span>,
    },
    {
      key: 'actions',
      header: t.actions,
      render: (l: TeacherRoom) => (
        <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(l)}>
          <Trash2 className="h-4 w-4" />
        </Button>
      ),
      className: 'w-24 text-right',
    },
  ];

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/admin/teachers')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t.back}
        </Button>
        <h1 className="text-2xl font-bold text-museum-text">
          Кабинеты: {teacher?.full_name}
        </h1>
        <div className="flex-1" />
        <Button onClick={handleAdd}>
          <Plus className="h-4 w-4 mr-2" />
          {t.add}
        </Button>
      </div>

      <DataTable columns={columns} data={links} loading={loading} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Привязать кабинет">
        <form onSubmit={handleSave} className="space-y-4">
          <Select
            label="Кабинет"
            value={newRoomId}
            onChange={(e) => setNewRoomId(Number(e.target.value))}
            required
          >
            <option value="">Выберите кабинет</option>
            {rooms.map(r => (
              <option key={r.id} value={r.id}>{r.code} — {r.name}</option>
            ))}
          </Select>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={isPrimary}
              onChange={(e) => setIsPrimary(e.target.checked)}
              className="w-4 h-4 accent-museum-accent"
            />
            <span className="text-sm font-bold text-museum-text">Основной кабинет</span>
          </label>

          {error && (
            <p className="text-sm text-museum-danger">{error}</p>
          )}

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" type="button" onClick={() => setIsModalOpen(false)}>{t.cancel}</Button>
            <Button type="submit" loading={saving}>{t.save}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
