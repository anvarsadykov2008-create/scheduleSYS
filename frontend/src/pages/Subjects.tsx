import React, { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import CsvImportButton from '../components/ui/CsvImportButton';
import { Plus, Pencil, Trash2 } from 'lucide-react';

interface Subject {
  id: number;
  name: string;
}

export default function Subjects() {
  const { t } = useLang();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentSubject, setCurrentSubject] = useState<Partial<Subject> | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchSubjects = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<Subject[]>('/subjects');
      setSubjects(data);
    } catch (error) {
      console.error('Failed to fetch subjects:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const handleCreate = () => {
    setCurrentSubject({ name: '' });
    setIsModalOpen(true);
  };

  const handleEdit = (subject: Subject) => {
    setCurrentSubject(subject);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm(t.confirmDeleteSubject)) {
      try {
        await apiClient.delete(`/subjects/${id}`);
        fetchSubjects();
      } catch (error) {
        console.error('Failed to delete subject:', error);
      }
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentSubject?.name) return;

    setSaving(true);
    try {
      const payload = {
        name: currentSubject.name,
      };
      if (currentSubject.id) {
        await apiClient.put(`/subjects/${currentSubject.id}`, payload);
      } else {
        await apiClient.post('/subjects', payload);
      }
      setIsModalOpen(false);
      fetchSubjects();
    } catch (error) {
      console.error('Failed to save subject:', error);
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    { key: 'name', header: t.subjectFullName },
    {
      key: 'actions',
      header: t.actions,
      render: (s: Subject) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => handleEdit(s)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(s.id)}>
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
        <h1 className="text-2xl font-bold text-museum-text">{t.subjectsTitle}</h1>
        <div className="flex gap-2">
          <CsvImportButton endpoint="/subjects/import-csv" onSuccess={fetchSubjects} />
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            {t.addSubject}
          </Button>
        </div>
      </div>

      <DataTable columns={columns} data={subjects} loading={loading} />

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={currentSubject?.id ? t.editSubject : t.addSubject}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label={t.subjectFullName}
            value={currentSubject?.name || ''}
            onChange={(e) => setCurrentSubject({ ...currentSubject, name: e.target.value })}
            placeholder={t.subjectNamePlaceholder}
            required
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
