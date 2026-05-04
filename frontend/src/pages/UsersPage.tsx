import React, { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import Select from '../components/ui/Select';
import { Plus, Pencil, Trash2 } from 'lucide-react';

interface User {
  id: number;
  username: string;
  role: string;
  full_name: string | null;
  teacher_id: number | null;
  group_id: number | null;
  is_not_student: boolean;
}

interface Teacher { id: number; full_name: string; }
interface Group { id: number; name: string; }

export default function UsersPage() {
  const { t } = useLang();
  const [users, setUsers] = useState<User[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<Partial<User> | null>(null);
  const [password, setPassword] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [uData, tData, gData] = await Promise.all([
        apiClient.get<User[]>('/users'),
        apiClient.get<Teacher[]>('/teachers'),
        apiClient.get<Group[]>('/groups'),
      ]);
      setUsers(uData);
      setTeachers(tData);
      setGroups(gData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = () => {
    setCurrentUser({ username: '', role: 'студент', full_name: '', is_not_student: false });
    setPassword('');
    setIsModalOpen(true);
  };

  const handleEdit = (user: User) => {
    setCurrentUser(user);
    setPassword('');
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm(t.confirmDeleteUser)) {
      try {
        await apiClient.delete(`/users/${id}`);
        fetchData();
      } catch (error) {
        console.error('Failed to delete user:', error);
      }
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser?.username) return;

    setSaving(true);
    try {
      const payload = {
        username: currentUser.username,
        role: currentUser.role,
        full_name: currentUser.full_name || null,
        teacher_id: currentUser.teacher_id ? Number(currentUser.teacher_id) : null,
        group_id: currentUser.group_id ? Number(currentUser.group_id) : null,
        is_not_student: currentUser.is_not_student || false,
        ...(password ? { password } : {}),
      };

      if (currentUser.id) {
        await apiClient.put(`/users/${currentUser.id}`, payload);
      } else {
        await apiClient.post('/users', payload);
      }
      setIsModalOpen(false);
      fetchData();
    } catch (error) {
      console.error('Failed to save user:', error);
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    { key: 'username', header: t.userIIN, className: 'w-32' },
    { key: 'full_name', header: t.userFullName },
    {
      key: 'role',
      header: t.userRole,
      render: (u: User) => {
        const roles: Record<string, string> = {
          'администратор': t.roleAdmin,
          'диспетчер': t.roleDispatcher,
          'преподаватель': t.roleTeacher,
          'студент': t.roleStudent,
          'администрация': t.roleManagement,
        };
        return roles[u.role] || u.role;
      },
      className: 'w-32',
    },
    {
      key: 'linked',
      header: 'Привязка',
      render: (u: User) => {
        if (u.teacher_id) return `${t.userTeacher}: ${teachers.find(t_ => t_.id === u.teacher_id)?.full_name || '?'}`;
        if (u.group_id) return `${t.userGroup}: ${groups.find(g => g.id === u.group_id)?.name || '?'}`;
        return t.userNotLinked;
      }
    },
    {
      key: 'actions',
      header: t.actions,
      render: (u: User) => (
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => handleEdit(u)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-museum-danger" onClick={() => handleDelete(u.id)}>
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
        <h1 className="text-2xl font-bold text-museum-text">{t.usersTitle}</h1>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          {t.add}
        </Button>
      </div>

      <DataTable columns={columns} data={users} loading={loading} />

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={currentUser?.id ? t.editUser : t.createUser}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label={t.userIIN}
            value={currentUser?.username || ''}
            onChange={(e) => setCurrentUser({ ...currentUser, username: e.target.value })}
            required
            maxLength={12}
          />
          <Input
            label={t.userFullName}
            value={currentUser?.full_name || ''}
            onChange={(e) => setCurrentUser({ ...currentUser, full_name: e.target.value })}
            placeholder="Иванов Иван Иванович"
          />
          <Input
            label={currentUser?.id ? t.userNewPassword : t.userPassword}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required={!currentUser?.id}
          />
          <Select
            label={t.userRole}
            value={currentUser?.role || 'STUDENT'}
            onChange={(e) => {
              const role = e.target.value;
              setCurrentUser({ ...currentUser, role, is_not_student: role !== 'STUDENT' });
            }}
            required
          >
            <option value="ADMIN">{t.roleAdmin}</option>
            <option value="DISPATCHER">{t.roleDispatcher}</option>
            <option value="TEACHER">{t.roleTeacher}</option>
            <option value="STUDENT">{t.roleStudent}</option>
            <option value="MANAGEMENT">{t.roleManagement}</option>
          </Select>

          {(currentUser?.role === 'TEACHER' || currentUser?.role === 'преподаватель') && (
            <Select
              label={t.userTeacher}
              value={currentUser?.teacher_id || ''}
              onChange={(e) => setCurrentUser({ ...currentUser, teacher_id: e.target.value ? Number(e.target.value) : null })}
            >
              <option value="">{t.userNotLinked}</option>
              {teachers.map(tr => <option key={tr.id} value={tr.id}>{tr.full_name}</option>)}
            </Select>
          )}

          {(currentUser?.role === 'STUDENT' || currentUser?.role === 'студент') && (
            <Select
              label={t.userGroup}
              value={currentUser?.group_id || ''}
              onChange={(e) => setCurrentUser({ ...currentUser, group_id: e.target.value ? Number(e.target.value) : null })}
            >
              <option value="">{t.userNotLinked}</option>
              {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
            </Select>
          )}

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>{t.cancel}</Button>
            <Button type="submit" loading={saving}>{t.save}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
