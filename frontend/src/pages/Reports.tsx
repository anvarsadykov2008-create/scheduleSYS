import { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import { Users, Building2, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface TeacherWorkload {
  teacher_id: number;
  full_name: string;
  total_lessons: number;
  hours_per_week: number;
  unique_subjects: number;
  unique_groups: number;
}

interface ClassroomUtilization {
  classroom_id: number;
  name: string;
  room_type: string;
  used_slots: number;
  total_slots: number;
  utilization_percent: number;
}

export default function Reports() {
  const { t } = useLang();
  const [loading, setLoading] = useState(true);
  const [workload, setWorkload] = useState<TeacherWorkload[]>([]);
  const [classroomUsage, setClassroomUsage] = useState<ClassroomUtilization[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [wData, cData] = await Promise.all([
          apiClient.get<TeacherWorkload[]>('/reports/teacher-workload').catch(() => []),
          apiClient.get<ClassroomUtilization[]>('/reports/classroom-utilization').catch(() => []),
        ]);
        setWorkload(wData);
        setClassroomUsage(cData);
      } catch (error) {
        console.error('Failed to fetch reports:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const workloadColumns = [
    { key: 'full_name', header: t.teacher },
    { key: 'hours_per_week', header: t.hoursPerWeek, className: 'w-24 text-center' },
    { key: 'max_hours', header: t.maxHours, render: () => '36', className: 'w-24 text-center' },
    {
      key: 'utilization',
      header: t.utilization,
      render: (w: TeacherWorkload) => {
        const util = Math.round((w.hours_per_week / 36) * 100);
        return (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-museum-bg rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full ${util > 100 ? 'bg-museum-danger' : 'bg-museum-accent'}`}
                style={{ width: `${Math.min(util, 100)}%` }}
              />
            </div>
            <span className={`text-xs font-bold ${util > 100 ? 'text-museum-danger' : 'text-museum-text'}`}>
              {util}%
            </span>
          </div>
        );
      },
      className: 'w-48',
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-museum-text">{t.reportsTitle}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-museum-accent" />
            <h2 className="text-lg font-semibold text-museum-text">{t.teacherWorkload}</h2>
          </div>
          <DataTable columns={workloadColumns} data={workload} loading={loading} emptyMessage={t.noWorkloadData} />
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-museum-accent" />
            <h2 className="text-lg font-semibold text-museum-text">{t.classroomUtilization}</h2>
          </div>
          <DataTable 
            columns={[
              { key: 'name', header: t.classroom },
              { key: 'room_type', header: t.classroomType, className: 'hidden md:table-cell w-32' },
              { key: 'used_slots', header: t.slotsUsed, className: 'w-24 text-center' },
              { 
                key: 'utilization_percent', 
                header: t.utilization,
                render: (c: ClassroomUtilization) => (
                   <span className="font-bold">{c.utilization_percent}%</span>
                ),
                className: 'w-32 text-right'
              }
            ]} 
            data={classroomUsage} 
            loading={loading} 
            emptyMessage={t.noClassroomData} 
          />
        </section>
      </div>

      <section className="bg-museum-surface border border-museum-border rounded-museum-md p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-museum-text">{t.conflicts}</h2>
        </div>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <CheckCircle2 className="h-12 w-12 text-museum-success mb-3 opacity-20" />
          <p className="text-museum-text font-medium">{t.noConflicts}</p>
          <p className="text-sm text-museum-text-muted mt-1">{t.noConflictsHint}</p>
        </div>
      </section>
    </div>
  );
}
