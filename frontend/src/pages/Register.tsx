import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { Calendar } from 'lucide-react';

interface Group { id: number; name: string; course: number; }

export default function Register() {
  const { t } = useLang();
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[]>([]);
  const [form, setForm] = useState({ iin: '', full_name: '', password: '', group_id: '', role: 'STUDENT' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    apiClient.get<Group[]>('/groups').then(setGroups).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await apiClient.post<{ password: string }>('/auth/register', {
        iin: form.iin,
        full_name: form.full_name,
        password: form.password || null,
        group_id: form.group_id ? Number(form.group_id) : null,
        role: form.role,
      });
      setSuccess(res.password);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.error;
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-museum-bg flex items-center justify-center p-6">
        <div className="bg-museum-surface border border-museum-border rounded-museum-md p-8 max-w-sm w-full text-center">
          <div className="w-12 h-12 bg-museum-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-museum-success text-2xl">✓</span>
          </div>
          <h2 className="text-lg font-bold text-museum-text mb-2">{t.registerSuccess}</h2>
          <div className="bg-museum-accent/10 border border-museum-accent/20 rounded-museum-sm px-4 py-3 mb-4">
            <code className="text-museum-accent font-bold text-lg">{success}</code>
          </div>
          <p className="text-sm text-museum-text-muted mb-6">{t.registerSavePassword}</p>
          <button
            onClick={() => navigate('/login')}
            className="w-full py-2.5 bg-museum-accent text-white font-semibold rounded-museum-sm uppercase tracking-wide text-sm"
          >
            {t.registerGoToLogin}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-museum-bg flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 bg-museum-surface border-b border-museum-border">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-museum-accent rounded-museum-sm flex items-center justify-center">
            <Calendar className="h-4 w-4 text-black" />
          </div>
          <span className="font-bold text-museum-text">ScheduleSYS</span>
        </Link>
        <LanguageSwitcher />
      </header>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm bg-museum-surface border border-museum-border rounded-museum-md shadow-lg p-8">
          <h1 className="text-xl font-bold text-museum-text mb-6 text-center">{t.registerTitle}</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">{t.registerIIN}</label>
              <input
                type="text" value={form.iin} onChange={(e) => setForm({ ...form, iin: e.target.value })}
                maxLength={12} required
                className="w-full px-3 py-2.5 bg-museum-bg border border-museum-border rounded-museum-sm text-museum-text text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">{t.registerFullName}</label>
              <input
                type="text" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                required
                className="w-full px-3 py-2.5 bg-museum-bg border border-museum-border rounded-museum-sm text-museum-text text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">{t.loginPassword}</label>
              <input
                type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Минимум 6 символов (необязательно)"
                className="w-full px-3 py-2.5 bg-museum-bg border border-museum-border rounded-museum-sm text-museum-text text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">{t.userRole}</label>
              <select
                value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full px-3 py-2.5 bg-museum-bg border border-museum-border rounded-museum-sm text-museum-text text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors"
              >
                <option value="STUDENT">{t.roleStudent}</option>
                <option value="TEACHER">{t.roleTeacher}</option>
              </select>
            </div>
            {form.role === 'STUDENT' && (
              <div>
                <label className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">{t.registerGroup}</label>
                <select
                  value={form.group_id} onChange={(e) => setForm({ ...form, group_id: e.target.value })}
                  className="w-full px-3 py-2.5 bg-museum-bg border border-museum-border rounded-museum-sm text-museum-text text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors"
                >
                  <option value="">{t.registerSelectGroup}</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>{g.name} ({g.course} курс)</option>
                  ))}
                </select>
              </div>
            )}
            {error && (
              <div className="px-3 py-2 bg-museum-danger-soft border border-museum-danger/20 rounded-museum-sm text-museum-danger text-sm">{error}</div>
            )}
            <button
              type="submit" disabled={loading}
              className="w-full py-3 bg-museum-accent text-white font-semibold rounded-museum-sm hover:bg-museum-accent-hover transition-all active:scale-[0.98] disabled:opacity-50 uppercase tracking-wide text-sm"
            >
              {loading ? t.registerLoading : t.registerButton}
            </button>
          </form>
          <div className="mt-4 text-center text-sm text-museum-text-muted">
            {t.registerHaveAccount}{' '}
            <Link to="/login" className="text-museum-accent hover:underline font-semibold">{t.loginButton}</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
