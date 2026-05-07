import React, { useCallback, useMemo, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { fetchMarketOverview, fetchStockSignals } from '@/services/api';
import { mockMarketOverview, mockSignals } from '@/utils/mockData';
import { formatCurrency, formatPercent, formatLargeNumber } from '@/utils/format';
import { LoadingState, ErrorState, MetricCard, SignalBadge } from '@/components/common/StatusComponents';
import { TrendingUp, TrendingDown, BarChart3, Activity, Search, Sparkles, X, Wifi } from 'lucide-react';
import type { StockSignal, MarketOverview } from '@/services/api';

const Dashboard: React.FC = () => {
  // --- ARCHITECTURE: Separate data sources for production UX ---
  const [marketSignals, setMarketSignals] = useState<StockSignal[]>([]);
  const [searchResults, setSearchResults] = useState<StockSignal[] | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [pollInfo, setPollInfo] = useState<{lastUpdate: string, pollCount: number}>({lastUpdate: '', pollCount: 0});

  const pollMarketData = useCallback(() => {
    return fetchMarketOverview();
  }, []);

  const pollSignalsData = useCallback(() => {
    console.log('🎯 Fetching live signals...');
    setPollInfo(prev => ({
      lastUpdate: new Date().toLocaleTimeString(),
      pollCount: prev.pollCount + 1
    }));
    return fetchStockSignals();
  }, []);

  // 🔄 REAL-TIME MARKET DATA - Poll every 10 seconds (market indices)
  const { data: marketData, loading: mLoading } = usePolling<MarketOverview>(
    pollMarketData,
    10000
  );
  
  // 🔄 REAL-TIME STOCK SIGNALS - Poll every 8 seconds (live signals)
  const { data: signalsData, loading: sLoading } = usePolling<StockSignal[]>(
    pollSignalsData,
    8000
  );

  // --- SYNC POLLING TO DISPLAY DATA ---
  // Protection: DO NOT overwrite if user is viewing search results
  useEffect(() => {
    if (!searchResults && signalsData) {
      setMarketSignals(signalsData);
    }
  }, [signalsData, searchResults]);

  const market = marketData ?? { indices: [], topGainers: [], topLosers: [], mostActive: [] };

  // --- SOURCE OF TRUTH ---
  const activeSignals = searchResults ?? marketSignals;

  const stats = useMemo(() => {
    const buyCount = activeSignals.filter(s => s.signal === 'BUY').length;
    const sellCount = activeSignals.filter(s => s.signal === 'SELL').length;
    return { buyCount, sellCount, total: activeSignals.length };
  }, [activeSignals]);

  // --- DERIVED STATE: LOCAL FILTERING ---
  const filteredSignals = useMemo(() => {
    if (!searchQuery) return activeSignals;

    const q = searchQuery.toLowerCase();
    return activeSignals.filter(signal =>
      signal.symbol?.toLowerCase().includes(q) ||
      signal.signal?.toLowerCase().includes(q) ||
      (signal.name && signal.name.toLowerCase().includes(q))
    );
  }, [activeSignals, searchQuery]);

  // --- ACTIONS ---
  const handlePromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 12 })
      });
      
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Prompt error:', error);
      // Fallback: Use what we have in marketSignals
      const q = searchQuery.toLowerCase();
      const fallbackResults = marketSignals.filter(s => 
        s.symbol.toLowerCase().includes(q) || 
        (s.name && s.name.toLowerCase().includes(q))
      );
      setSearchResults(fallbackResults);
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchResults(null);
    setSearchQuery("");
  };

  if (mLoading && sLoading && marketSignals.length === 0) return <LoadingState message="Connecting to market..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Market Dashboard</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="flex h-2 w-2 rounded-full bg-signal-buy animate-pulse" />
            <p className="text-sm text-muted-foreground">Market Pulse Live • {pollInfo.lastUpdate || 'Connecting...'}</p>
          </div>
        </div>
        
        {searchResults && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 animate-in fade-in slide-in-from-right-4">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-xs font-medium text-primary">Viewing Custom Results</span>
            <button 
              onClick={clearSearch}
              className="ml-2 p-0.5 rounded-full hover:bg-primary/20 text-primary transition-colors"
              title="Return to live data"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>

      {/* Prompt Input */}
      <form onSubmit={handlePromptSubmit} className="space-y-2">
        <div className="relative group">
          <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
          <input
            id="dashboard-search"
            name="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search symbols or ask AI... 'Show bullish tech stocks', 'RELIANCE', etc."
            className="w-full pl-10 pr-24 py-2.5 rounded-xl border border-border bg-card text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary shadow-sm"
          />
          <div className="absolute right-2 top-2 flex items-center gap-1">
            {searchQuery && (
              <button 
                type="button"
                onClick={clearSearch}
                className="p-1.5 rounded-md hover:bg-accent text-muted-foreground transition-colors"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <button
              type="submit"
              disabled={loading || !searchQuery.trim()}
              className="p-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all flex items-center gap-2 px-3"
              aria-label="Search signals"
            >
              {loading ? (
                <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span className="text-xs font-medium hidden sm:inline">Ask AI</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

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
        <MetricCard label="Total Visible" value={stats.total.toString()} icon={<Activity className="h-4 w-4 text-primary" />} />
      </div>

      {/* Unified Signals Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <h2 className="font-semibold text-card-foreground">
              {searchResults ? 'Tailored Insights' : 'Active Market Signals'}
            </h2>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground bg-muted/50 px-2 py-0.5 rounded uppercase tracking-wider font-semibold">
            <Wifi className={`h-3 w-3 ${!searchResults ? 'text-signal-buy animate-pulse' : 'text-muted-foreground'}`} />
            {!searchResults ? 'Live Streaming' : 'Static Result'}
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground uppercase text-[10px] tracking-wider">Symbol</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground uppercase text-[10px] tracking-wider hidden sm:table-cell">Price</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground uppercase text-[10px] tracking-wider">Change</th>
                <th className="text-center px-4 py-3 font-medium text-muted-foreground uppercase text-[10px] tracking-wider">Signal</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground uppercase text-[10px] tracking-wider hidden md:table-cell">Confidence</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground uppercase text-[10px] tracking-wider hidden lg:table-cell">Volume</th>
              </tr>
            </thead>
            <tbody>
              {filteredSignals.length > 0 ? (
                filteredSignals.map((s) => (
                  <tr key={s.symbol} className="border-b border-border last:border-0 hover:bg-accent/40 transition-colors">
                    <td className="px-4 py-3">
                      <Link to={`/stock/${s.symbol}`} className="font-bold text-foreground hover:text-primary transition-colors flex flex-col">
                        {s.symbol}
                        <span className="text-[10px] font-normal text-muted-foreground truncate max-w-[120px]">{s.name}</span>
                      </Link>
                    </td>
                    <td className="text-right px-4 py-3 font-mono font-medium hidden sm:table-cell">{formatCurrency(s.price)}</td>
                    <td className={`text-right px-4 py-3 font-mono font-medium ${s.change >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
                      {s.change >= 0 ? '+' : ''}{formatPercent(s.changePercent)}
                    </td>
                    <td className="text-center px-4 py-3"><SignalBadge signal={s.signal} /></td>
                    <td className="text-right px-4 py-3 hidden md:table-cell">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                          <div className={`h-full rounded-full ${s.confidence > 0.7 ? 'bg-signal-buy' : 'bg-primary'}`} style={{ width: `${s.confidence * 100}%` }} />
                        </div>
                        <span className="text-xs text-muted-foreground tabular-nums">{typeof s.confidence === "number" ? (s.confidence * 100).toFixed(0) : "0"}%</span>
                      </div>
                    </td>
                    <td className="text-right px-4 py-3 font-mono text-muted-foreground hidden lg:table-cell">{formatLargeNumber(s.volume)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-muted-foreground italic">
                    No signals found matching your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Movers Section */}
      {!searchResults && (
        <div className="grid md:grid-cols-2 gap-4 animate-in fade-in duration-500">
          <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-border bg-signal-buy/5">
              <h3 className="font-semibold text-signal-buy flex items-center gap-2 tracking-tight"><TrendingUp className="h-4 w-4" /> Market Gainers</h3>
            </div>
            <div className="divide-y divide-border">
              {market.topGainers.slice(0, 5).map(s => (
                <Link key={s.symbol} to={`/stock/${s.symbol}`} className="flex items-center justify-between px-4 py-3 hover:bg-accent/40 transition-colors">
                  <span className="font-bold text-sm text-foreground">{s.symbol}</span>
                  <span className="text-sm font-mono font-bold text-signal-buy">{formatPercent(s.changePercent)}</span>
                </Link>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-border bg-signal-sell/5">
              <h3 className="font-semibold text-signal-sell flex items-center gap-2 tracking-tight"><TrendingDown className="h-4 w-4" /> Market Losers</h3>
            </div>
            <div className="divide-y divide-border">
              {market.topLosers.slice(0, 5).map(s => (
                <Link key={s.symbol} to={`/stock/${s.symbol}`} className="flex items-center justify-between px-4 py-3 hover:bg-accent/40 transition-colors">
                  <span className="font-bold text-sm text-foreground">{s.symbol}</span>
                  <span className="text-sm font-mono font-bold text-signal-sell">{formatPercent(s.changePercent)}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(Dashboard);
