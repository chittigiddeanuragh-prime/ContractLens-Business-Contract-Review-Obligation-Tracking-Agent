import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className = '',
}) => {
  return (
    <div className={`flex items-center gap-1 border-b border-slate-200 dark:border-[#183a4f] overflow-x-auto no-scrollbar ${className}`}>
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all border-b-2 whitespace-nowrap ${
              isActive
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400 bg-cyan-500/5 dark:bg-[#0e2636]'
                : 'border-transparent text-slate-500 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white hover:border-slate-300 dark:hover:border-[#25526e]'
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-600 dark:text-cyan-300'
                    : 'bg-slate-200 dark:bg-[#183a4f] text-slate-600 dark:text-[#8ba5b5]'
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
