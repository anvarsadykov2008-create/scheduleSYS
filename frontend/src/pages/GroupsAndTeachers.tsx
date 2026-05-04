import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useLang } from '../context/LanguageContext';
import Groups from './Groups';
import Teachers from './Teachers';
import { Users, GraduationCap } from 'lucide-react';

export default function GroupsAndTeachers() {
  const { t } = useLang();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<'groups' | 'teachers'>('groups');

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'teachers' || tab === 'groups') {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const handleTabChange = (tab: 'groups' | 'teachers') => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-museum-border">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => handleTabChange('groups')}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-bold text-sm flex items-center gap-2 transition-colors
              ${
                activeTab === 'groups'
                  ? 'border-blue-500 text-blue-500'
                  : 'border-transparent text-museum-text-muted hover:text-museum-text-secondary hover:border-museum-border'
              }
            `}
          >
            <GraduationCap className="w-5 h-5" />
            {t.groups}
          </button>
          
          <button
            onClick={() => handleTabChange('teachers')}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-bold text-sm flex items-center gap-2 transition-colors
              ${
                activeTab === 'teachers'
                  ? 'border-green-500 text-green-500'
                  : 'border-transparent text-museum-text-muted hover:text-museum-text-secondary hover:border-museum-border'
              }
            `}
          >
            <Users className="w-5 h-5" />
            {t.teachers}
          </button>
        </nav>
      </div>

      <div className="mt-6">
        {activeTab === 'groups' ? <Groups /> : <Teachers />}
      </div>
    </div>
  );
}
