import { useTheme } from '../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';

export default function ThemeSwitcher() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="fixed bottom-6 right-6 z-50 p-3 rounded-full bg-museum-surface/80 backdrop-blur-md border border-museum-border shadow-lg hover:shadow-xl hover:scale-110 active:scale-95 transition-all group"
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <Moon className="h-6 w-6 text-museum-text-secondary group-hover:text-museum-accent transition-colors" />
      ) : (
        <Sun className="h-6 w-6 text-museum-text-secondary group-hover:text-museum-accent transition-colors" />
      )}
    </button>
  );
}
