import React from 'react';

interface DonutChartData {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  data: DonutChartData[];
  totalLabel?: string;
  size?: number;
}

export const DonutChart: React.FC<DonutChartProps> = ({
  data,
  totalLabel = 'Total Risk Items',
  size = 140,
}) => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let accumulatedPercent = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-200 dark:text-[#183a4f]"
            fill="transparent"
          />
          {total > 0 &&
            data.map((item, idx) => {
              const percent = item.value / total;
              const strokeDasharray = `${percent * circumference} ${circumference}`;
              const strokeDashoffset = -accumulatedPercent * circumference;
              accumulatedPercent += percent;

              return (
                <circle
                  key={idx}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  stroke={item.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-500 hover:opacity-80"
                />
              );
            })}
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-2">
          <span className="text-xl font-black text-slate-900 dark:text-white leading-none">{total}</span>
          <span className="text-[10px] font-bold text-slate-500 dark:text-[#8ba5b5] mt-0.5 uppercase tracking-tighter">
            {totalLabel}
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-2 w-full">
        {data.map((item, idx) => {
          const percent = total > 0 ? Math.round((item.value / total) * 100) : 0;
          return (
            <div key={idx} className="flex items-center justify-between text-xs font-semibold">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                <span className="text-slate-700 dark:text-slate-200">{item.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-900 dark:text-white font-bold">{item.value}</span>
                <span className="text-[11px] text-slate-400 dark:text-[#648498] w-9 text-right">({percent}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
