import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import { Calendar, MapPin, ArrowRight, User, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

interface StudentData {
  group_name: string;
  course: number;
  stats: {
    hours_per_week: number;
    lessons_per_week: number;
    subjects_count: number;
    days_count: number;
  };
}

export default function StudentDashboard() {
  const { user, logout } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const [data, setData] = useState<StudentData | null>(null);
  const [, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<StudentData>('/student/dashboard').then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const stats = [
    { label: t.hoursPerWeekLabel, value: data?.stats.hours_per_week ?? '—' },
    { label: t.lessonsPerWeekLabel, value: data?.stats.lessons_per_week ?? '—' },
    { label: t.subjectsLabel, value: data?.stats.subjects_count ?? '—' },
    { label: t.daysLabel, value: data?.stats.days_count ?? '—' },
  ];

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="bg-museum-surface border border-museum-border rounded-museum-md p-8 shadow-sm mb-8">
        <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-museum-accent rounded-full flex items-center justify-center">
               <User className="h-8 w-8 text-black" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-museum-text">{user?.full_name}</h1>
              <p className="text-museum-text-muted">
                {t.studentGroup}: <span className="text-museum-accent font-bold">{data?.group_name || '—'}</span> 
                • {data?.course} {t.studentCourse}
              </p>
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

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map(s => (
            <div key={s.label} className="bg-museum-bg p-4 rounded-museum-sm border border-museum-border">
              <p className="text-[10px] font-bold text-museum-text-muted uppercase tracking-wider mb-1">{s.label}</p>
              <p className="text-xl font-bold text-museum-text">{s.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link to="/my-schedule" className="group bg-museum-surface border border-museum-border p-6 rounded-museum-md hover:border-museum-accent transition-all shadow-sm">
           <div className="w-10 h-10 bg-museum-accent/10 rounded-museum-sm flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
             <Calendar className="h-5 w-5 text-museum-accent" />
           </div>
           <h3 className="font-bold text-museum-text mb-1 flex items-center gap-2">
             {t.myScheduleLink} <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
           </h3>
           <p className="text-sm text-museum-text-muted">{t.myScheduleDesc}</p>
        </Link>

        <Link to="/classrooms" className="group bg-museum-surface border border-museum-border p-6 rounded-museum-md hover:border-museum-accent transition-all shadow-sm">
           <div className="w-10 h-10 bg-blue-500/10 rounded-museum-sm flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
             <MapPin className="h-5 w-5 text-blue-500" />
           </div>
           <h3 className="font-bold text-museum-text mb-1 flex items-center gap-2">
             {t.freeClassroomsLink} <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
           </h3>
           <p className="text-sm text-museum-text-muted">{t.freeClassroomsDesc}</p>
        </Link>
      </div>
    </div>
  );
}
