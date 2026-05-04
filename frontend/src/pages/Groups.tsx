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

interface Specialty {
  specialty_id: number;
  name: string;
  department_id: number;
}

interface Group {
  id: number;
  name: string;
  code?: string;
  course_no?: number;
  specialty_id?: number;
  student_count?: number;
}

export default function Groups() {
  const { t } = useLang();
  const [groups, setGroups] = useState<Group[]>([]);
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentGroup, setCurrentGroup] = useState<Partial<Group> | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [groupsData, specsData] = await Promise.all([
        apiClient.get<Group[]>('/groups'),
        apiClient.get<Specialty[]>('/departments/specialties/all'),
      ]);
      setGroups(groupsData);
      setSpecialties(specsData);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const specialtyName = (id?: number) =>
    specialties.find(s => s.specialty_id === id)?.name || t.noData;

  const handleCreate = () => {
    setCurrentGroup({ name: '', course_no: 1, specialty_id: specialties[0]?.specialty_id, student_count: 25 });
    setError('');
    setIsModalOpen(true);
  };

  const handleEdit = (group: Group) => {
    setCurrentGroup(group);
    setError('');
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm(t.confirmDeleteGroup)) {
      try {
        await apiClient.delete(`/groups/${id}`);
        fetchData();
      } catch (err) {
        alert(err instanceof Error ? err.message : t.error);
      }
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentGroup?.name || !currentGroup?.specialty_id) {
      setError('Заполните все обязательные поля');
      return;
    }

    setSaving(true);
    setError('');
    try {
      const payload = {
        name: currentGroup.name,
        code: currentGroup.code || currentGroup.name,
        course_no: Number(currentGroup.course_no) || 1,
        specialty_id: Number(currentGroup.specialty_id),
        student_count: currentGroup.student_count ? Number(currentGroup.student_count) : null,
      };
      if (currentGroup.id) {
        await apiClient.put(`/groups/${currentGroup.id}`, payload);
      } else {
        await apiClient.post('/groups', payload);
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
    { key: 'name', header: t.groupName },
    { key: 'course_no', header: t.groupCourse, className: 'w-20' },
    {
      key: 'specialty_id',
      header: t.groupDepartment,
      render: (g: Group) => specialtyName(g.specialty_id),
    },
    { key: 'student_count', header: t.groupStudentCount, className: 'w-24 text-center' },
    {
      key: 'actions',
      header: t.actions,
      render: (g: Group) => (
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => handleEdit(g)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(g.id)}>
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
        <h1 className="text-2xl font-bold text-museum-text">{t.groupsTitle}</h1>
        <div className="flex gap-2">
          <CsvImportButton endpoint="/groups/import-csv" onSuccess={fetchData} />
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            {t.addGroup}
          </Button>
        </div>
      </div>

      <DataTable columns={columns} data={groups} loading={loading} />

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={currentGroup?.id ? t.editGroup : t.addGroup}
      >
        <form onSubmit={handleSave} className="space-y-4">
          {error && (
            <div className="text-sm text-museum-danger bg-museum-danger/10 border border-museum-danger/20 rounded p-3">
              {error}
            </div>
          )}
          <Input
            label={t.groupName}
            value={currentGroup?.name || ''}
            onChange={(e) => setCurrentGroup({ ...currentGroup, name: e.target.value })}
            placeholder="П-21-1"
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label={t.groupCourse}
              type="number"
              min="1"
              max="4"
              value={currentGroup?.course_no || 1}
              onChange={(e) => setCurrentGroup({ ...currentGroup, course_no: Number(e.target.value) })}
              required
            />
            <Input
              label={t.groupStudentCount}
              type="number"
              min="1"
              max="100"
              value={currentGroup?.student_count || 25}
              onChange={(e) => setCurrentGroup({ ...currentGroup, student_count: Number(e.target.value) })}
            />
          </div>
          <Select
            label={t.groupDepartment}
            value={currentGroup?.specialty_id || ''}
            onChange={(e) => setCurrentGroup({ ...currentGroup, specialty_id: Number(e.target.value) })}
            required
          >
            <option value="">{t.groupSelectDepartment}</option>
            {specialties.map((spec) => (
              <option key={spec.specialty_id} value={spec.specialty_id}>{spec.name}</option>
            ))}
          </Select>
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
