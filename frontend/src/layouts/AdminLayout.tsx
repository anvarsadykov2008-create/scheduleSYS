import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LanguageContext';
import LanguageSwitcher from '../components/LanguageSwitcher';
import {
  LayoutDashboard, Users, Building2,
  Calendar, CalendarDays, BarChart3, Settings, LogOut, Menu,
  FileText, UserCog, BookOpenCheck, ListChecks, Clock4, Layers
} from 'lucide-react';

export default function AdminLayout() {
  const { user, logout, isAdmin } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/admin', label: t.home, icon: LayoutDashboard, end: true },
    { to: '/admin/departments', label: 'Отделения и специальности', icon: Layers },
    { to: '/admin/people', label: 'Группы и преподаватели', icon: Users },
    { to: '/admin/places', label: 'Аудитории и дисциплины', icon: Building2 },
    { to: '/admin/lesson-types', label: 'Виды занятий', icon: ListChecks },
    { to: '/admin/academic-periods', label: 'Учебные периоды', icon: Clock4 },
    { to: '/admin/semesters', label: t.semesters, icon: Calendar },
    { to: '/admin/hour-grid', label: 'Сетка часов', icon: BookOpenCheck },
    { to: '/admin/schedule', label: t.schedule, icon: CalendarDays },
    { to: '/admin/reports', label: t.reports, icon: BarChart3 },
    { to: '/admin/settings', label: t.settings, icon: Settings },
    ...(isAdmin ? [
      { to: '/admin/users', label: t.users, icon: UserCog },
      { to: '/admin/audit', label: t.auditLog, icon: FileText },
    ] : []),
  ];

  const sidebarContent = (
    <aside className="flex flex-col bg-museum-surface border-r border-museum-border h-full">
      {/* Logo */}
      <div className="p-4 border-b border-museum-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-museum-accent rounded-museum-sm flex items-center justify-center">
            <BookOpenCheck className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-museum-text">ScheduleSYS</p>
            <p className="text-xs text-museum-text-muted">{t.adminPanel}</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded-museum-sm text-sm transition-colors ${
                isActive
                  ? 'bg-museum-accent text-white font-semibold'
                  : 'text-museum-text-secondary hover:bg-museum-surface-hover hover:text-museum-text'
              }`
            }
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="p-3 border-t border-museum-border">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-museum-accent/10 rounded-museum-sm flex items-center justify-center">
            <span className="text-museum-accent font-bold text-xs">
              {user?.full_name?.[0] ?? user?.username?.[0] ?? '?'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-museum-text truncate">{user?.full_name ?? user?.username}</p>
            <p className="text-xs text-museum-text-muted truncate">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-museum-text-secondary hover:text-museum-danger hover:bg-museum-danger-soft rounded-museum-sm transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          {t.logout}
        </button>
      </div>
    </aside>
  );

  return (
    <div className="flex h-screen bg-museum-bg overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden md:flex md:w-56 flex-shrink-0 flex-col">
        {sidebarContent}
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setSidebarOpen(false)} />
          <div className="absolute left-0 top-0 bottom-0 w-56 z-50">
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar (mobile) */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-museum-surface border-b border-museum-border">
          <button onClick={() => setSidebarOpen(true)}>
            <Menu className="h-5 w-5 text-museum-text" />
          </button>
          <span className="font-semibold text-museum-text text-sm">ScheduleSYS</span>
          <LanguageSwitcher />
        </header>

        {/* Desktop top bar */}
        <header className="hidden md:flex items-center justify-end gap-3 px-6 py-3 bg-museum-surface border-b border-museum-border">
          <LanguageSwitcher />
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
