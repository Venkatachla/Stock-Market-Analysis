import React, { useMemo } from 'react';
import { usePolling } from '@/hooks/usePolling';
import { fetchPortfolio } from '@/services/api';
import { mockPortfolio } from '@/utils/mockData';
import { formatCurrency, formatPercent } from '@/utils/format';
import { SignalBadge, MetricCard } from '@/components/common/StatusComponents';
import { PieChart, TrendingUp, TrendingDown, Wallet } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { PortfolioHolding } from '@/services/api';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

const Portfolio: React.FC = () => {
  const { data: holdings } = usePolling<PortfolioHolding[]>(
    () => fetchPortfolio().catch(() => mockPortfolio), 30000
  );

  const portfolio = holdings ?? mockPortfolio;

  const stats = useMemo(() => {
    const totalValue = portfolio.reduce((sum, h) => sum + h.currentPrice * h.quantity, 0);
    const totalInvested = portfolio.reduce((sum, h) => sum + h.avgPrice * h.quantity, 0);
    const totalPnl = totalValue - totalInvested;
    const totalPnlPercent = (totalPnl / totalInvested) * 100;
    return { totalValue, totalInvested, totalPnl, totalPnlPercent };
  }, [portfolio]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Portfolio Analysis</h1>
        <p className="text-sm text-muted-foreground mt-1">Track your holdings and performance</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Portfolio Value" value={formatCurrency(stats.totalValue)} icon={<Wallet className="h-4 w-4 text-primary" />} />
        <MetricCard label="Invested" value={formatCurrency(stats.totalInvested)} />
        <MetricCard label="Total P&L" value={formatCurrency(stats.totalPnl)} change={formatPercent(stats.totalPnlPercent)} positive={stats.totalPnl >= 0}
          icon={stats.totalPnl >= 0 ? <TrendingUp className="h-4 w-4 text-signal-buy" /> : <TrendingDown className="h-4 w-4 text-signal-sell" />} />
        <MetricCard label="Holdings" value={portfolio.length.toString()} icon={<PieChart className="h-4 w-4 text-primary" />} />
      </div>

      {/* Allocation visual */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold text-card-foreground mb-4">Allocation</h2>
        <div className="flex h-6 rounded-full overflow-hidden">
          {portfolio.map((h, i) => (
            <div
              key={h.symbol}
              className="relative group"
              style={{ width: `${h.allocation}%`, backgroundColor: COLORS[i % COLORS.length] }}
              title={`${h.symbol}: ${h.allocation}%`}
            >
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded text-xs font-medium bg-popover text-popover-foreground border border-border opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                {h.symbol}: {h.allocation}%
              </div>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap gap-3 mt-3">
          {portfolio.map((h, i) => (
            <div key={h.symbol} className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
              {h.symbol} ({h.allocation}%)
            </div>
          ))}
        </div>
      </div>

      {/* Holdings Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="font-semibold text-card-foreground">Holdings</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Stock</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">Qty</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">Avg Price</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">Current</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">P&L</th>
                <th className="text-center px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">Signal</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((h) => (
                <tr key={h.symbol} className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors">
                  <td className="px-4 py-3">
                    <Link to={`/stock/${h.symbol}`} className="font-medium text-foreground hover:text-primary">{h.symbol}</Link>
                    <div className="text-xs text-muted-foreground">{h.name}</div>
                  </td>
                  <td className="text-right px-4 py-3 font-mono hidden sm:table-cell">{h.quantity}</td>
                  <td className="text-right px-4 py-3 font-mono hidden md:table-cell">{formatCurrency(h.avgPrice)}</td>
                  <td className="text-right px-4 py-3 font-mono">{formatCurrency(h.currentPrice)}</td>
                  <td className={`text-right px-4 py-3 font-mono ${h.pnl >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
                    {formatCurrency(h.pnl)}
                    <div className="text-xs">{formatPercent(h.pnlPercent)}</div>
                  </td>
                  <td className="text-center px-4 py-3 hidden lg:table-cell"><SignalBadge signal={h.signal} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default React.memo(Portfolio);
