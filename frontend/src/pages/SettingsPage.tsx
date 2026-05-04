import { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { Save, AlertCircle, RefreshCcw, SlidersHorizontal, Calendar, Clock, Lock } from 'lucide-react';

interface Setting {
  key: string;
  value: string;
  description: string;
}

// Icons and labels for each known setting key
const SETTING_META: Record<string, { icon: React.ReactNode; labelKey: string; hintKey?: string }> = {
  max_daily_lessons: {
    icon: <SlidersHorizontal className="h-5 w-5" />,
    labelKey: 'settingsMaxDailyLessons',
    hintKey: 'settingsMaxDailyLessonsHint',
  },
  min_teacher_gap: {
    icon: <Clock className="h-5 w-5" />,
    labelKey: 'settingsMinTeacherGap',
    hintKey: 'settingsMinTeacherGapHint',
  },
  semester_start: {
    icon: <Calendar className="h-5 w-5" />,
    labelKey: 'settingsSemesterStart',
    hintKey: 'settingsSemesterStartHint',
  },
  semester_end: {
    icon: <Calendar className="h-5 w-5" />,
    labelKey: 'settingsSemesterEnd',
    hintKey: 'settingsSemesterEndHint',
  },
};

export default function SettingsPage() {
  const { t } = useLang();
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);

  // Password change state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');
    
    if (newPassword !== confirmPassword) {
      setPasswordError('Пароли не совпадают');
      return;
    }
    
    if (newPassword.length < 6) {
      setPasswordError('Пароль должен быть не менее 6 символов');
      return;
    }

    setPasswordSaving(true);
    try {
      await apiClient.post('/users/me/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
      setPasswordSuccess('Пароль успешно изменен');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || 'Ошибка при смене пароля');
    } finally {
      setPasswordSaving(false);
    }
  };

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<Setting[]>('/settings');
      setSettings(data);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSaved(false);
    try {
      await Promise.all(
        settings.map(s => apiClient.post(`/settings/${s.key}`, { value: s.value }))
      );
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setError(t.settingsErrorSave);
    } finally {
      setSaving(false);
    }
  };

  const updateValue = (key: string, value: string) => {
    setSettings(settings.map(s => (s.key === key ? { ...s, value } : s)));
  };

  if (loading) return (
    <div className="flex justify-center items-center p-20">
      <RefreshCcw className="animate-spin text-museum-accent h-8 w-8" />
    </div>
  );

  return (
    <div className="max-w-2xl">
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-2xl font-bold text-museum-text">{t.settingsTitle}</h1>
          <p className="text-sm text-museum-text-muted mt-1">{t.settingsSubtitle}</p>
        </div>
        <Button onClick={handleSave} loading={saving}>
          <Save className="h-4 w-4 mr-2" />
          {t.save}
        </Button>
      </div>

      {/* Success banner */}
      {saved && (
        <div className="mb-6 p-4 bg-museum-success-soft border border-museum-success/30 rounded-museum-md flex items-center gap-3 text-museum-success">
          <Save className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm font-semibold">{t.settingsSaveSuccess}</span>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-4 bg-museum-danger-soft border border-museum-danger/20 rounded-museum-md flex items-center gap-3 text-museum-danger">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm font-semibold">{error}</span>
        </div>
      )}

      {/* System Settings Section */}
      <div className="space-y-4 mb-12">
        {settings.map((s) => {
          const meta = SETTING_META[s.key];
          const label = meta ? t[meta.labelKey as keyof typeof t] as string : s.description || s.key;
          const hint = meta?.hintKey ? t[meta.hintKey as keyof typeof t] as string : undefined;
          const icon = meta?.icon;

          return (
            <div
              key={s.key}
              className="bg-museum-surface border border-museum-border rounded-museum-md p-5 transition-shadow hover:shadow-sm"
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                {icon && (
                  <div className="flex-shrink-0 w-10 h-10 rounded-museum-sm bg-museum-accent-soft text-museum-accent flex items-center justify-center mt-0.5">
                    {icon}
                  </div>
                )}

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <label className="block text-[14px] font-bold text-museum-text mb-0.5">
                    {label}
                  </label>
                  {hint && (
                    <p className="text-[12px] text-museum-text-muted mb-3 leading-relaxed">{hint}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2">
                    <Input
                      value={s.value}
                      onChange={(e) => updateValue(s.key, e.target.value)}
                      className="flex-1"
                    />
                    <code className="text-[11px] font-mono text-museum-text-muted bg-museum-bg border border-museum-border px-2 py-1 rounded-md whitespace-nowrap">
                      {s.key}
                    </code>
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {settings.length === 0 && (
          <div className="text-center py-12 text-museum-text-muted bg-museum-surface border border-museum-border rounded-museum-md">
            {t.settingsNotFound}
          </div>
        )}
      </div>

      <hr className="border-museum-border mb-10" />

      {/* Password Change Section */}
      <div className="bg-museum-surface border border-museum-border rounded-museum-md p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-museum-accent/10 rounded-full flex items-center justify-center">
            <Lock className="h-5 w-5 text-museum-accent" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-museum-text">Смена пароля</h2>
            <p className="text-sm text-museum-text-muted">Обновите свой пароль для безопасности</p>
          </div>
        </div>

        <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
          <Input
            label="Текущий пароль"
            type="password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            required
          />
          <Input
            label="Новый пароль"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <Input
            label="Подтвердите новый пароль"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          {passwordError && (
            <div className="flex items-center gap-2 text-museum-danger text-sm bg-museum-danger/10 p-3 rounded-museum-sm">
              <AlertCircle className="h-4 w-4" />
              {passwordError}
            </div>
          )}

          {passwordSuccess && (
            <div className="text-museum-success text-sm bg-museum-success/10 p-3 rounded-museum-sm">
              {passwordSuccess}
            </div>
          )}

          <div className="pt-2">
            <Button type="submit" loading={passwordSaving}>
              Обновить пароль
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
