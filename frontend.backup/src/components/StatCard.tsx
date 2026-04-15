import { ReactNode } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string;
  change?: number;
  changeSuffix?: string;
  icon?: ReactNode;
  className?: string;
}

export function StatCard({ title, value, change, changeSuffix = "%", icon, className }: StatCardProps) {
  return (
    <div className={cn("stat-card", className)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</span>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </div>
      <div className="font-mono-data text-[1.75rem] font-bold text-foreground leading-tight">{value}</div>
      {change !== undefined && (
        <div className={cn("flex items-center gap-1 mt-1 text-sm font-medium", change >= 0 ? "gauge-value-positive" : "gauge-value-negative")}>
          {change > 0 ? <TrendingUp className="h-3.5 w-3.5" /> : change < 0 ? <TrendingDown className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
          <span>{change >= 0 ? "+" : ""}{change.toFixed(2)}{changeSuffix}</span>
        </div>
      )}
    </div>
  );
}