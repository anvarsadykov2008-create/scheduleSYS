import React, { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import CsvImportButton from '../components/ui/CsvImportButton';
import { Plus, Pencil, Trash2, Library, CalendarOff, DoorOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

interface AcademicPeriod {
  id: number;
  name: string;
}

interface Teacher {
  id: number;
  last_name: string;
  first_name: string;
  middle_name?: string | null;
  full_name: string;
  home_room_id?: number | null;
  is_head_of_department?: boolean;
  department_id?: number | null;
}

interface Classroom {
  id: number;
  code: string;
  name: string;
}

interface Department {
  id: number;
  name: string;
}

const DAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

export default function Teachers() {
  const { t } = useLang();
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentTeacher, setCurrentTeacher] = useState<Partial<Teacher> | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);

  // Недоступные дни
  const [isDaysModalOpen, setIsDaysModalOpen] = useState(false);
  const [daysTeacher, setDaysTeacher] = useState<Teacher | null>(null);
  const [periods, setPeriods] = useState<AcademicPeriod[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [unavailableDays, setUnavailableDays] = useState<number[]>([]);
  const [daysSaving, setDaysSaving] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [teachersData, classroomsData, departmentsData] = await Promise.all([
        apiClient.get<Teacher[]>('/teachers'),
        apiClient.get<Classroom[]>('/classrooms'),
        apiClient.get<Department[]>('/departments'),
      ]);
      setTeachers(teachersData);
      setClassrooms(classroomsData);
      setDepartments(departmentsData);
    } catch (err) {
      console.error('Failed to fetch teachers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openDaysModal = async (teacher: Teacher) => {
    setDaysTeacher(teacher);
    setUnavailableDays([]);
    setDaysSaving(false);
    try {
      const ps = await apiClient.get<AcademicPeriod[]>('/academic-periods');
      setPeriods(ps);
      const firstId = ps[0]?.id ?? null;
      setSelectedPeriod(firstId);
      if (firstId) {
        const data = await apiClient.get<{ unavailable_days: number[] }>(
          `/teachers/${teacher.id}/unavailable-days?semester_id=${firstId}`
        );
        setUnavailableDays(data.unavailable_days);
      }
    } catch (e) {
      console.error(e);
    }
    setIsDaysModalOpen(true);
  };

  const handlePeriodChange = async (periodId: number) => {
    setSelectedPeriod(periodId);
    if (!daysTeacher) return;
    try {
      const data = await apiClient.get<{ unavailable_days: number[] }>(
        `/teachers/${daysTeacher.id}/unavailable-days?semester_id=${periodId}`
      );
      setUnavailableDays(data.unavailable_days);
    } catch (e) {
      console.error(e);
    }
  };

  const toggleDay = (day: number) => {
    setUnavailableDays(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
    );
  };

  const saveDays = async () => {
    if (!daysTeacher || !selectedPeriod) return;
    setDaysSaving(true);
    try {
      await apiClient.put(
        `/teachers/${daysTeacher.id}/unavailable-days?semester_id=${selectedPeriod}`,
        unavailableDays
      );
      setIsDaysModalOpen(false);
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Ошибка сохранения');
    } finally {
      setDaysSaving(false);
    }
  };

  const handleCreate = () => {
    setCurrentTeacher({ last_name: '', first_name: '', middle_name: '', is_head_of_department: false, home_room_id: null, department_id: null });
    setError('');
    setIsModalOpen(true);
  };

  const handleEdit = (teacher: Teacher) => {
    setCurrentTeacher(teacher);
    setError('');
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm(t.confirmDeleteTeacher)) {
      try {
        await apiClient.delete(`/teachers/${id}`);
        fetchData();
      } catch (err) {
        alert(err instanceof Error ? err.message : t.error);
      }
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentTeacher?.last_name || !currentTeacher?.first_name) {
      setError('Фамилия и имя обязательны');
      return;
    }

    setSaving(true);
    setError('');
    try {
      const payload = {
        last_name: currentTeacher.last_name.trim(),
        first_name: currentTeacher.first_name.trim(),
        middle_name: currentTeacher.middle_name?.trim() || null,
        home_room_id: currentTeacher.home_room_id ? Number(currentTeacher.home_room_id) : null,
        is_head_of_department: !!currentTeacher.is_head_of_department,
        department_id: currentTeacher.is_head_of_department && currentTeacher.department_id ? Number(currentTeacher.department_id) : null,
      };
      if (currentTeacher.id) {
        await apiClient.put(`/teachers/${currentTeacher.id}`, payload);
      } else {
        await apiClient.post('/teachers', payload);
      }
      setIsModalOpen(false);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    { key: 'full_name', header: t.teacherFullName },
    {
      key: 'actions',
      header: t.actions,
      render: (teacher: Teacher) => (
        <div className="flex gap-2">
          <Link to={`/admin/teacher-subjects/${teacher.id}`}>
            <Button variant="ghost" size="sm" title={t.teacherWorkloadBtn}>
              <Library className="h-4 w-4" />
            </Button>
          </Link>
          <Link to={`/admin/teacher-rooms/${teacher.id}`}>
            <Button variant="ghost" size="sm" title="Кабинеты преподавателя">
              <DoorOpen className="h-4 w-4" />
            </Button>
          </Link>
          <Button variant="ghost" size="sm" title="Недоступные дни" onClick={() => openDaysModal(teacher)}>
            <CalendarOff className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => handleEdit(teacher)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(teacher.id)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
      className: 'w-44 text-right',
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-museum-text">{t.teachersTitle}</h1>
        <div className="flex gap-2">
          <CsvImportButton endpoint="/teachers/import-csv" onSuccess={fetchData} />
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            {t.addTeacher}
          </Button>
        </div>
      </div>

      <DataTable columns={columns} data={teachers} loading={loading} />

      <Modal
        isOpen={isDaysModalOpen}
        onClose={() => setIsDaysModalOpen(false)}
        title={`Недоступные дни — ${daysTeacher?.full_name}`}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-museum-text mb-1">Семестр</label>
            <select
              className="w-full border border-museum-border rounded-md px-3 py-2 text-sm bg-white"
              value={selectedPeriod ?? ''}
              onChange={e => handlePeriodChange(Number(e.target.value))}
            >
              {periods.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <p className="text-sm font-medium text-museum-text mb-2">Выберите дни, когда преподаватель недоступен:</p>
            <div className="grid grid-cols-7 gap-2">
              {DAY_NAMES.map((name, idx) => {
                const day = idx + 1;
                const checked = unavailableDays.includes(day);
                return (
                  <button
                    key={day}
                    type="button"
                    onClick={() => toggleDay(day)}
                    className={`py-2 rounded text-sm font-medium border transition-colors ${
                      checked
                        ? 'bg-museum-danger text-white border-museum-danger'
                        : 'bg-white text-museum-text border-museum-border hover:bg-museum-bg'
                    }`}
                  >
                    {name}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="secondary" type="button" onClick={() => setIsDaysModalOpen(false)}>
              {t.cancel}
            </Button>
            <Button onClick={saveDays} loading={daysSaving}>
              {t.save}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={currentTeacher?.id ? t.editTeacher : t.addTeacher}
      >
        <form onSubmit={handleSave} className="space-y-4">
          {error && (
            <div className="text-sm text-museum-danger bg-museum-danger/10 border border-museum-danger/20 rounded p-3">
              {error}
            </div>
          )}
          <Input
            label="Фамилия"
            value={currentTeacher?.last_name || ''}
            onChange={(e) => setCurrentTeacher({ ...currentTeacher, last_name: e.target.value })}
            placeholder="Иванов"
            required
          />
          <Input
            label="Имя"
            value={currentTeacher?.first_name || ''}
            onChange={(e) => setCurrentTeacher({ ...currentTeacher, first_name: e.target.value })}
            placeholder="Иван"
            required
          />
          <Input
            label="Отчество"
            value={currentTeacher?.middle_name || ''}
            onChange={(e) => setCurrentTeacher({ ...currentTeacher, middle_name: e.target.value })}
            placeholder="Иванович"
          />
          <div>
            <label className="block text-sm font-medium text-museum-text mb-1">Кабинет (Офис)</label>
            <select
              className="w-full border border-museum-border rounded-md px-3 py-2 text-sm bg-white"
              value={currentTeacher?.home_room_id || ''}
              onChange={(e) => setCurrentTeacher({ ...currentTeacher, home_room_id: e.target.value ? Number(e.target.value) : null })}
            >
              <option value="">Не назначен</option>
              {classrooms.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2 mt-4">
            <input
              type="checkbox"
              id="is_head"
              className="rounded border-museum-border text-museum-accent focus:ring-museum-accent"
              checked={currentTeacher?.is_head_of_department || false}
              onChange={(e) => setCurrentTeacher({ ...currentTeacher, is_head_of_department: e.target.checked })}
            />
            <label htmlFor="is_head" className="text-sm font-medium text-museum-text">
              Является заведующим отделением
            </label>
          </div>
          {currentTeacher?.is_head_of_department && (
            <div>
              <label className="block text-sm font-medium text-museum-text mb-1">Отделение</label>
              <select
                className="w-full border border-museum-border rounded-md px-3 py-2 text-sm bg-white"
                value={currentTeacher?.department_id || ''}
                onChange={(e) => setCurrentTeacher({ ...currentTeacher, department_id: e.target.value ? Number(e.target.value) : null })}
                required
              >
                <option value="">Выберите отделение</option>
                {departments.map(d => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
          )}
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" type="button" onClick={() => setIsModalOpen(false)}>
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
