import React, { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import Select from '../components/ui/Select';
import CsvImportButton from '../components/ui/CsvImportButton';
import { Plus, Pencil, Trash2 } from 'lucide-react';

interface Classroom {
  id: number;
  code: string;
  name: string;
  floor: number | null;
  capacity?: number | null;
  room_type_id: number | null;
}

export default function Classrooms() {
  const { t } = useLang();
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentClassroom, setCurrentClassroom] = useState<Partial<Classroom> | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchClassrooms = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<Classroom[]>('/classrooms');
      setClassrooms(data);
    } catch (error) {
      console.error('Failed to fetch classrooms:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const handleCreate = () => {
    setCurrentClassroom({ code: '', name: '', room_type_id: 1, floor: 1, capacity: null });
    setIsModalOpen(true);
  };

  const handleEdit = (classroom: Classroom) => {
    setCurrentClassroom(classroom);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm(t.confirmDeleteClassroom)) {
      try {
        await apiClient.delete(`/classrooms/${id}`);
        fetchClassrooms();
      } catch (error) {
        console.error('Failed to delete classroom:', error);
      }
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentClassroom?.code) return;

    setSaving(true);
    try {
      const payload = {
        code: currentClassroom.code,
        name: currentClassroom.name || currentClassroom.code,
        floor: currentClassroom.floor === null || currentClassroom.floor === undefined ? null : Number(currentClassroom.floor),
        capacity: currentClassroom.capacity === null || currentClassroom.capacity === undefined ? null : Number(currentClassroom.capacity),
        room_type_id: currentClassroom.room_type_id ? Number(currentClassroom.room_type_id) : 1,
      };
      if (currentClassroom.id) {
        await apiClient.put(`/classrooms/${currentClassroom.id}`, payload);
      } else {
        await apiClient.post('/classrooms', payload);
      }
      setIsModalOpen(false);
      fetchClassrooms();
    } catch (error) {
      console.error('Failed to save classroom:', error);
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    { key: 'code', header: t.classroomName },
    {
      key: 'room_type_id',
      header: t.classroomType,
      render: (c: Classroom) => {
        const types: Record<number, string> = {
          1: t.classroomTypeRegular,
          2: t.classroomTypeComputer,
          3: t.classroomTypeLab,
          4: t.classroomTypeGym,
          5: t.classroomTypeSpecial,
        };
        const id = c.room_type_id ?? 1;
        return types[id] || String(id);
      },
    },
    { key: 'floor', header: 'Этаж', className: 'w-24 text-center' },
    { key: 'capacity', header: 'Вместимость', render: (c: Classroom) => c.capacity ?? '—', className: 'w-32 text-center' },
    {
      key: 'actions',
      header: t.actions,
      render: (c: Classroom) => (
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => handleEdit(c)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(c.id)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
      className: 'w-24 text-right',
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-museum-text">{t.classroomsTitle}</h1>
        <div className="flex gap-2">
          <CsvImportButton endpoint="/classrooms/import-csv" onSuccess={fetchClassrooms} />
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            {t.addClassroom}
          </Button>
        </div>
      </div>

      <DataTable columns={columns} data={classrooms} loading={loading} />

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={currentClassroom?.id ? t.editClassroom : t.addClassroom}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label={t.classroomName}
            value={currentClassroom?.code || ''}
            onChange={(e) => {
              const code = e.target.value;
              setCurrentClassroom({ ...currentClassroom, code, name: currentClassroom?.name || code });
            }}
            placeholder={t.classroomNamePlaceholder}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label={t.classroomType}
              value={String(currentClassroom?.room_type_id ?? 1)}
              onChange={(e) => setCurrentClassroom({ ...currentClassroom, room_type_id: Number(e.target.value) })}
              required
            >
              <option value="1">{t.classroomTypeRegular}</option>
              <option value="2">{t.classroomTypeComputer}</option>
              <option value="3">{t.classroomTypeLab}</option>
              <option value="4">{t.classroomTypeGym}</option>
              <option value="5">{t.classroomTypeSpecial}</option>
            </Select>
            <Input
              label="Этаж"
              type="number"
              min="1"
              max="20"
              value={currentClassroom?.floor ?? 1}
              onChange={(e) => setCurrentClassroom({ ...currentClassroom, floor: Number(e.target.value) })}
              required
            />
          </div>
          <Input
            label="Вместимость (мест)"
            type="number"
            min="1"
            max="500"
            value={currentClassroom?.capacity ?? ''}
            onChange={(e) => setCurrentClassroom({
              ...currentClassroom,
              capacity: e.target.value === '' ? null : Number(e.target.value)
            })}
            placeholder="Например: 30"
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              {t.cancel}
            </Button>
            <Button type="submit" loading={saving}>
              {t.save}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
