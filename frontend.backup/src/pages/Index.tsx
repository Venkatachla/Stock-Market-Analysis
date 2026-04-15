import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { formatCurrency } from "@/lib/formatters";
import { RefreshCw } from "lucide-react";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

type MarketCondition = "Bullish" | "Bearish" | "Sideways";
type ExecutionMode = "paper" | "live";
type DecisionStatus = "PENDING" | "EXECUTED" | "SKIPPED";

interface BullStock {
  symbol: string;
  probability_up: number;
  prob_up: number;
  prob_down: number;
  confidence_score: number;
  confidence: number;
  signal: string;
  regime: string;
  sentiment_score: number;
  latest_price: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  position_size: number;
  trade_validity: boolean;
  date: string;
}

const normalizeCondition = (input: unknown): MarketCondition => {
  const val = String(input ?? "").toLowerCase();
  if (val.includes("bull")) return "Bullish";
  if (val.includes("bear")) return "Bearish";
  return "Sideways";
};

const rrValue = (row: BullStock): number => {
  const entry = row.entry_price || row.latest_price || 0;
  const sl = row.stop_loss || (entry * 0.98);
  const tp = row.take_profit || (entry * 1.03);
  const risk = Math.abs(entry - sl);
  if (risk <= 0) return 0;
  return Math.abs(tp - entry) / risk;
};

const stockKey = (row: BullStock): string => String(row.symbol || "").toUpperCase();

const signalBadgeClass = (signal: string): string => {
  const s = String(signal || "").toUpperCase();
  if (s.includes("BUY")) return "badge-bullish";
  if (s.includes("SELL")) return "badge-bearish";
  return "badge-neutral";
};

