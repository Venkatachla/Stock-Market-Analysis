import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { formatCurrency } from "@/lib/formatters";
import { RefreshCw } from "lucide-react";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
const SETTINGS_KEY = "trading_controls_v1";

interface Signal {
  id?: string;
  symbol: string;
  signal_type: string;
  confidence_score?: number;
  confidence?: number;
  entry_price?: number;
  stop_loss?: number;
  take_profit?: number;
  latest_price?: number;
  price?: number;
  timestamp: string;
}

interface Controls {
  confidenceThreshold: number;
  maxTradesPerDay: number;
}

const defaultControls: Controls = {
  confidenceThreshold: 70,
  maxTradesPerDay: 5,
};

const getControls = (): Controls => {
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (!raw) return defaultControls;

  try {
    const parsed = JSON.parse(raw);
    return {
      confidenceThreshold: Number(parsed.confidenceThreshold ?? defaultControls.confidenceThreshold),
      maxTradesPerDay: Number(parsed.maxTradesPerDay ?? defaultControls.maxTradesPerDay),
    };
  } catch {
    return defaultControls;
  }
};

const confidenceValue = (row: Signal): number => {
  if (typeof row.confidence_score === "number") return row.confidence_score;
  return (row.confidence ?? 0) * 100;
};

const rrValue = (row: Signal): number => {
  const entry = row.entry_price ?? row.latest_price ?? row.price ?? 0;
  const sl = row.stop_loss ?? entry * 0.98;
  const tp = row.take_profit ?? entry * 1.03;
  const risk = Math.abs(entry - sl);
  if (risk <= 0) return 0;
  return Math.abs(tp - entry) / risk;
};

const Signals = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchSignals = async (manual = false) => {
    try {
      if (manual) setRefreshing(true);
      else setLoading(true);

      const response = await axios.get(`${API_URL}/signals`);
      const rows = Array.isArray(response.data) ? response.data : response.data?.signals || [];
      setSignals(rows);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error fetching signals:", error);
      setSignals([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSignals(false);
  }, []);

  const controls = getControls();

  const topSignals = useMemo(() => {
    const limit = Math.max(1, Math.min(5, controls.maxTradesPerDay));
    return [...signals]
      .filter((s) => {
        const t = String(s.signal_type).toUpperCase();
        return (t === "BUY" || t === "SELL") && confidenceValue(s) >= controls.confidenceThreshold;
      })
      .sort((a, b) => confidenceValue(b) - confidenceValue(a))
      .slice(0, limit);
  }, [controls.confidenceThreshold, controls.maxTradesPerDay, signals]);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1>SIGNALS</h1>
            <p className="text-sm text-muted-foreground mt-1">Top opportunities only</p>
            <p className="text-xs text-muted-foreground mt-1">Updated: {lastUpdated || "--"}</p>
          </div>
          <button
            onClick={() => fetchSignals(true)}
            disabled={loading || refreshing}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium bg-accent/60 border border-border rounded-md hover:bg-accent disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        <div className="space-y-3">
          {topSignals.map((signal, index) => {
            const entry = signal.entry_price ?? signal.latest_price ?? signal.price ?? 0;
            const sl = signal.stop_loss ?? entry * 0.98;
            const tp = signal.take_profit ?? entry * 1.03;
            const isBest = index === 0;

            return (
              <div
                key={`${signal.symbol}-${signal.timestamp}-${signal.id ?? ""}`}
                className={`rounded-xl border p-4 ${isBest ? "border-green-500/50 bg-green-500/10" : "border-border/60 bg-card"}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold ${isBest ? "bg-green-500/20 text-green-300" : "bg-muted text-foreground"}`}>
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-semibold text-lg">{signal.symbol}</p>
                      {isBest && <p className="text-xs text-green-300">Best Trade</p>}
                    </div>
                  </div>
                  <span className={String(signal.signal_type).toUpperCase() === "BUY" ? "badge-bullish" : "badge-bearish"}>
                    {String(signal.signal_type).toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Entry</p>
                    <p className="font-mono-data">{formatCurrency(entry)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">SL</p>
                    <p className="font-mono-data text-red-300">{formatCurrency(sl)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">TP</p>
                    <p className="font-mono-data text-green-300">{formatCurrency(tp)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Confidence</p>
                    <p className="font-mono-data">{confidenceValue(signal).toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Risk/Reward</p>
                    <p className="font-mono-data">1 : {rrValue(signal).toFixed(2)}</p>
                  </div>
                </div>
              </div>
            );
          })}

          {!loading && topSignals.length === 0 && (
            <div className="rounded-xl border border-border/60 bg-card p-6 text-center text-muted-foreground">
              No signals passed auto-filter ({controls.confidenceThreshold}% threshold).
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default Signals;
