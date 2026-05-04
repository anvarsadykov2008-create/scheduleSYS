import { useLang } from '../context/LanguageContext';
import { Globe } from 'lucide-react';

export default function LanguageSwitcher() {
  const { lang, setLang } = useLang();
  return (
    <button
      onClick={() => setLang(lang === 'ru' ? 'kz' : 'ru')}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-museum-sm border border-museum-border text-museum-text-secondary hover:text-museum-text hover:bg-museum-surface-hover text-sm font-semibold transition-colors"
    >
      <Globe className="h-4 w-4" />
      {lang === 'ru' ? 'KZ' : 'RU'}
    </button>
  );
}
