import React, { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import Select from '../components/ui/Select';
import { Plus, Pencil, Trash2, CalendarPlus } from 'lucide-react';

interface AcademicYear {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
}

interface Semester {
  id: number;
  number: number;
  start_date: string;
  end_date: string;
  academic_year_id: number;
  academic_year?: AcademicYear;
}

export default function Semesters() {
  const { t } = useLang();
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isYearModalOpen, setIsYearModalOpen] = useState(false);
  const [currentYear, setCurrentYear] = useState<Partial<AcademicYear>>({ name: '', start_date: '', end_date: '' });
  
  const [isSemModalOpen, setIsSemModalOpen] = useState(false);
  const [currentSem, setCurrentSem] = useState<Partial<Semester>>({ number: 1, start_date: '', end_date: '', academic_year_id: 0 });
  
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [semsData, yearsData] = await Promise.all([
        apiClient.get<Semester[]>('/semesters'),
        apiClient.get<AcademicYear[]>('/academic_years'),
      ]);
      setSemesters(semsData);
      setAcademicYears(yearsData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateYear = () => {
    setCurrentYear({ name: '', start_date: '', end_date: '' });
    setIsYearModalOpen(true);
  };

  const handleSaveYear = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiClient.post('/academic_years', currentYear);
      setIsYearModalOpen(false);
      fetchData();
    } catch (error) {
      console.error('Failed to save year:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateSem = () => {
    setCurrentSem({
      number: 1,
      start_date: '',
      end_date: '',
      academic_year_id: academicYears[0]?.id || 0
    });
    setIsSemModalOpen(true);
  };

  const handleEditSem = (sem: Semester) => {
    setCurrentSem(sem);
    setIsSemModalOpen(true);
  };

  const handleSaveSem = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        number: Number(currentSem.number),
        start_date: currentSem.start_date,
        end_date: currentSem.end_date,
        academic_year_id: Number(currentSem.academic_year_id),
      };
      if (currentSem.id) {
        await apiClient.put(`/semesters/${currentSem.id}`, payload);
      } else {
        await apiClient.post('/semesters', payload);
      }
      setIsSemModalOpen(false);
      fetchData();
    } catch (error) {
      console.error('Failed to save semester:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSem = async (id: number) => {
    if (window.confirm(t.confirmDeleteSemester)) {
      try {
        await apiClient.delete(`/semesters/${id}`);
        fetchData();
      } catch (error) {
        console.error('Failed to delete semester:', error);
      }
    }
  };

  const columns = [
    {
      key: 'academic_year',
      header: t.academicYear,
      render: (s: Semester) => s.academic_year?.name || t.noData,
    },
    { key: 'number', header: t.semesterNumber, className: 'w-32' },
    { key: 'start_date', header: t.startDate, className: 'w-40' },
    { key: 'end_date', header: t.endDate, className: 'w-40' },
    {
      key: 'actions',
      header: t.actions,
      render: (s: Semester) => (
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => handleEditSem(s)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDeleteSem(s.id)}>
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
        <h1 className="text-2xl font-bold text-museum-text">{t.semestersTitle}</h1>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleCreateYear}>
            <CalendarPlus className="h-4 w-4 mr-2" />
            {t.createAcademicYear}
          </Button>
          <Button onClick={handleCreateSem}>
            <Plus className="h-4 w-4 mr-2" />
            {t.addSemester}
          </Button>
        </div>
      </div>

      <DataTable columns={columns} data={semesters} loading={loading} />

      {/* Year Modal */}
      <Modal isOpen={isYearModalOpen} onClose={() => setIsYearModalOpen(false)} title={t.manageAcademicYears}>
        <form onSubmit={handleSaveYear} className="space-y-4">
          <Input
            label={t.academicYear}
            value={currentYear.name || ''}
            onChange={(e) => setCurrentYear({ ...currentYear, name: e.target.value })}
            placeholder="2025-2026"
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label={t.startDate}
              type="date"
              value={currentYear.start_date || ''}
              onChange={(e) => setCurrentYear({ ...currentYear, start_date: e.target.value })}
              required
            />
            <Input
              label={t.endDate}
              type="date"
              value={currentYear.end_date || ''}
              onChange={(e) => setCurrentYear({ ...currentYear, end_date: e.target.value })}
              required
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" onClick={() => setIsYearModalOpen(false)}>{t.cancel}</Button>
            <Button type="submit" loading={saving}>{t.save}</Button>
          </div>
        </form>
      </Modal>

      {/* Semester Modal */}
      <Modal isOpen={isSemModalOpen} onClose={() => setIsSemModalOpen(false)} title={currentSem.id ? t.editSemester : t.addSemester}>
        <form onSubmit={handleSaveSem} className="space-y-4">
          <Select
            label={t.academicYear}
            value={currentSem.academic_year_id || ''}
            onChange={(e) => setCurrentSem({ ...currentSem, academic_year_id: Number(e.target.value) })}
            required
          >
            <option value="">{t.noData}</option>
            {academicYears.map(y => <option key={y.id} value={y.id}>{y.name}</option>)}
          </Select>
          <Select
            label={t.semesterNumber}
            value={currentSem.number || 1}
            onChange={(e) => setCurrentSem({ ...currentSem, number: Number(e.target.value) })}
            required
          >
            <option value={1}>{t.semester1}</option>
            <option value={2}>{t.semester2}</option>
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label={t.startDate}
              type="date"
              value={currentSem.start_date || ''}
              onChange={(e) => setCurrentSem({ ...currentSem, start_date: e.target.value })}
              required
            />
            <Input
              label={t.endDate}
              type="date"
              value={currentSem.end_date || ''}
              onChange={(e) => setCurrentSem({ ...currentSem, end_date: e.target.value })}
              required
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" onClick={() => setIsSemModalOpen(false)}>{t.cancel}</Button>
            <Button type="submit" loading={saving}>{t.save}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
