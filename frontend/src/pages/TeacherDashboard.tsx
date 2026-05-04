import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import { Calendar, User, BookOpen, GraduationCap, Clock, LogOut, ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

interface TeacherStats {
  hours_per_week: number;
  total_lessons: number;
  subjects_count: number;
  groups_count: number;
}

interface TeacherWorkload {
  subject_name: string;
  group_name: string;
}

export default function TeacherDashboard() {
  const { user, logout } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const [stats, setStats] = useState<TeacherStats | null>(null);
  const [workload, setWorkload] = useState<TeacherWorkload[]>([]);
  const [, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const [s, w] = await Promise.all([
          apiClient.get<TeacherStats>('/teacher/stats'),
          apiClient.get<TeacherWorkload[]>('/teacher/workload')
        ]);
        setStats(s);
        setWorkload(w);
      } catch {
        // Fallback or empty
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const statCards = [
    { label: t.hoursPerWeekStat, value: stats?.hours_per_week ?? '—', icon: Clock, color: 'text-orange-500' },
    { label: t.totalLessons, value: stats?.total_lessons ?? '—', icon: Calendar, color: 'text-blue-500' },
    { label: t.subjectsStat, value: stats?.subjects_count ?? '—', icon: BookOpen, color: 'text-purple-500' },
    { label: t.groupsStat, value: stats?.groups_count ?? '—', icon: GraduationCap, color: 'text-green-500' },
  ];

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="bg-museum-surface border border-museum-border rounded-museum-md p-8 shadow-sm mb-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-museum-accent rounded-full flex items-center justify-center">
               <User className="h-8 w-8 text-black" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-museum-text">{user?.full_name}</h1>
              <p className="text-museum-text-muted uppercase text-xs font-bold tracking-widest mt-1">{t.roleTeacher}</p>
            </div>
          </div>
          
          <button 
            onClick={handleLogout} 
            className="flex items-center gap-2 px-4 py-2 border border-museum-border hover:border-museum-danger hover:text-museum-danger rounded-museum-sm text-sm text-museum-text-secondary transition-colors"
          >
            <LogOut className="h-4 w-4" />
            {t.logout}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map(s => (
          <div key={s.label} className="bg-museum-surface border border-museum-border p-5 rounded-museum-md shadow-sm">
             <s.icon className={`h-5 w-5 ${s.color} mb-3`} />
             <p className="text-[10px] font-bold text-museum-text-muted uppercase tracking-wider mb-1">{s.label}</p>
             <p className="text-xl font-bold text-museum-text">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <Link
          to="/teacher-schedule"
          className="group flex items-center justify-between bg-museum-surface border border-museum-border p-5 rounded-museum-md hover:border-museum-accent transition-all shadow-sm"
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-museum-accent/10 rounded-museum-sm flex items-center justify-center group-hover:scale-110 transition-transform">
              <Calendar className="h-5 w-5 text-museum-accent" />
            </div>
            <div>
              <p className="font-bold text-museum-text">{t.mySchedule}</p>
              <p className="text-xs text-museum-text-muted mt-0.5">{t.myScheduleDesc}</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-museum-text-muted group-hover:text-museum-accent transition-colors" />
        </Link>
        <Link
          to="/"
          className="group flex items-center justify-between bg-museum-surface border border-museum-border p-5 rounded-museum-md hover:border-museum-accent transition-all shadow-sm"
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-blue-500/10 rounded-museum-sm flex items-center justify-center group-hover:scale-110 transition-transform">
              <GraduationCap className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="font-bold text-museum-text">Общее расписание</p>
              <p className="text-xs text-museum-text-muted mt-0.5">Расписание всех групп по семестрам</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-museum-text-muted group-hover:text-museum-accent transition-colors" />
        </Link>
      </div>

      <div className="bg-museum-surface border border-museum-border rounded-museum-md p-6 shadow-sm">
        <h2 className="text-lg font-bold text-museum-text mb-4">{t.myWorkload}</h2>
        {workload.length === 0 ? (
          <p className="text-sm text-museum-text-muted py-4">{t.noWorkloadInfo}</p>
        ) : (
          <div className="divide-y divide-museum-border/40">
            {workload.map((w, i) => (
              <div key={i} className="py-3 flex items-center justify-between group">
                <div>
                  <p className="text-sm font-bold text-museum-text">{w.subject_name}</p>
                  <p className="text-xs text-museum-text-muted">{t.groups}: {w.group_name}</p>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                   <div className="w-2 h-2 bg-museum-accent rounded-full" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
