import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import { Users, GraduationCap, Building2, BookOpen, CalendarDays, Plus, Calendar, Clock, Activity, ArrowRight } from 'lucide-react';
import Button from '../components/ui/Button';

interface Stats {
  groups: number;
  teachers: number;
  classrooms: number;
  subjects: number;
  schedule_versions: number;
  workload_entries: number;
}

interface Version {
  id: number;
  status: string;
  created_at: string;
  description: string | null;
}

export default function Dashboard() {
  const { t } = useLang();
  const [stats, setStats] = useState<Stats | null>(null);
  const [latestVersion, setLatestVersion] = useState<Version | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [statsData, versions] = await Promise.all([
          apiClient.get<{ groups_count: number; teachers_count: number; classrooms_count: number; subjects_count: number; workload_entries_count: number }>('/stats'),
          apiClient.get<Version[]>('/schedule/versions'),
        ]);
        setStats({
          groups: statsData.groups_count,
          teachers: statsData.teachers_count,
          classrooms: statsData.classrooms_count,
          subjects: statsData.subjects_count,
          schedule_versions: versions.length,
          workload_entries: statsData.workload_entries_count,
        });
        if (versions.length > 0) {
          setLatestVersion(versions[0]);
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const cards = [
    { label: t.dashboardGroups, value: stats?.groups ?? '—', icon: GraduationCap, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { label: t.dashboardTeachers, value: stats?.teachers ?? '—', icon: Users, color: 'text-green-500', bg: 'bg-green-500/10' },
    { label: t.dashboardClassrooms, value: stats?.classrooms ?? '—', icon: Building2, color: 'text-orange-500', bg: 'bg-orange-500/10' },
    { label: t.dashboardSubjects, value: stats?.subjects ?? '—', icon: BookOpen, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-museum-accent animate-pulse">
        <Clock className="w-8 h-8" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-museum-text">{t.dashboardTitle}</h1>
        <div className="text-sm text-museum-text-muted flex items-center gap-2">
          <Activity className="w-4 h-4 text-museum-success" />
          Система работает нормально
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="bg-museum-surface border border-museum-border rounded-museum-md p-5 transition-transform hover:-translate-y-1 hover:shadow-lg">
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2.5 rounded-xl ${c.bg}`}>
                 <c.icon className={`h-6 w-6 ${c.color}`} />
              </div>
            </div>
            <div className="text-3xl font-black text-museum-text mb-1">{c.value}</div>
            <div className="text-xs font-bold text-museum-text-muted uppercase tracking-wider">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Latest Schedule Status */}
        <div className="lg:col-span-2 bg-museum-surface border border-museum-border rounded-museum-md p-6">
          <h2 className="text-lg font-bold text-museum-text mb-4 flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-museum-accent" />
            Состояние расписания
          </h2>
          
          {latestVersion ? (
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between bg-museum-bg rounded-lg p-4 border border-museum-border">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-museum-text">Версия {latestVersion.id}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${
                    latestVersion.status === 'published' ? 'bg-museum-success/10 text-museum-success border border-museum-success/20' :
                    latestVersion.status === 'approved' ? 'bg-blue-100 text-blue-600 border border-blue-200' :
                    'bg-museum-surface text-museum-text-secondary border border-museum-border'
                  }`}>
                    {latestVersion.status === 'published' ? t.statusPublished :
                     latestVersion.status === 'approved' ? t.statusApproved :
                     latestVersion.status === 'archived' ? t.statusArchive : t.statusDraft}
                  </span>
                </div>
                <div className="text-xs text-museum-text-muted">
                  Создано: {new Date(latestVersion.created_at).toLocaleString()}
                </div>
                {latestVersion.description && (
                  <div className="text-sm text-museum-text mt-2 italic border-l-2 border-museum-accent/30 pl-2">
                    «{latestVersion.description}»
                  </div>
                )}
              </div>
              
              <Link to="/admin/schedule">
                <Button variant="secondary" className="whitespace-nowrap">
                  Перейти к расписанию <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          ) : (
            <div className="text-center py-8 bg-museum-bg rounded-lg border border-dashed border-museum-border">
              <p className="text-museum-text-muted text-sm mb-3">Расписание ещё не сгенерировано</p>
              <Link to="/admin/schedule">
                <Button>
                  <Calendar className="w-4 h-4 mr-2" />
                  Сгенерировать расписание
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-museum-surface border border-museum-border rounded-museum-md p-6">
          <h2 className="text-lg font-bold text-museum-text mb-4 text-center">Быстрые действия</h2>
          <div className="flex flex-col gap-3">
             <Link to="/admin/people?tab=teachers&action=add">
               <button className="w-full flex items-center justify-between p-3 bg-museum-bg hover:bg-museum-surface-hover border border-museum-border rounded-lg transition-colors group">
                 <span className="flex items-center gap-3 text-sm font-semibold text-museum-text">
                   <div className="p-1.5 bg-green-500/10 text-green-500 rounded-md group-hover:scale-110 transition-transform">
                     <Users className="w-4 h-4" />
                   </div>
                   Добавить преподавателя
                 </span>
                 <Plus className="w-4 h-4 text-museum-text-muted" />
               </button>
             </Link>
             
             <Link to="/admin/people?tab=groups&action=add">
               <button className="w-full flex items-center justify-between p-3 bg-museum-bg hover:bg-museum-surface-hover border border-museum-border rounded-lg transition-colors group">
                 <span className="flex items-center gap-3 text-sm font-semibold text-museum-text">
                   <div className="p-1.5 bg-blue-500/10 text-blue-500 rounded-md group-hover:scale-110 transition-transform">
                     <GraduationCap className="w-4 h-4" />
                   </div>
                   Добавить группу
                 </span>
                 <Plus className="w-4 h-4 text-museum-text-muted" />
               </button>
             </Link>

             <Link to="/admin/places?tab=classrooms&action=add">
               <button className="w-full flex items-center justify-between p-3 bg-museum-bg hover:bg-museum-surface-hover border border-museum-border rounded-lg transition-colors group">
                 <span className="flex items-center gap-3 text-sm font-semibold text-museum-text">
                   <div className="p-1.5 bg-orange-500/10 text-orange-500 rounded-md group-hover:scale-110 transition-transform">
                     <Building2 className="w-4 h-4" />
                   </div>
                   Внести аудиторию
                 </span>
                 <Plus className="w-4 h-4 text-museum-text-muted" />
               </button>
             </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
