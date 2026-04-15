import { useEffect, useState, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";
import { ArrowUpRight, Search, SlidersHorizontal, Activity, BellRing, PieChart, ShieldCheck } from "lucide-react";
import { StockCard } from "@/components/StockCard";
import { useBulkSignals } from "@/hooks/useBulkSignals";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [universe, setUniverse] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [activeTab, setActiveTab] = useState("All Stocks");
  const [sortOption, setSortOption] = useState("AI Confidence");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const itemsPerPage = 20;

  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [portfolioAnalytics, setPortfolioAnalytics] = useState<any | null>(null);
  const [liveAlerts, setLiveAlerts] = useState<any[]>([]);
  const [chainStatus, setChainStatus] = useState<any | null>(null);
  const { fetchSignals, signals } = useBulkSignals();
  
  useEffect(() => {
    const w = JSON.parse(localStorage.getItem("risk_os_watchlist") || "[]");
    setWatchlist(w.map((item:any)=> typeof item === 'string' ? item : item.symbol));
  }, []);

  useEffect(() => {
    const loadInsights = async () => {
      try {
        const [portfolioRes, alertsRes, chainRes] = await Promise.all([
          axios.get(`${API_URL}/portfolio/analytics`),
          axios.get(`${API_URL}/alerts/live?timeframe=1d&min_confidence=75&limit=5`),
          axios.get(`${API_URL}/chain/status`),
        ]);
        setPortfolioAnalytics(portfolioRes.data ?? null);
        setLiveAlerts(Array.isArray(alertsRes.data?.alerts) ? alertsRes.data.alerts : []);
        setChainStatus(chainRes.data ?? null);
      } catch {
        setPortfolioAnalytics(null);
        setLiveAlerts([]);
        setChainStatus(null);
      }
    };
    loadInsights();
  }, []);

  const toggleWatchlist = (e: React.MouseEvent, symbol: string) => {
    e.preventDefault();
    let w = JSON.parse(localStorage.getItem("risk_os_watchlist") || "[]");
    w = w.map((item:any)=> typeof item === 'string' ? item : item.symbol);
    if (w.includes(symbol)) {
      w = w.filter((s: string) => s !== symbol);
    } else {
      w.push(symbol);
    }
    localStorage.setItem("risk_os_watchlist", JSON.stringify(w));
    setWatchlist(w);
  };

  // Debounced Search and Tab fetching 
  useEffect(() => {
    const loadData = async (isReset = true) => {
      try {
        if (isReset) {
            setLoading(true);
            setPage(0);
        } else {
            setLoadingMore(true);
        }

        const offset = isReset ? 0 : page * itemsPerPage;
        let endpoint = `${API_URL}/stocks?limit=${itemsPerPage}&offset=${offset}`;
        
        if (search.trim()) {
           endpoint = `${API_URL}/stocks/search?q=${search}&limit=${itemsPerPage}`;
          } else if (activeTab === "BUY") { 
             endpoint = `${API_URL}/stocks/top-bulls?limit=${itemsPerPage}`;
          } else if (activeTab === "SELL") {
             endpoint = `${API_URL}/stocks/top-bears?limit=${itemsPerPage}`;
        } else if (activeTab === "Losers") {
           endpoint = `${API_URL}/stocks/top-losers?limit=${itemsPerPage}`;
        } 
        
        // Watchlist handled slightly differently (client side filter on local storage, or a dedicated endpoint)
        // For simplicity, we just fetch universe if it's watchlist and filter client side if we don't have enough DB logic
        if (activeTab === "My Watchlist") {
             // For a real production app, we would send the watchlist array to the backend to get details. 
             // Just fetching it manually here:
             const wList = watchlist.slice(0, 50); // limit 50
             const res = await axios.get(`${API_URL}/stocks/search?q=watchlist_query_placeholder`); 
             // We'll fallback to a custom approach for watchlist
        }

        // Standard fetch
        if (activeTab !== "My Watchlist") {
          const res = await axios.get(endpoint);
          const freshData = res.data.data || [];
          setUniverse(prev => isReset ? freshData : [...prev, ...freshData]);
            if (freshData.length < itemsPerPage || search.trim() || activeTab === "Gainers" || activeTab === "Losers" || activeTab === "BUY" || activeTab === "SELL") {
              setHasMore(false);
          } else {
              setHasMore(true);
          }
        } else {
           // Basic watchlist mock load if nothing else 
           setUniverse(watchlist.map(sym => ({ symbol: sym, name: sym })));
           setHasMore(false);
        }

      } catch (err) {
        console.error("Dashboard failed to load", err);
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    };
    
    // Debounce search
    const timer = setTimeout(() => {
        loadData(true);
    }, 300);
    return () => clearTimeout(timer);
  }, [search, activeTab, watchlist.length]);

  const loadMore = () => {
    if (!loading && !loadingMore && hasMore) {
        setPage(p => p + 1);
    }
  };

  useEffect(() => {
      // Trigger load data append when page changes
      if (page > 0) {
        const offset = page * itemsPerPage;
        axios.get(`${API_URL}/stocks?limit=${itemsPerPage}&offset=${offset}`).then(res => {
            const arr = res.data.data || [];
            if (arr.length) {
                setUniverse(prev => [...prev, ...arr]);
            } else {
                setHasMore(false);
            }
        });
      }
  }, [page]);

  useEffect(() => {
    const q = search.trim();
    if (!q) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await axios.get(`${API_URL}/symbols/search?q=${encodeURIComponent(q)}&limit=10`);
        setSuggestions(Array.isArray(res.data) ? res.data : []);
        setShowSuggestions(true);
      } catch {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 120);

    return () => clearTimeout(timer);
  }, [search]);

  const filteredAndSortedStocks = useMemo(() => {
    let list = [...universe];
    
    if (sortOption === "AI Confidence") {
       list = list.sort((a,b) => {
          const pb = signals[b.symbol]?.prob || 0;
          const pa = signals[a.symbol]?.prob || 0;
          return pb - pa;
       });
    } else if (sortOption === "Price") {
       list = list.sort((a,b) => (b.strike || 0) - (a.strike || 0));
    }
    return list;
  }, [universe, sortOption, signals]);

    const requestSignals = useCallback((symbolsToFetch: string[]) => {
      fetchSignals(symbolsToFetch);
    }, [fetchSignals]);

  const visibleItems = filteredAndSortedStocks;

  useEffect(() => {
     if (visibleItems.length > 0) {
        requestSignals(visibleItems.map(i => i.symbol));
     }
  }, [visibleItems, requestSignals]);

  return (
    <AppLayout>
      <div className="space-y-8 max-w-7xl mx-auto pb-24">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Market Discover</h1>
            <p className="text-muted-foreground text-sm mt-1">24/7 Live Analytics over 200k+ assets</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-xl border border-border/50 bg-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <PieChart className="h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Portfolio Analytics</p>
            </div>
            {portfolioAnalytics ? (
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-muted/30 p-3">
                  <p className="text-xs text-muted-foreground">Portfolio Value</p>
                  <p className="font-semibold">₹{Number(portfolioAnalytics.portfolio_value || 0).toFixed(2)}</p>
                </div>
                <div className="rounded-lg bg-muted/30 p-3">
                  <p className="text-xs text-muted-foreground">Unrealized PnL</p>
                  <p className={`font-semibold ${Number(portfolioAnalytics.unrealized_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    ₹{Number(portfolioAnalytics.unrealized_pnl || 0).toFixed(2)}
                  </p>
                </div>
                <div className="rounded-lg bg-muted/30 p-3">
                  <p className="text-xs text-muted-foreground">Day Change</p>
                  <p className={`font-semibold ${Number(portfolioAnalytics.day_change || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {Number(portfolioAnalytics.day_change_pct || 0).toFixed(2)}%
                  </p>
                </div>
                <div className="rounded-lg bg-muted/30 p-3">
                  <p className="text-xs text-muted-foreground">Diversification</p>
                  <p className="font-semibold">{Number(portfolioAnalytics.diversification_score || 0).toFixed(1)} / 100</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Portfolio analytics unavailable.</p>
            )}
          </div>

          <div className="rounded-xl border border-border/50 bg-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <BellRing className="h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Live Strong-Signal Alerts</p>
            </div>
            {liveAlerts.length === 0 ? (
              <p className="text-sm text-muted-foreground">No strong alerts right now. Check again after market moves.</p>
            ) : (
              <div className="space-y-2">
                {liveAlerts.map((a, idx) => (
                  <Link
                    to={`/stock/${a.symbol}`}
                    key={`${a.symbol}-${idx}`}
                    className="block rounded-lg border border-border/40 p-3 hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <p className="font-semibold">{a.symbol}</p>
                      <p className={`${String(a.signal).toUpperCase() === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>{a.signal}</p>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Conf {Number(a.confidence || a.confidence_score || 0).toFixed(1)}% • Entry ₹{Number(a.price || a.entry_price || 0).toFixed(2)}</p>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card p-4">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Blockchain Proof Layer</p>
            </div>
            <div className="text-xs text-muted-foreground">
              {chainStatus ? `${Number(chainStatus.block_count || 0)} blocks • ${Number(chainStatus.anchored_ratio || 0).toFixed(1)}% anchored` : "Status unavailable"}
            </div>
          </div>

          {chainStatus ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-emerald-400 mb-2">Implemented</p>
                <div className="space-y-2">
                  {(Array.isArray(chainStatus.implemented) ? chainStatus.implemented : []).map((item: string, i: number) => (
                    <div key={`impl-${i}`} className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-sm">
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-amber-400 mb-2">Planned Next</p>
                <div className="space-y-2">
                  {(Array.isArray(chainStatus.planned) ? chainStatus.planned : []).map((item: string, i: number) => (
                    <div key={`plan-${i}`} className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-sm">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Blockchain section could not load. Start backend and refresh.</p>
          )}
        </div>

        <div>
           {/* Section Top Controls */}
           <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 mb-4">
             <div className="flex space-x-1 border-b border-border/40 overflow-x-auto no-scrollbar pb-1">
               {["All Stocks", "BUY", "SELL", "My Watchlist"].map(tab => (
                 <button
                   key={tab}
                   onClick={() => setActiveTab(tab)}
                   className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${activeTab === tab ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground"}`}
                 >
                   {tab}
                 </button>
               ))}
             </div>

             <div className="flex items-center gap-3">
               <div className="relative w-full md:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input 
                    type="text" 
                    placeholder="Search universe (200k+)" 
                    className="w-full bg-muted/50 border border-border/50 rounded-lg pl-9 pr-4 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    onFocus={() => setShowSuggestions(suggestions.length > 0)}
                  />
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute z-30 mt-1 w-full rounded-lg border border-border/60 bg-card shadow-xl max-h-72 overflow-auto">
                      {suggestions.map((item) => (
                        <button
                          key={item.symbol}
                          onClick={() => {
                            setSearch(item.symbol);
                            setShowSuggestions(false);
                          }}
                          className="w-full text-left px-3 py-2 hover:bg-muted/60 border-b last:border-b-0 border-border/30"
                        >
                          <div className="text-sm font-semibold">{item.symbol}</div>
                          <div className="text-xs text-muted-foreground truncate">{item.name || item.symbol}</div>
                        </button>
                      ))}
                    </div>
                  )}
               </div>
             </div>
           </div>

           <div className="bg-card border border-border/50 rounded-xl overflow-hidden shadow-sm">
              <div className="grid grid-cols-12 gap-2 md:gap-4 px-4 md:px-6 py-3 border-b border-border/50 text-xs font-medium text-muted-foreground uppercase tracking-wider bg-muted/20">
                 <div className="col-span-11 md:col-span-7">Universe Match (Name & Price Mocked for Speed)</div>
                 <div className="hidden md:block md:col-span-4 pl-4 text-center">Chart 30D</div>
                 <div className="col-span-1 md:col-span-1 text-right">Act</div>
              </div>
              
              <div className="divide-y divide-border/30">
                 {loading ? (
                    <div className="flex items-center justify-center p-8 text-muted-foreground text-sm flex-col gap-3 py-24">
                      <Activity className="h-6 w-6 animate-pulse" />
                      Loading 200k+ Market Universe...
                    </div>
                 ) : filteredAndSortedStocks.length === 0 ? (
                    <div className="p-8 text-center text-muted-foreground">No matches found.</div>
                 ) : (
                    <>
                      {visibleItems.map((stock, i) => {
                        const sym = String(stock.symbol || `UNKNOWN-${i}`);
                        return (
                        <StockCard
                          key={`${sym}-${i}`}
                          symbol={sym}
                            price={stock.price || stock.strike || 100 + (sym.length * 10)}
                            change={stock.change !== undefined ? stock.change : ((sym.length % 5) - 2)}
                            isWatchlisted={watchlist.includes(sym)}
                            onToggleWatchlist={toggleWatchlist}
                            initialSignal={stock.initialSignal || signals[sym]?.signal}
                            initialProb={stock.initialProb !== undefined ? stock.initialProb : (signals[sym]?.prob ? signals[sym].prob / 100 : undefined)}
                        />
                      )})}
                      {hasMore && (
                        <div className="p-6 flex justify-center">
                          <button 
                            onClick={loadMore}
                            disabled={loadingMore}
                            className="px-6 py-2 bg-muted hover:bg-muted/80 text-foreground text-sm font-medium rounded-full transition-colors disabled:opacity-50"
                          >
                            {loadingMore ? 'Loading...' : 'Load More Markets'}
                          </button>
                        </div>
                      )}
                    </>
                 )}
              </div>
           </div>
        </div>
      </div>
    </AppLayout>
  );
}