const Index = () => {
  const [bullStocks, setBullStocks] = useState<BullStock[]>([]);
  const [selectedStock, setSelectedStock] = useState<BullStock | null>(null);
  const [marketCondition, setMarketCondition] = useState<MarketCondition>("Sideways");
  const [executionMode, setExecutionMode] = useState<ExecutionMode>("paper");
  const [decisionMap, setDecisionMap] = useState<Record<string, DecisionStatus>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchData = async (manual = false) => {
    try {
      if (manual) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const [bullRes, regimeRes] = await Promise.allSettled([
        axios.get(`${API_URL}/trade-now/bull-stocks`, { params: { limit: 80 } }),
        axios.get(`${API_URL}/regime`),
      ]);

      let rows: BullStock[] = [];
      if (bullRes.status === "fulfilled" && Array.isArray(bullRes.value.data)) {
        rows = bullRes.value.data as BullStock[];
      }

      // Fallback: if bull endpoint is empty or unavailable, show strongest directional candidates.
      if (!rows.length) {
        try {
          const predRes = await axios.get(`${API_URL}/predictions`, { params: { top_n: 80 } });
          const predRows = Array.isArray(predRes.data) ? (predRes.data as BullStock[]) : [];
          rows = [...predRows]
            .sort((a, b) => (b.prob_up ?? b.probability_up ?? 0) - (a.prob_up ?? a.probability_up ?? 0))
            .slice(0, 20);
        } catch {
          rows = [];
        }
      }

      setBullStocks(rows);
      setSelectedStock((prev) => {
        if (!rows.length) return null;
        if (!prev) return rows[0];
        const found = rows.find((r) => r.symbol === prev.symbol);
        return found ?? rows[0];
      });
      if (regimeRes.status === "fulfilled") {
        setMarketCondition(normalizeCondition(regimeRes.value.data?.regime ?? regimeRes.value.data));
      }
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error loading TRADE NOW stocks:", error);
      setBullStocks([]);
      setSelectedStock(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData(false);
  }, []);

  const tradingAllowed = marketCondition !== "Bearish" && bullStocks.length > 0;

  const handleDecision = async (stock: BullStock, action: DecisionStatus) => {
    const key = stockKey(stock);
    setDecisionMap((prev) => ({ ...prev, [key]: action }));

    try {
      if (action === "SKIPPED") {
        await axios.post(`${API_URL}/trade/reject`, { symbol: stock.symbol, timestamp: new Date().toISOString() });
      }

      if (action === "EXECUTED") {
        await axios.post(`${API_URL}/trade/execute`, {
          symbol: stock.symbol,
          mode: executionMode,
          signal_type: stock.signal,
          entry_price: stock.entry_price,
          stop_loss: stock.stop_loss,
          take_profit: stock.take_profit,
        });
      }
    } catch {
      // Keep local state when backend execute endpoint is unavailable.
    }
  };

  const sortedStocks = useMemo(() => {
    return [...bullStocks].sort((a, b) => b.confidence_score - a.confidence_score);
  }, [bullStocks]);

  const marketBannerClass =
    marketCondition === "Bullish"
      ? "bg-green-500/15 border-green-500/40 text-green-300"
      : marketCondition === "Bearish"
        ? "bg-red-500/15 border-red-500/40 text-red-300"
        : "bg-yellow-500/15 border-yellow-500/40 text-yellow-300";

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1>TRADE NOW</h1>
            <p className="text-xs text-muted-foreground mt-1">Updated: {lastUpdated || "--"}</p>
          </div>
          <button
            onClick={() => fetchData(true)}
            disabled={loading || refreshing}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium bg-accent/60 border border-border rounded-md hover:bg-accent disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        <div className={`rounded-xl border p-5 ${marketBannerClass}`}>
          <p className="text-xs uppercase tracking-wide opacity-80">Market Status</p>
          <p className="text-3xl font-bold mt-1">{marketCondition}</p>
        </div>

        <div className={`rounded-xl border p-5 ${tradingAllowed ? "border-green-500/40 bg-green-500/10" : "border-red-500/40 bg-red-500/10"}`}>
          <p className="text-xs uppercase tracking-wide opacity-80">System Status</p>
          <p className="text-2xl font-bold mt-1">{tradingAllowed ? "Trading Allowed" : "No Trade Today"}</p>
          <div className="mt-3 inline-flex items-center gap-2 rounded-md border border-border/50 bg-black/20 px-2 py-1 text-xs">
            <span className="text-muted-foreground">Execution Mode</span>
            <button
              onClick={() => setExecutionMode("paper")}
              className={`px-2 py-1 rounded ${executionMode === "paper" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
            >
              Paper
            </button>
            <button
              onClick={() => setExecutionMode("live")}
              className={`px-2 py-1 rounded ${executionMode === "live" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
            >
              Live
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          <div className="xl:col-span-8 space-y-3">
            {sortedStocks.map((stock) => {
              const key = stockKey(stock);
              const decision = decisionMap[key] ?? "PENDING";
              const isSelected = selectedStock?.symbol === stock.symbol;

              return (
                <div
                  key={key}
                  onClick={() => setSelectedStock(stock)}
                  className={`rounded-xl border p-4 cursor-pointer transition-colors ${isSelected ? "border-primary/60 bg-primary/10" : "border-border/60 bg-card"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-lg font-bold">{stock.symbol}</p>
                    <span className={signalBadgeClass(stock.signal)}>{stock.signal || "HOLD"}</span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm mt-3">
                    <div>
                      <p className="text-muted-foreground text-xs">Entry</p>
                      <p className="font-mono-data">{formatCurrency(stock.entry_price)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">SL</p>
                      <p className="font-mono-data text-red-300">{formatCurrency(stock.stop_loss)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">TP</p>
                      <p className="font-mono-data text-green-300">{formatCurrency(stock.take_profit)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Confidence</p>
                      <p className="font-mono-data">{stock.confidence_score.toFixed(0)}%</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-3">
                    <p className="text-sm">Risk/Reward: <span className="font-semibold">1 : {rrValue(stock).toFixed(2)}</span></p>
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDecision(stock, "EXECUTED");
                        }}
                        className="rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-xs font-semibold hover:bg-primary/90"
                      >
                        EXECUTE
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDecision(stock, "SKIPPED");
                        }}
                        className="rounded-md border border-border px-3 py-1.5 text-xs font-semibold hover:bg-accent"
                      >
                        SKIP
                      </button>
                    </div>
                  </div>

                  {decision !== "PENDING" && <p className="text-xs text-muted-foreground mt-2">Status: {decision}</p>}
                </div>
              );
            })}

            {!loading && sortedStocks.length === 0 && (
              <div className="rounded-xl border border-border/60 bg-card p-6 text-center text-muted-foreground">
                No strict bullish stocks right now. Showing best available candidates when data is available.
              </div>
            )}
          </div>

          <div className="xl:col-span-4">
            <div className="rounded-xl border border-border/60 bg-card p-4 sticky top-4">
              <h3 className="text-sm font-semibold">Stock Details</h3>
              {selectedStock ? (
                <div className="space-y-2 mt-3 text-sm">
                  <div className="flex justify-between"><span className="text-muted-foreground">Symbol</span><span className="font-semibold">{selectedStock.symbol}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Signal</span><span className={signalBadgeClass(selectedStock.signal)}>{selectedStock.signal || "HOLD"}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Probability Up</span><span>{(selectedStock.prob_up * 100).toFixed(2)}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Confidence</span><span>{selectedStock.confidence_score.toFixed(2)}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Regime</span><span>{selectedStock.regime}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Sentiment</span><span>{(selectedStock.sentiment_score * 100).toFixed(1)}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Latest Price</span><span>{formatCurrency(selectedStock.latest_price)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Entry</span><span>{formatCurrency(selectedStock.entry_price)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Stop Loss</span><span className="text-red-300">{formatCurrency(selectedStock.stop_loss)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Take Profit</span><span className="text-green-300">{formatCurrency(selectedStock.take_profit)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Risk/Reward</span><span>1 : {rrValue(selectedStock).toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Position Size</span><span>{selectedStock.position_size}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Trade Valid</span><span>{selectedStock.trade_validity ? "Yes" : "No"}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Date</span><span>{selectedStock.date}</span></div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground mt-3">Select a stock card to see full details.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default Index;
