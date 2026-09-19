import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  trendText?: string;
  color?: 'cyan' | 'emerald' | 'amber' | 'red';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trendText,
  color = 'cyan',
}) => {
  const colorMap = {
    cyan: 'text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    emerald: 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    amber: 'text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20',
    red: 'text-red-600 dark:text-red-400 bg-red-500/10 border-red-500/20',
  };

  return (
    <div className="p-4 rounded-xl bg-slate-50 dark:bg-[#091b27] border border-slate-200 dark:border-[#183a4f] shadow-sm flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold text-slate-500 dark:text-[#8ba5b5] uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-1.5 rounded-lg border ${colorMap[color]}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="mt-2">
        <div className="text-xl font-black text-slate-900 dark:text-white tracking-tight">{value}</div>
        {subtitle && <p className="text-[11px] text-slate-500 dark:text-[#8ba5b5] mt-0.5">{subtitle}</p>}
        {trendText && (
          <div className="text-[11px] font-semibold mt-1 flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
            <span>{trendText}</span>
          </div>
        )}
      </div>
    </div>
  );
};
