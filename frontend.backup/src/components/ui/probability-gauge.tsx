'use client';

interface ProbabilityGaugeProps {
  probUp: number;
  probDown: number;
  size?: 'sm' | 'md' | 'lg';
}

export function ProbabilityGauge({ probUp, probDown, size = 'md' }: ProbabilityGaugeProps) {
  const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-32 h-32',
    lg: 'w-48 h-48',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-2xl',
  };

  const upPercentage = Math.round(probUp * 100);
  const downPercentage = Math.round(probDown * 100);

  return (
    <div className={`flex flex-col items-center justify-center ${sizeClasses[size]}`}>
      <div className="relative w-full h-full">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#1f2937"
            strokeWidth="2"
          />
          {/* Down segment (red) */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#ef4444"
            strokeWidth="6"
            strokeDasharray={`${(downPercentage / 100) * 282.7} 282.7`}
            className="transition-all duration-500"
          />
          {/* Up segment (green) */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#10b981"
            strokeWidth="6"
            strokeDasharray={`${(probUp / 100) * 282.7} 282.7`}
            strokeDashoffset={-((downPercentage / 100) * 282.7)}
            className="transition-all duration-500"
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`${textSizeClasses[size]} font-bold`}>
            {upPercentage > 50 ? '🔼' : '🔽'}
          </div>
          <div className={`text-center ${textSizeClasses[size]} font-semibold text-gray-300 mt-1`}>
            {upPercentage}%
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProbabilityGauge;
