import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  hoverable = false,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white dark:bg-[#0e2636] border border-slate-200 dark:border-[#183a4f] rounded-2xl p-6 shadow-sm transition-all ${
        hoverable ? 'hover:bg-slate-50 dark:hover:bg-[#133044] cursor-pointer hover:border-cyan-500/40 dark:hover:border-cyan-500/40' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};
