import React, { useCallback, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { fetchDiscovery } from '@/services/api';
import { mockSignals } from '@/utils/mockData';
import { formatCurrency, formatPercent, formatLargeNumber } from '@/utils/format';
import { SignalBadge } from '@/components/common/StatusComponents';
import { Search } from 'lucide-react';
import type { StockSignal } from '@/services/api';

const sectors = ['All', 'Banking', 'IT', 'Energy', 'FMCG', 'Telecom', 'Pharma', 'Auto'];
const signalFilters = ['All', 'BUY', 'SELL', 'NEUTRAL'] as const;

const Discovery: React.FC = () => {
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('All');
  const [signalFilter, setSignalFilter] = useState<typeof signalFilters[number]>('All');
  const [sortBy, setSortBy] = useState<'change' | 'volume' | 'confidence'>('confidence');
  const pollDiscovery = useCallback(
    () => fetchDiscovery().catch(() => mockSignals),
    []
  );

  const { data: stocks } = usePolling<StockSignal[]>(
    pollDiscovery, 30000
  );

  const items = stocks ?? mockSignals;

  const filtered = useMemo(() => {
    let result = [...items];
    if (search) result = result.filter(s => s.symbol.toLowerCase().includes(search.toLowerCase()) || s.name.toLowerCase().includes(search.toLowerCase()));
    if (sector !== 'All') result = result.filter(s => s.sector === sector);
    if (signalFilter !== 'All') result = result.filter(s => s.signal === signalFilter);
    result.sort((a, b) => {
      if (sortBy === 'change') return Math.abs(b.changePercent) - Math.abs(a.changePercent);
      if (sortBy === 'volume') return b.volume - a.volume;
      return b.confidence - a.confidence;
    });
    return result;
  }, [items, search, sector, signalFilter, sortBy]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Stock Discovery</h1>
        <p className="text-sm text-muted-foreground mt-1">Find stocks based on signals, sectors, and momentum</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            id="discovery-search"
            name="search"
            type="text"
            placeholder="Search stocks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="Search stocks"
          />
        </div>
        <select id="discovery-sector" name="sector" value={sector} onChange={(e) => setSector(e.target.value)} className="px-3 py-2 text-sm rounded-md border border-input bg-background text-foreground" aria-label="Filter by sector">
          {sectors.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select id="discovery-signal" name="signal" value={signalFilter} onChange={(e) => setSignalFilter(e.target.value as typeof signalFilters[number])} className="px-3 py-2 text-sm rounded-md border border-input bg-background text-foreground" aria-label="Filter by signal">
          {signalFilters.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select id="discovery-sort" name="sort" value={sortBy} onChange={(e) => setSortBy(e.target.value as 'change' | 'volume' | 'confidence')} className="px-3 py-2 text-sm rounded-md border border-input bg-background text-foreground" aria-label="Sort by">
          <option value="confidence">Confidence</option>
          <option value="change">Change %</option>
          <option value="volume">Volume</option>
        </select>
      </div>

      {/* Results */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((s) => (
          <Link
            key={s.symbol}
            to={`/stock/${s.symbol}`}
            className="rounded-lg border border-border bg-card p-4 hover:border-primary/50 transition-colors group"
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="font-semibold text-card-foreground group-hover:text-primary transition-colors">{s.symbol}</span>
                <div className="text-xs text-muted-foreground">{s.name}</div>
              </div>
              <SignalBadge signal={s.signal} />
            </div>
            <div className="flex items-end justify-between">
              <div>
                <div className="text-lg font-mono font-semibold text-card-foreground">{formatCurrency(s.price)}</div>
                <div className={`text-sm font-mono ${s.change >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>{formatPercent(s.changePercent)}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground">Vol</div>
                <div className="text-sm font-mono text-muted-foreground">{formatLargeNumber(s.volume)}</div>
              </div>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Confidence</span>
                <span>{typeof s.confidence === "number" ? (s.confidence * 100).toFixed(0) : "0"}%</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${s.confidence * 100}%` }} />
              </div>
            </div>
            {s.sector && <div className="mt-2 text-xs text-muted-foreground">Sector: {s.sector}</div>}
          </Link>
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">No stocks match your filters.</div>
      )}
    </div>
  );
};

export default React.memo(Discovery);
