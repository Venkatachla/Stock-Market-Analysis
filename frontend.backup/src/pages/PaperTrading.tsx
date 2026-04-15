import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { formatCurrency } from "@/lib/formatters";
import { RefreshCw } from "lucide-react";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface PaperTrade {
  id?: string;
  symbol: string;
  entry_price: number;
  exit_price?: number | null;
  pnl?: number;
  status?: string;
  stop_loss?: number;
  take_profit?: number;
  timestamp?: string;
}

const tradeKey = (trade: PaperTrade, idx: number): string => `${trade.symbol}-${trade.timestamp ?? idx}-${trade.id ?? ""}`;

const PaperTrading = () => {
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchOpenTrades = async (manual = false) => {
    try {
      if (manual) setRefreshing(true);
      else setLoading(true);

      const response = await axios.get(`${API_URL}/paper-trades`);
      const rows = Array.isArray(response.data) ? response.data : response.data?.trades || [];
      setTrades(rows);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error loading active trades:", error);
      setTrades([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOpenTrades(false);
  }, []);

  const openTrades = useMemo(
    () => trades.filter((t) => String(t.status ?? "OPEN").toUpperCase() === "OPEN"),
    [trades]
  );

  const currentPnl = openTrades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);

  const closeTrade = async (trade: PaperTrade, idx: number) => {
    const key = tradeKey(trade, idx);
    try {
      await axios.post(`${API_URL}/trade/close`, { symbol: trade.symbol, id: trade.id, timestamp: trade.timestamp });
    } catch {
      // Continue with local close fallback.
    }

    setTrades((prev) => prev.filter((t, i) => tradeKey(t, i) !== key));
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1>ACTIVE TRADES</h1>
            <p className="text-xs text-muted-foreground mt-1">Updated: {lastUpdated || "--"}</p>
          </div>
          <button
            onClick={() => fetchOpenTrades(true)}
            disabled={loading || refreshing}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium bg-accent/60 border border-border rounded-md hover:bg-accent disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        <div className={`rounded-xl border p-5 ${currentPnl >= 0 ? "border-green-500/40 bg-green-500/10" : "border-red-500/40 bg-red-500/10"}`}>
          <p className="text-xs uppercase tracking-wide opacity-80">Current Open PnL</p>
          <p className="text-4xl font-bold mt-1">{formatCurrency(currentPnl)}</p>
        </div>

        <div className="space-y-3">
          {openTrades.map((trade, idx) => {
            const entry = trade.entry_price;
            const current = trade.exit_price ?? trade.entry_price;
            const sl = trade.stop_loss ?? entry * 0.98;
            const tp = trade.take_profit ?? entry * 1.03;

            return (
              <div key={tradeKey(trade, idx)} className="rounded-xl border border-border/60 bg-card p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xl font-semibold">{trade.symbol}</p>
                  <button
                    onClick={() => closeTrade(trade, idx)}
                    className="rounded-md border border-red-500/30 bg-red-500/15 px-3 py-1.5 text-xs font-semibold text-red-300"
                  >
                    Close Trade
                  </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Entry</p>
                    <p className="font-mono-data">{formatCurrency(entry)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Current</p>
                    <p className="font-mono-data">{formatCurrency(current)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">PnL</p>
                    <p className={`font-mono-data ${(trade.pnl ?? 0) >= 0 ? "text-green-300" : "text-red-300"}`}>{formatCurrency(trade.pnl ?? 0)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">SL</p>
                    <p className="font-mono-data text-red-300">{formatCurrency(sl)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">TP</p>
                    <p className="font-mono-data text-green-300">{formatCurrency(tp)}</p>
                  </div>
                </div>
              </div>
            );
          })}

          {!loading && openTrades.length === 0 && (
            <div className="rounded-xl border border-border/60 bg-card p-6 text-center text-muted-foreground">
              No open trades right now.
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default PaperTrading;
