import React, { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import Select from '../components/ui/Select';
import { Plus, Pencil, Trash2, Building2, GraduationCap } from 'lucide-react';

interface Department { id: number; name: string; code?: string; }
interface Specialty { specialty_id: number; department_id: number; code: string; name: string; }

export default function Departments() {
  const { t } = useLang();
  const [tab, setTab] = useState<'departments' | 'specialties'>('departments');

  // ── Departments ──────────────────────────────────────────
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loadingDepts, setLoadingDepts] = useState(true);
  const [deptModal, setDeptModal] = useState(false);
  const [currentDept, setCurrentDept] = useState<Partial<Department>>({});
  const [savingDept, setSavingDept] = useState(false);

  const fetchDepts = async () => {
    setLoadingDepts(true);
    try { setDepartments(await apiClient.get<Department[]>('/departments')); }
    finally { setLoadingDepts(false); }
  };
  useEffect(() => { fetchDepts(); }, []);

  const saveDept = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingDept(true);
    try {
      if (currentDept.id) {
        await apiClient.put(`/departments/${currentDept.id}`, { name: currentDept.name, code: currentDept.code || '' });
      } else {
        await apiClient.post('/departments', { name: currentDept.name, code: currentDept.code || '' });
      }
      setDeptModal(false);
      fetchDepts();
    } catch (err: any) { alert(err.message); }
    finally { setSavingDept(false); }
  };

  const deleteDept = async (id: number) => {
    if (!window.confirm('Удалить отделение?')) return;
    try { await apiClient.delete(`/departments/${id}`); fetchDepts(); }
    catch (err: any) { alert(err.message); }
  };

  const deptColumns = [
    { key: 'name', header: 'Название' },
    { key: 'code', header: 'Код', render: (d: Department) => <span className="font-mono text-xs">{d.code || '—'}</span> },
    {
      key: 'actions', header: t.actions, className: 'w-24 text-right',
      render: (d: Department) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => { setCurrentDept(d); setDeptModal(true); }}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => deleteDept(d.id)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  // ── Specialties ──────────────────────────────────────────
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [loadingSpecs, setLoadingSpecs] = useState(false);
  const [specModal, setSpecModal] = useState(false);
  const [currentSpec, setCurrentSpec] = useState<Partial<Specialty & { id?: number }>>({});
  const [savingSpec, setSavingSpec] = useState(false);

  const fetchSpecs = async () => {
    setLoadingSpecs(true);
    try { setSpecialties(await apiClient.get<Specialty[]>('/departments/specialties/all')); }
    finally { setLoadingSpecs(false); }
  };
  useEffect(() => { if (tab === 'specialties') fetchSpecs(); }, [tab]);

  const saveSpec = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentSpec.department_id) { alert('Выберите отделение'); return; }
    setSavingSpec(true);
    try {
      if (currentSpec.specialty_id) {
        await apiClient.put(`/departments/${currentSpec.department_id}/specialties/${currentSpec.specialty_id}`, {
          code: currentSpec.code, name: currentSpec.name,
        });
      } else {
        await apiClient.post(`/departments/${currentSpec.department_id}/specialties`, {
          code: currentSpec.code, name: currentSpec.name,
        });
      }
      setSpecModal(false);
      fetchSpecs();
    } catch (err: any) { alert(err.message); }
    finally { setSavingSpec(false); }
  };

  const deleteSpec = async (spec: Specialty) => {
    if (!window.confirm('Удалить специальность?')) return;
    try {
      await apiClient.delete(`/departments/${spec.department_id}/specialties/${spec.specialty_id}`);
      fetchSpecs();
    } catch (err: any) { alert(err.message); }
  };

  const deptMap = Object.fromEntries(departments.map(d => [d.id, d.name]));

  const specColumns = [
    { key: 'name', header: 'Специальность' },
    { key: 'code', header: 'Код', render: (s: Specialty) => <span className="font-mono text-xs">{s.code}</span> },
    { key: 'dept', header: 'Отделение', render: (s: Specialty) => deptMap[s.department_id] || '—' },
    {
      key: 'actions', header: t.actions, className: 'w-24 text-right',
      render: (s: Specialty) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => { setCurrentSpec(s); setSpecModal(true); }}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => deleteSpec(s)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      {/* Tabs */}
      <div className="border-b border-museum-border mb-6">
        <nav className="-mb-px flex space-x-8">
          {([
            { key: 'departments', label: 'Отделения', icon: Building2 },
            { key: 'specialties', label: 'Специальности', icon: GraduationCap },
          ] as const).map(item => (
            <button key={item.key} onClick={() => setTab(item.key)}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-bold text-sm transition-colors ${
                tab === item.key
                  ? 'border-museum-accent text-museum-accent'
                  : 'border-transparent text-museum-text-muted hover:text-museum-text hover:border-museum-border'
              }`}>
              <item.icon className="h-4 w-4" />{item.label}
            </button>
          ))}
        </nav>
      </div>

      {tab === 'departments' && (
        <>
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-xl font-bold text-museum-text">Отделения</h1>
            <Button onClick={() => { setCurrentDept({}); setDeptModal(true); }}>
              <Plus className="h-4 w-4 mr-2" /> Добавить
            </Button>
          </div>
          <DataTable columns={deptColumns} data={departments} loading={loadingDepts} />

          <Modal isOpen={deptModal} onClose={() => setDeptModal(false)}
            title={currentDept.id ? 'Редактировать отделение' : 'Новое отделение'}>
            <form onSubmit={saveDept} className="space-y-4">
              <Input label="Название" value={currentDept.name || ''} required
                onChange={e => setCurrentDept({ ...currentDept, name: e.target.value })} />
              <Input label="Код (необязательно)" value={currentDept.code || ''}
                onChange={e => setCurrentDept({ ...currentDept, code: e.target.value })} />
              <div className="flex justify-end gap-3 mt-6">
                <Button variant="secondary" type="button" onClick={() => setDeptModal(false)}>{t.cancel}</Button>
                <Button type="submit" loading={savingDept}>{t.save}</Button>
              </div>
            </form>
          </Modal>
        </>
      )}

      {tab === 'specialties' && (
        <>
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-xl font-bold text-museum-text">Специальности</h1>
            <Button onClick={() => { setCurrentSpec({ department_id: departments[0]?.id }); setSpecModal(true); }}>
              <Plus className="h-4 w-4 mr-2" /> Добавить
            </Button>
          </div>
          <DataTable columns={specColumns} data={specialties} loading={loadingSpecs} />

          <Modal isOpen={specModal} onClose={() => setSpecModal(false)}
            title={currentSpec.specialty_id ? 'Редактировать специальность' : 'Новая специальность'}>
            <form onSubmit={saveSpec} className="space-y-4">
              <Select label="Отделение" value={currentSpec.department_id || ''} required
                onChange={e => setCurrentSpec({ ...currentSpec, department_id: Number(e.target.value) })}>
                <option value="">Выберите отделение</option>
                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </Select>
              <Input label="Код (напр. 0301)" value={currentSpec.code || ''} required
                onChange={e => setCurrentSpec({ ...currentSpec, code: e.target.value })} />
              <Input label="Название специальности" value={currentSpec.name || ''} required
                onChange={e => setCurrentSpec({ ...currentSpec, name: e.target.value })} />
              <div className="flex justify-end gap-3 mt-6">
                <Button variant="secondary" type="button" onClick={() => setSpecModal(false)}>{t.cancel}</Button>
                <Button type="submit" loading={savingSpec}>{t.save}</Button>
              </div>
            </form>
          </Modal>
        </>
      )}
    </div>
  );
}
