import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useLang } from '../context/LanguageContext';
import Classrooms from './Classrooms';
import Subjects from './Subjects';
import { Building2, BookOpen } from 'lucide-react';

export default function ClassroomsAndSubjects() {
  const { t } = useLang();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<'classrooms' | 'subjects'>('classrooms');

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'classrooms' || tab === 'subjects') {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const handleTabChange = (tab: 'classrooms' | 'subjects') => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-museum-border">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => handleTabChange('classrooms')}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-bold text-sm flex items-center gap-2 transition-colors
              ${
                activeTab === 'classrooms'
                  ? 'border-orange-500 text-orange-500'
                  : 'border-transparent text-museum-text-muted hover:text-museum-text-secondary hover:border-museum-border'
              }
            `}
          >
            <Building2 className="w-5 h-5" />
            {t.classrooms}
          </button>
          
          <button
            onClick={() => handleTabChange('subjects')}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-bold text-sm flex items-center gap-2 transition-colors
              ${
                activeTab === 'subjects'
                  ? 'border-purple-500 text-purple-500'
                  : 'border-transparent text-museum-text-muted hover:text-museum-text-secondary hover:border-museum-border'
              }
            `}
          >
            <BookOpen className="w-5 h-5" />
            {t.subjects}
          </button>
        </nav>
      </div>

      <div className="mt-6">
        {activeTab === 'classrooms' ? <Classrooms /> : <Subjects />}
      </div>
    </div>
  );
}
