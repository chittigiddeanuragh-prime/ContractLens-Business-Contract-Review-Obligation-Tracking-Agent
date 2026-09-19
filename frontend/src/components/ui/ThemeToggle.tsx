import React, { useEffect, useState } from 'react';
import { Sun, Moon, Laptop } from 'lucide-react';

export type ThemeMode = 'dark' | 'light' | 'system';

export const ThemeToggle: React.FC = () => {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem('contractlens-theme') as ThemeMode;
    return saved || 'dark';
  });

  const applyTheme = (mode: ThemeMode) => {
    const root = document.documentElement;
    if (mode === 'dark') {
      root.classList.add('dark');
    } else if (mode === 'light') {
      root.classList.remove('dark');
    } else {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  };

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem('contractlens-theme', theme);
  }, [theme]);

  const cycleTheme = () => {
    if (theme === 'dark') setThemeState('light');
    else if (theme === 'light') setThemeState('system');
    else setThemeState('dark');
  };

  return (
    <button
      onClick={cycleTheme}
      className="p-2 px-3 rounded-xl bg-white dark:bg-[#0e2636] border border-slate-200 dark:border-[#183a4f] text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-[#133044] transition-all shadow-sm flex items-center gap-2 text-xs font-bold"
      title={`Theme: ${theme.toUpperCase()} (Click to toggle)`}
    >
      {theme === 'dark' && (
        <>
          <Moon className="w-4 h-4 text-cyan-400" />
          <span className="hidden sm:inline">Dark</span>
        </>
      )}
      {theme === 'light' && (
        <>
          <Sun className="w-4 h-4 text-amber-500" />
          <span className="hidden sm:inline">Light</span>
        </>
      )}
      {theme === 'system' && (
        <>
          <Laptop className="w-4 h-4 text-sky-400" />
          <span className="hidden sm:inline">System</span>
        </>
      )}
    </button>
  );
};
