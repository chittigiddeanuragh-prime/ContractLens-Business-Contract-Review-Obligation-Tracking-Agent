import React from 'react';

export type BadgeVariant = 'critical' | 'at_risk' | 'good' | 'info' | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'info',
  size = 'sm',
  className = '',
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    critical: 'bg-red-100 text-red-700 dark:bg-[#ef4444] dark:text-white border-red-200 dark:border-red-500',
    at_risk: 'bg-amber-100 text-amber-800 dark:bg-[#f59e0b] dark:text-slate-950 border-amber-200 dark:border-amber-400',
    good: 'bg-emerald-100 text-emerald-800 dark:bg-[#10b981] dark:text-slate-950 border-emerald-200 dark:border-emerald-400',
    info: 'bg-sky-100 text-sky-800 dark:bg-[#0ea5e9] dark:text-white border-sky-200 dark:border-sky-400',
    neutral: 'bg-slate-100 text-slate-700 dark:bg-[#183a4f] dark:text-slate-300 border-slate-200 dark:border-[#25526e]',
  };

  const sizeStyles = size === 'sm' ? 'px-2.5 py-0.5 text-xs font-bold' : 'px-3 py-1 text-xs font-black';

  return (
    <span className={`inline-flex items-center rounded-full border shadow-sm ${variantStyles[variant]} ${sizeStyles} ${className}`}>
      {children}
    </span>
  );
};
