import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { fetchMarketOverview, fetchStockSignals } from '@/services/api';
import { mockMarketOverview, mockSignals } from '@/utils/mockData';
import { formatCurrency, formatPercent, formatLargeNumber } from '@/utils/format';
import { LoadingState, ErrorState, MetricCard, SignalBadge } from '@/components/common/StatusComponents';
import { TrendingUp, TrendingDown, BarChart3, Activity } from 'lucide-react';
import type { StockSignal, MarketOverview } from '@/services/api';

const Dashboard: React.FC = () => {
  const { data: marketData, loading: mLoading, error: mError, retry: mRetry } = usePolling<MarketOverview>(
    () => fetchMarketOverview().catch(() => mockMarketOverview), 30000
  );
  const { data: signalsData, loading: sLoading, error: sError, retry: sRetry } = usePolling<StockSignal[]>(
    () => fetchStockSignals().catch(() => mockSignals), 30000
  );

  const market = marketData ?? mockMarketOverview;
  const signals = signalsData ?? mockSignals;

  const stats = useMemo(() => {
    const buyCount = signals.filter(s => s.signal === 'BUY').length;
    const sellCount = signals.filter(s => s.signal === 'SELL').length;
    return { buyCount, sellCount, total: signals.length };
  }, [signals]);

  if (mLoading && sLoading) return <LoadingState message="Loading dashboard..." />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Market Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Real-time market overview and signals</p>
      </div>

      {/* Market Indices */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {market.indices.map((idx) => (
          <MetricCard
            key={idx.name}
            label={idx.name}
            value={idx.value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            change={formatPercent(idx.changePercent)}
            positive={idx.change >= 0}
            icon={idx.change >= 0 ? <TrendingUp className="h-4 w-4 text-signal-buy" /> : <TrendingDown className="h-4 w-4 text-signal-sell" />}
          />
        ))}
      </div>

      {/* Signal Summary */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard label="Buy Signals" value={stats.buyCount.toString()} icon={<TrendingUp className="h-4 w-4 text-signal-buy" />} />
        <MetricCard label="Sell Signals" value={stats.sellCount.toString()} icon={<TrendingDown className="h-4 w-4 text-signal-sell" />} />
        <MetricCard label="Total Tracked" value={stats.total.toString()} icon={<Activity className="h-4 w-4 text-primary" />} />
      </div>

      {/* Signals Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <h2 className="font-semibold text-card-foreground">Active Signals</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Symbol</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">Price</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">Change</th>
                <th className="text-center px-4 py-3 font-medium text-muted-foreground">Signal</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">Confidence</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">Volume</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s) => (
                <tr key={s.symbol} className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors">
                  <td className="px-4 py-3">
                    <Link to={`/stock/${s.symbol}`} className="font-medium text-foreground hover:text-primary transition-colors">
                      {s.symbol}
                    </Link>
                    <div className="text-xs text-muted-foreground">{s.name}</div>
                  </td>
                  <td className="text-right px-4 py-3 font-mono hidden sm:table-cell">{formatCurrency(s.price)}</td>
                  <td className={`text-right px-4 py-3 font-mono ${s.change >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
                    {formatPercent(s.changePercent)}
                  </td>
                  <td className="text-center px-4 py-3"><SignalBadge signal={s.signal} /></td>
                  <td className="text-right px-4 py-3 hidden md:table-cell">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${s.confidence * 100}%` }} />
                      </div>
                      <span className="text-xs text-muted-foreground">{(s.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="text-right px-4 py-3 font-mono text-muted-foreground hidden lg:table-cell">{formatLargeNumber(s.volume)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Movers */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-border bg-card">
          <div className="px-4 py-3 border-b border-border">
            <h3 className="font-semibold text-signal-buy flex items-center gap-2"><TrendingUp className="h-4 w-4" /> Top Gainers</h3>
          </div>
          <div className="divide-y divide-border">
            {market.topGainers.slice(0, 5).map(s => (
              <Link key={s.symbol} to={`/stock/${s.symbol}`} className="flex items-center justify-between px-4 py-2.5 hover:bg-accent/50 transition-colors">
                <div>
                  <span className="font-medium text-sm text-foreground">{s.symbol}</span>
                  <span className="text-xs text-muted-foreground ml-2">{s.name}</span>
                </div>
                <span className="text-sm font-mono text-signal-buy">{formatPercent(s.changePercent)}</span>
              </Link>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card">
          <div className="px-4 py-3 border-b border-border">
            <h3 className="font-semibold text-signal-sell flex items-center gap-2"><TrendingDown className="h-4 w-4" /> Top Losers</h3>
          </div>
          <div className="divide-y divide-border">
            {market.topLosers.slice(0, 5).map(s => (
              <Link key={s.symbol} to={`/stock/${s.symbol}`} className="flex items-center justify-between px-4 py-2.5 hover:bg-accent/50 transition-colors">
                <div>
                  <span className="font-medium text-sm text-foreground">{s.symbol}</span>
                  <span className="text-xs text-muted-foreground ml-2">{s.name}</span>
                </div>
                <span className="text-sm font-mono text-signal-sell">{formatPercent(s.changePercent)}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(Dashboard);
