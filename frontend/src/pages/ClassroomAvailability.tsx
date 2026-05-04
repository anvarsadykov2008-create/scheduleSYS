import { useState, useEffect, useCallback } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import Select from '../components/ui/Select';
import { CheckCircle2, XCircle } from 'lucide-react';

interface Semester { id: number; number: number; academic_year?: { name: string } }
interface Classroom { id: number; name: string; type: string }
interface BusyClassroom { classroom_id: number; pair_number: number; info: string }
interface ScheduleVersion { id: number; status: string }
interface ScheduleEntry {
  classroom_id: number;
  classroom_name: string;
  day_of_week: number;
  time_slot_number: number;
  group_name: string;
  subject_name: string;
}

export default function ClassroomAvailability() {
  const { t } = useLang();
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [selectedSem, setSelectedSem] = useState<number | ''>('');
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [busyList, setBusyList] = useState<BusyClassroom[]>([]);
  const [, setLoading] = useState(false);

  useEffect(() => {
    apiClient.get<Semester[]>('/semesters').then(setSemesters).catch(() => {});
    apiClient.get<Classroom[]>('/classrooms').then(setClassrooms).catch(() => {});
  }, []);

  const fetchAvailability = useCallback(async () => {
    if (!selectedSem) return;
    setLoading(true);
    try {
      // Find published version
      const versions = await apiClient.get<ScheduleVersion[]>(`/schedule/versions?semester_id=${selectedSem}`);
      const published = versions.find(v => v.status === 'published');
      if (published) {
        const jsDay = new Date().getDay(); // 0=Sun,1=Mon...6=Sat
        const today = jsDay === 0 ? 7 : jsDay; // convert to Mon=1..Sun=7
        if (today >= 1 && today <= 5) {
          const data = await apiClient.get<ScheduleEntry[]>(`/schedule/versions/${published.id}/entries/detailed`);
          const todayEntries = data.filter(d => d.day_of_week === today);
          const busy = todayEntries.map(d => ({
            classroom_id: d.classroom_id,
            pair_number: d.time_slot_number,
            info: `${d.group_name} - ${d.subject_name}`,
          }));
          setBusyList(busy);
        }
      }
    } catch {
      setBusyList([]);
    } finally {
      setLoading(false);
    }
  }, [selectedSem]);

  useEffect(() => {
    fetchAvailability();
  }, [fetchAvailability]);

  const pairs = [1, 2, 3, 4];

  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-museum-text">{t.freeClassroomsTitle}</h1>
        <div className="flex items-center gap-2 mt-1">
          <div className="w-2 h-2 bg-museum-success rounded-full animate-pulse" />
          <span className="text-xs text-museum-text-muted font-bold uppercase tracking-wider">{t.realtime}</span>
        </div>
      </div>

      <div className="max-w-xs mb-8">
        <Select
          label={t.semesterSelect}
          value={selectedSem}
          onChange={(e) => setSelectedSem(Number(e.target.value))}
        >
          <option value="">{t.selectSemester}</option>
          {semesters.map(s => (
            <option key={s.id} value={s.id}>{s.academic_year?.name} - {s.number} {t.semSuffix}</option>
          ))}
        </Select>
      </div>

      {!selectedSem ? (
         <div className="bg-museum-surface border border-museum-border p-10 rounded-museum-md text-center text-museum-text-muted">
            {t.selectSemesterWithSchedule}
         </div>
      ) : (
        <div className="overflow-x-auto bg-museum-surface border border-museum-border rounded-museum-md shadow-sm">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-museum-bg border-b border-museum-border">
                <th className="p-4 text-left font-bold text-museum-text-secondary uppercase text-[10px] tracking-widest">{t.collegeClassrooms}</th>
                {pairs.map(p => (
                  <th key={p} className="p-4 text-center font-bold text-museum-text-secondary uppercase text-[10px] tracking-widest">
                    {p} {t.pairN}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {classrooms.map(c => (
                <tr key={c.id} className="border-b border-museum-border/40 hover:bg-museum-surface-hover transition-colors">
                  <td className="p-4">
                    <div className="font-bold text-museum-text">{c.name}</div>
                    <div className="text-[10px] text-museum-text-muted font-bold uppercase">{c.type}</div>
                  </td>
                  {pairs.map(p => {
                    const occupant = busyList.find(b => b.classroom_id === c.id && b.pair_number === p);
                    return (
                      <td key={p} className="p-4 text-center">
                        {occupant ? (
                          <div className="group relative">
                            <XCircle className="h-5 w-5 text-museum-danger mx-auto" />
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-museum-surface border border-museum-border rounded shadow-xl hidden group-hover:block z-20">
                               <p className="text-[10px] font-bold text-museum-danger uppercase mb-1">{t.classroomsOccupied}</p>
                               <p className="text-xs text-museum-text font-bold">{occupant.info}</p>
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center">
                             <CheckCircle2 className="h-5 w-5 text-museum-success" />
                             <span className="text-[10px] font-bold text-museum-success uppercase mt-1 opacity-0 group-hover:opacity-100">{t.classroomsFree}</span>
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
