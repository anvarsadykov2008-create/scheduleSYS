import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LanguageContext';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { Calendar, Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const { t } = useLang();
  const { login } = useAuth();
  const navigate = useNavigate();

  const [iin, setIin] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(iin.trim(), password);
      // redirect based on role will happen in App
      navigate('/');
    } catch (err: any) {
      setError(err.message || t.loginError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-museum-bg flex flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 bg-museum-surface border-b border-museum-border">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-museum-accent rounded-museum-sm flex items-center justify-center">
            <Calendar className="h-4 w-4 text-black" />
          </div>
          <span className="font-bold text-museum-text">ScheduleSYS</span>
        </Link>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <Link to="/" className="text-sm text-museum-text-secondary hover:text-museum-accent transition-colors">
            {t.viewSchedule}
          </Link>
        </div>
      </header>

      {/* Login form */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm bg-museum-surface border border-museum-border rounded-museum-md shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-museum-accent rounded-museum-md flex items-center justify-center mx-auto mb-4">
              <Calendar className="h-7 w-7 text-black" />
            </div>
            <h1 className="text-xl font-bold text-museum-text">{t.loginTitle}</h1>
            <p className="text-sm text-museum-text-muted mt-1">{t.loginSubtitle}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">
                {t.loginIIN}
              </label>
              <input
                type="text"
                value={iin}
                onChange={(e) => setIin(e.target.value)}
                placeholder={t.loginIINPlaceholder}
                maxLength={12}
                required
                className="w-full px-3 py-2.5 bg-museum-bg border border-museum-border rounded-museum-sm text-museum-text placeholder-museum-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">
                {t.loginPassword}
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t.loginPasswordPlaceholder}
                  required
                  className="w-full px-3 py-2.5 pr-10 bg-museum-bg border border-museum-border rounded-museum-sm text-museum-text placeholder-museum-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-museum-text-muted hover:text-museum-text"
                >
                  {showPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="px-3 py-2 bg-museum-danger-soft border border-museum-danger/20 rounded-museum-sm text-museum-danger text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-museum-accent hover:bg-museum-accent-hover text-white font-semibold rounded-museum-sm transition-colors disabled:opacity-50 uppercase tracking-wide text-sm"
            >
              {loading ? t.loginLoading : t.loginButton}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-museum-text-muted">
            {t.registerNoAccount}{' '}
            <Link to="/register" className="text-museum-accent hover:underline font-semibold">
              {t.registerLink}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
