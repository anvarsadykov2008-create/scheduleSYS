import { Outlet, Link } from 'react-router-dom';
import { useLang } from '../context/LanguageContext';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { BookOpenCheck, LogIn, Building2, UserCircle } from 'lucide-react';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';

export default function PublicLayout() {
  const { t } = useLang();
  const { user } = useAuth();

  const getProfileLink = () => {
    if (!user) return '/login';
    if (user.role === 'STUDENT') return '/student';
    if (user.role === 'TEACHER') return '/my-schedule';
    return '/admin';
  };

  return (
    <div className="min-h-screen bg-museum-bg flex flex-col">
      {/* Header */}
      <header className="bg-museum-surface border-b border-museum-border sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-museum-accent rounded-museum-sm flex items-center justify-center transition-transform group-hover:scale-105">
              <BookOpenCheck className="h-6 w-6 text-white" />
            </div>
            <div className="hidden sm:block">
              <p className="text-lg font-bold text-museum-text leading-none">ScheduleSYS</p>
              <p className="text-[10px] text-museum-text-muted font-bold uppercase tracking-widest mt-0.5">
                {t.publicScheduleCollege}
              </p>
            </div>
          </Link>

          {/* Navigation & Actions */}
          <div className="flex items-center gap-4">
            <nav className="hidden md:flex items-center gap-2 mr-2">
              <Link to="/classrooms">
                <Button variant="ghost" size="sm" className="hidden lg:flex">
                  <Building2 className="h-4 w-4" />
                  {t.freeClassrooms}
                </Button>
                <Button variant="ghost" size="sm" className="lg:hidden">
                  <Building2 className="h-4 w-4" />
                </Button>
              </Link>
            </nav>
            
            <LanguageSwitcher />

            <Link to={getProfileLink()}>
              <Button variant="primary" size="sm" className="gap-2">
                {user ? <UserCircle className="h-4 w-4" /> : <LogIn className="h-4 w-4" />}
                <span className="hidden sm:inline">{user ? t.personalAccount : t.loginButton}</span>
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer (Optional, but makes it look premium) */}
      <footer className="bg-museum-surface border-t border-museum-border py-8 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-sm text-museum-text-muted">
            &copy; {new Date().getFullYear()} ScheduleSYS. {t.publicScheduleSubtitle}
          </p>
        </div>
      </footer>
    </div>
  );
}
