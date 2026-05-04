import { useState, useEffect } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import { Calendar, Clock, MapPin, Users, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';

interface ScheduleEntry {
  id: number;
  day_of_week: number;
  time_slot_number: number;
  start_time: string;
  end_time: string;
  subject_name: string;
  teacher_name: string;
  classroom_name: string;
  lesson_type: string;
}

export default function StudentSchedule() {
  const { t } = useLang();
  const [schedule, setSchedule] = useState<ScheduleEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const data = await apiClient.get<ScheduleEntry[]>('/schedule/my');
        setSchedule(data);
      } catch {
        setSchedule([]);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  const days = [1, 2, 3, 4, 5, 6];
  const dayNames = [t.monday, t.tuesday, t.wednesday, t.thursday, t.friday, t.saturday];

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="flex items-center gap-4 mb-8">
        <Link to="/student">
           <Button variant="ghost" size="sm">
             <ArrowLeft className="h-4 w-4 mr-2" /> {t.back}
           </Button>
        </Link>
        <h1 className="text-2xl font-bold text-museum-text">{t.mySchedule}</h1>
      </div>

      {loading ? (
        <div className="flex justify-center p-20 animate-spin text-museum-accent"><Clock /></div>
      ) : schedule.length === 0 ? (
        <div className="bg-museum-surface border border-museum-border p-12 rounded-museum-md text-center">
            <Calendar className="h-12 w-12 text-museum-text-muted mx-auto mb-4 opacity-20" />
            <p className="text-museum-text-muted">{t.noLessonsThisWeek}</p>
        </div>
      ) : (
        <div className="space-y-6">
          {days.map((dayNum, idx) => {
            const dayLessons = schedule.filter(s => s.day_of_week === dayNum).sort((a,b) => a.time_slot_number - b.time_slot_number);
            if (dayLessons.length === 0) return null;
            return (
              <div key={dayNum} className="bg-museum-surface border border-museum-border rounded-museum-md overflow-hidden shadow-sm">
                <div className="bg-museum-accent px-4 py-2 text-white font-bold uppercase tracking-wider text-xs">
                  {dayNames[idx]}
                </div>
                <div className="divide-y divide-museum-border/40">
                  {dayLessons.map((l, i) => (
                    <div key={i} className="p-4 flex items-start gap-4 hover:bg-museum-surface-hover transition-colors">
                      <div className="flex-shrink-0 w-12 text-center">
                        <span className="text-lg font-bold text-museum-accent">{l.time_slot_number}</span>
                        <p className="text-[10px] text-museum-text-muted font-bold uppercase">{t.pair}</p>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                           <h3 className="text-sm font-bold text-museum-text leading-tight">{l.subject_name}</h3>
                           <span className="text-[10px] text-museum-text-muted font-mono font-bold bg-museum-bg px-1.5 py-0.5 rounded border border-museum-border">
                             {l.start_time.slice(0,5)} - {l.end_time.slice(0,5)}
                           </span>
                        </div>
                        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                           <p className="text-xs text-museum-text-secondary flex items-center gap-1.5">
                             <Users className="h-3 w-3" /> {l.teacher_name}
                           </p>
                           <p className="text-xs text-museum-text-secondary flex items-center gap-1.5 font-bold">
                             <MapPin className="h-3 w-3" /> {l.classroom_name}
                           </p>
                        </div>
                      </div>
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
