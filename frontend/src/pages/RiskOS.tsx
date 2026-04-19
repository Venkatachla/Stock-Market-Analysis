import React, { useCallback, useMemo } from 'react';
import { usePolling } from '@/hooks/usePolling';
import { fetchRiskMetrics } from '@/services/api';
import { mockRisk } from '@/utils/mockData';
import { MetricCard } from '@/components/common/StatusComponents';
import { Shield, AlertTriangle, Activity, TrendingDown } from 'lucide-react';
import type { RiskMetrics } from '@/services/api';

const RiskOS: React.FC = () => {
  const pollRiskMetrics = useCallback(
    () => fetchRiskMetrics().catch(() => mockRisk),
    []
  );

  const { data: risk } = usePolling<RiskMetrics>(
    pollRiskMetrics, 30000
  );

  const metrics = risk ?? mockRisk;
  const symbols = Object.keys(metrics.correlationMatrix);

  const riskLevel = useMemo(() => {
    if (metrics.volatility > 25) return { label: 'High', color: 'text-signal-sell' };
    if (metrics.volatility > 15) return { label: 'Medium', color: 'text-yellow-500' };
    return { label: 'Low', color: 'text-signal-buy' };
  }, [metrics.volatility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Risk-OS</h1>
        <p className="text-sm text-muted-foreground mt-1">Portfolio risk analysis and monitoring</p>
      </div>

      {/* Risk Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard label="Value at Risk (95%)" value={`${metrics.portfolioVar.toFixed(2)}%`}
          icon={<AlertTriangle className="h-4 w-4 text-signal-sell" />} />
        <MetricCard label="Sharpe Ratio" value={metrics.sharpeRatio.toFixed(2)}
          positive={metrics.sharpeRatio > 1}
          change={metrics.sharpeRatio > 1 ? 'Good' : 'Below average'}
          icon={<Shield className="h-4 w-4 text-primary" />} />
        <MetricCard label="Beta" value={metrics.beta.toFixed(2)}
          icon={<Activity className="h-4 w-4 text-primary" />} />
        <MetricCard label="Max Drawdown" value={`${metrics.maxDrawdown.toFixed(2)}%`}
          icon={<TrendingDown className="h-4 w-4 text-signal-sell" />} />
        <MetricCard label="Volatility" value={`${metrics.volatility.toFixed(1)}%`}
          change={riskLevel.label}
          positive={riskLevel.label === 'Low'}
          icon={<Activity className="h-4 w-4 text-primary" />} />
      </div>

      {/* Risk Gauge */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="font-semibold text-card-foreground mb-4">Risk Assessment</h2>
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32">
            <svg viewBox="0 0 100 100" className="transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
              <circle cx="50" cy="50" r="40" fill="none" stroke={metrics.volatility > 25 ? '#ef4444' : metrics.volatility > 15 ? '#f59e0b' : '#22c55e'}
                strokeWidth="8" strokeDasharray={`${(metrics.volatility / 40) * 251.2} 251.2`} strokeLinecap="round" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-xl font-bold ${riskLevel.color}`}>{riskLevel.label}</span>
            </div>
          </div>
          <div className="space-y-2 text-sm">
            <p className="text-muted-foreground">
              Portfolio volatility is <span className={`font-semibold ${riskLevel.color}`}>{metrics.volatility.toFixed(1)}%</span> annualized.
            </p>
            <p className="text-muted-foreground">
              With a VaR of {metrics.portfolioVar.toFixed(2)}%, there is a 5% chance of losing more than this in a single day.
            </p>
            <p className="text-muted-foreground">
              Sharpe ratio of {metrics.sharpeRatio.toFixed(2)} indicates {metrics.sharpeRatio > 1 ? 'good' : 'suboptimal'} risk-adjusted returns.
            </p>
          </div>
        </div>
      </div>

      {/* Correlation Matrix */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold text-card-foreground mb-4">Correlation Matrix</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr>
                <th className="px-3 py-2 text-left text-muted-foreground font-medium" />
                {symbols.map(s => <th key={s} className="px-3 py-2 text-center text-muted-foreground font-medium text-xs">{s}</th>)}
              </tr>
            </thead>
            <tbody>
              {symbols.map(row => (
                <tr key={row} className="border-t border-border">
                  <td className="px-3 py-2 font-medium text-foreground text-xs">{row}</td>
                  {symbols.map(col => {
                    const val = metrics.correlationMatrix[row]?.[col] ?? 0;
                    const intensity = Math.abs(val);
                    const bg = val === 1
                      ? 'bg-primary/20'
                      : intensity > 0.7
                        ? 'bg-signal-sell/20'
                        : intensity > 0.4
                          ? 'bg-yellow-500/15'
                          : 'bg-signal-buy/10';
                    return (
                      <td key={col} className={`px-3 py-2 text-center font-mono text-xs ${bg} rounded`}>
                        {val.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          High correlation (&gt;0.7) between holdings increases portfolio risk. Consider diversifying into less correlated assets.
        </p>
      </div>
    </div>
  );
};

export default React.memo(RiskOS);
