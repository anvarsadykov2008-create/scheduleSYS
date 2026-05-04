import { useState, useEffect, useCallback } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import Select from '../components/ui/Select';
import { MapPin, Clock, Info, Users } from 'lucide-react';

interface Semester { id: number; number: number; academic_year?: { name: string } }
interface Group { id: number; name: string }
interface ScheduleEntry {
  id: number;
  day_of_week: number;
  time_slot_number: number;
  start_time: string;
  end_time: string;
  subject_name: string;
  teacher_name: string;
  classroom_name: string;
  week_type: string;
}
interface ScheduleVersion { id: number; status: string }

export default function PublicSchedule() {
  const { t } = useLang();
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedSem, setSelectedSem] = useState<number | ''>('');
  const [selectedGroup, setSelectedGroup] = useState<number | ''>('');
  const [schedule, setSchedule] = useState<ScheduleEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiClient.get<Semester[]>('/semesters').then(setSemesters).catch(() => {});
    apiClient.get<Group[]>('/groups').then(setGroups).catch(() => {});
  }, []);

  const fetchSchedule = useCallback(async () => {
    if (!selectedSem || !selectedGroup) return;
    setLoading(true);
    try {
      const versions = await apiClient.get<ScheduleVersion[]>(`/schedule/versions?semester_id=${selectedSem}`);
      const published = versions.find(v => v.status === 'published');
      if (published) {
        const data = await apiClient.get<ScheduleEntry[]>(`/schedule/versions/${published.id}/entries/detailed?group_id=${selectedGroup}`);
        setSchedule(data);
      } else {
        setSchedule([]);
      }
    } catch {
      setSchedule([]);
    } finally {
      setLoading(false);
    }
  }, [selectedSem, selectedGroup]);

  useEffect(() => {
    fetchSchedule();
  }, [fetchSchedule]);

  const days = [1, 2, 3, 4, 5, 6];
  const dayNames = [t.monday, t.tuesday, t.wednesday, t.thursday, t.friday, t.saturday];

  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-museum-text mb-2">{t.publicScheduleTitle}</h1>
        <p className="text-museum-text-muted">{t.publicScheduleSubtitle}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10 bg-museum-surface border border-museum-border p-6 rounded-museum-md shadow-sm">
        <Select
          label={t.semesterLabel}
          value={selectedSem}
          onChange={(e) => setSelectedSem(Number(e.target.value))}
        >
          <option value="">{t.selectSemester}</option>
          {semesters.map(s => (
            <option key={s.id} value={s.id}>{s.academic_year?.name} - {s.number} {t.semSuffix}</option>
          ))}
        </Select>
        <Select
          label={t.selectGroupLabel}
          value={selectedGroup}
          onChange={(e) => setSelectedGroup(Number(e.target.value))}
        >
          <option value="">{t.selectGroup}</option>
          {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
        </Select>
      </div>

      {!selectedSem || !selectedGroup ? (
        <div className="flex flex-col items-center justify-center py-20 bg-museum-surface border border-dashed border-museum-border rounded-museum-md text-museum-text-muted">
          <Info className="h-12 w-12 mb-4 opacity-20" />
          <p>{t.noScheduleHint}</p>
        </div>
      ) : loading ? (
        <div className="flex justify-center p-20 animate-pulse text-museum-accent"><Clock /></div>
      ) : schedule.length === 0 ? (
        <div className="text-center py-20 bg-museum-surface border border-museum-border rounded-museum-md">
          <p className="text-museum-text font-bold text-lg">{t.noScheduleData}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {days.map((dayNum, idx) => {
            const dayLessons = schedule.filter(s => s.day_of_week === dayNum).sort((a,b) => a.time_slot_number - b.time_slot_number);
            if (dayLessons.length === 0) return null;
            return (
              <div key={dayNum} className="bg-museum-surface border border-museum-border rounded-museum-md overflow-hidden shadow-sm">
                <div className="bg-museum-accent px-4 py-2 text-white font-bold uppercase tracking-wider text-sm">
                  {dayNames[idx]}
                </div>
                <div className="divide-y divide-museum-border/40">
                  {dayLessons.map((l, i) => (
                    <div key={i} className="p-4 hover:bg-museum-surface-hover transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <span className="flex items-center gap-1.5 text-xs font-bold text-museum-accent bg-museum-bg px-2 py-0.5 rounded">
                          {l.time_slot_number} {t.pair}
                        </span>
                        <span className="text-[10px] text-museum-text-muted font-bold font-mono">
                          {l.start_time.slice(0,5)} - {l.end_time.slice(0,5)}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-museum-text mb-1 leading-tight">
                        {l.subject_name}
                      </h3>
                      <div className="space-y-1">
                        <p className="text-xs text-museum-text-secondary flex items-center gap-1.5">
                           <Users className="h-3 w-3" /> {l.teacher_name}
                        </p>
                        <p className="text-xs text-museum-text-secondary flex items-center gap-1.5 font-bold">
                           <MapPin className="h-3 w-3" /> {l.classroom_name}
                        </p>
                      </div>
                      {l.week_type !== 'обе' && (
                        <div className="mt-2 text-[9px] font-bold uppercase py-0.5 px-1.5 bg-museum-bg border border-museum-border inline-block rounded">
                           {l.week_type === 'числитель' ? t.weekNumerator : t.weekDenominator}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
