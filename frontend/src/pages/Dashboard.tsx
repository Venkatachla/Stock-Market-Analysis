import React, { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { fetchMarketOverview, fetchStockSignals } from '@/services/api';
import { mockMarketOverview, mockSignals } from '@/utils/mockData';
import { formatCurrency, formatPercent, formatLargeNumber } from '@/utils/format';
import { LoadingState, ErrorState, MetricCard, SignalBadge } from '@/components/common/StatusComponents';
import { TrendingUp, TrendingDown, BarChart3, Activity, Search, Sparkles } from 'lucide-react';
import type { StockSignal, MarketOverview } from '@/services/api';

const Dashboard: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [promptResults, setPromptResults] = useState<any>(null);
  const [promptLoading, setPromptLoading] = useState(false);
  const [pollInfo, setPollInfo] = useState<{lastUpdate: string, pollCount: number}>({lastUpdate: '', pollCount: 0});

  const pollMarketData = useCallback(() => {
    console.log('📊 Fetching market data...');
    setPollInfo(prev => ({
      lastUpdate: new Date().toLocaleTimeString(),
      pollCount: prev.pollCount + 1
    }));
    return fetchMarketOverview();
  }, []);

  const pollSignalsData = useCallback(() => {
    console.log('🎯 Fetching stock signals...');
    setPollInfo(prev => ({
      lastUpdate: new Date().toLocaleTimeString(),
      pollCount: prev.pollCount + 1
    }));
    return fetchStockSignals();
  }, []);

  // 🔄 REAL-TIME MARKET DATA - Poll every 10 seconds (was 30s)
  const { data: marketData, loading: mLoading, error: mError, retry: mRetry } = usePolling<MarketOverview>(
    pollMarketData,
    10000  // ✅ Changed from 30000 to 10000 (10 seconds) for real-time updates
  );
  
  // 🔄 REAL-TIME STOCK SIGNALS - Poll every 8 seconds (was 30s)
  const { data: signalsData, loading: sLoading, error: sError, retry: sRetry } = usePolling<StockSignal[]>(
    pollSignalsData,
    8000  // ✅ Changed from 30000 to 8000 (8 seconds) for real-time dynamic predictions
  );

  // Use real data, no fallback to mock
  const market = marketData ?? { indices: [], topGainers: [], topLosers: [], mostActive: [] };
  const signals = signalsData ?? [];

  const stats = useMemo(() => {
    const buyCount = signals.filter(s => s.signal_type === 'BUY' || s.signal === 'BUY').length;
    const sellCount = signals.filter(s => s.signal_type === 'SELL' || s.signal === 'SELL').length;
    return { buyCount, sellCount, total: signals.length };
  }, [signals]);

  const handlePromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    setPromptLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: prompt, limit: 10 })
      });
      const data = await response.json();
      setPromptResults(data);
    } catch (error) {
      console.error('Prompt error:', error);
      // Fallback: search locally in signals
      const q = prompt.toLowerCase();
      const results = signals.filter(s => 
        s.symbol.toLowerCase().includes(q) || 
        (s.name && s.name.toLowerCase().includes(q)) || 
        (q.includes('buy') && s.signal === 'BUY') ||
        (q.includes('sell') && s.signal === 'SELL')
      );
      setPromptResults({ query: prompt, results, message: `Found ${results.length} matching signals` });
    } finally {
      setPromptLoading(false);
    }
  };

  if (mLoading && sLoading) return <LoadingState message="Loading dashboard..." />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Market Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Real-time market overview and signals</p>
      </div>

      {/* Prompt Input */}
      <form onSubmit={handlePromptSubmit} className="space-y-2">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
          <input
            id="dashboard-search"
            name="search"
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask anything... 'Show bullish tech stocks', 'High confidence signals', 'My portfolio', etc."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-border bg-card text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            type="submit"
            disabled={promptLoading || !prompt.trim()}
            className="absolute right-2 top-2 p-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            aria-label="Search signals"
          >
            <Sparkles className="h-5 w-5" />
          </button>
        </div>
        <div className="text-xs text-muted-foreground">
          💡 Try: "buy signals", "sell signals", "high confidence", "RELIANCE", "portfolio", etc.
        </div>
      </form>

      {/* Prompt Results */}
      {promptResults && (
        <div className="rounded-lg border border-blue-500/50 bg-blue-500/10 p-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-sm font-medium text-foreground">Search Results</p>
              <p className="text-xs text-muted-foreground mt-1">Query: <span className="font-mono text-primary">"{promptResults.query}"</span></p>
              <p className="text-xs text-muted-foreground">{promptResults.message || `Found ${promptResults.results?.length || 0} results`}</p>
            </div>
            <button
              onClick={() => setPromptResults(null)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              ✕
            </button>
          </div>
          {promptResults.results && Array.isArray(promptResults.results) && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {promptResults.results.map((r: any, i: number) => (
                <div key={i} className="rounded bg-card border border-border p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-foreground">{r.symbol}</span>
                    <span className={`text-xs px-2 py-1 rounded ${r.signal_type === 'BUY' ? 'bg-signal-buy/20 text-signal-buy' : 'bg-signal-sell/20 text-signal-sell'}`}>
                      {r.signal_type}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">{r.reason}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Confidence:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${r.confidence * 100}%` }} />
                      </div>
                      <span className="text-xs font-mono text-primary">{(r.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

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
