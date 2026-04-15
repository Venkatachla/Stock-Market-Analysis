'use client';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  className?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  className = '',
  trend,
}: StatCardProps) {
  const trendColor =
    trend === 'up'
      ? 'text-accent-green'
      : trend === 'down'
        ? 'text-accent-red'
        : 'text-gray-400';

  const changeBgColor =
    trend === 'up'
      ? 'bg-green-500/10'
      : trend === 'down'
        ? 'bg-red-500/10'
        : 'bg-gray-500/10';

  return (
    <div
      className={`bg-trading-card border border-gray-700/50 rounded-lg p-4 hover:border-gray-600 transition-colors ${className}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        {icon && <div className="text-gray-500 ml-2">{icon}</div>}
      </div>

      {change !== undefined && (
        <div className={`flex items-center gap-2 mt-2 ${trendColor}`}>
          <span className="text-sm font-semibold">
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {Math.abs(change).toFixed(2)}%
          </span>
          {changeLabel && <span className="text-xs text-gray-400">{changeLabel}</span>}
        </div>
      )}
    </div>
  );
}

export default StatCard;
