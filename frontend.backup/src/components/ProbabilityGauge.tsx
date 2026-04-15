import { cn } from "@/lib/utils";

interface ProbabilityGaugeProps {
  value: number;
  size?: number;
  className?: string;
}

export function ProbabilityGauge({ value, size = 140, className }: ProbabilityGaugeProps) {
  const clampedValue = Math.max(0, Math.min(100, value));
  const radius = (size - 20) / 2;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (clampedValue / 100) * circumference;

  const getColor = (v: number) => {
    if (v >= 70) return "hsl(var(--success))";
    if (v >= 40) return "hsl(var(--warning))";
    return "hsl(var(--destructive))";
  };

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <svg width={size} height={size / 2 + 20} viewBox={`0 0 ${size} ${size / 2 + 20}`}>
        {/* Background arc */}
        <path
          d={`M ${10} ${size / 2 + 10} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2 + 10}`}
          fill="none"
          stroke="hsl(var(--border))"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={`M ${10} ${size / 2 + 10} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2 + 10}`}
          fill="none"
          stroke={getColor(clampedValue)}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: "stroke-dashoffset 0.8s ease-out, stroke 0.3s" }}
        />
        {/* Value text */}
        <text
          x={size / 2}
          y={size / 2 + 5}
          textAnchor="middle"
          className="font-mono-data"
          fill="hsl(var(--foreground))"
          fontSize={size * 0.18}
          fontWeight="700"
        >
          {clampedValue}%
        </text>
        <text
          x={size / 2}
          y={size / 2 + 20}
          textAnchor="middle"
          fill="hsl(var(--muted-foreground))"
          fontSize={size * 0.08}
        >
          Confidence
        </text>
      </svg>
    </div>
  );
}