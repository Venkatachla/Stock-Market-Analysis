import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { formatCurrency } from "@/lib/formatters";
import { Search, RefreshCw } from "lucide-react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Prediction {
  symbol: string;
  prob_up?: number;
  prob_down?: number;
  confidence_score?: number;
  confidence?: number;
  signal: string;
  regime?: string;
  sentiment_score?: number;
  latest_price: number;
  entry_price?: number;
  stop_loss?: number;
  take_profit?: number;
  trade_validity?: boolean;
}

const StockPrediction = () => {
  const navigate = useNavigate();
  const [selectedSymbol, setSelectedSymbol] = useState("RELIANCE");
  const [searchInput, setSearchInput] = useState("");
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const confidence = (row: Prediction) => {
    if (typeof row.confidence_score === "number") return row.confidence_score;
    return (row.confidence ?? 0) * 100;
  };

  const normalizeSignal = (row: Prediction): "BUY" | "SELL" | "NO TRADE" => {
    const val = String(row.signal ?? "").toUpperCase();
    if (val === "BUY" || val === "SELL") return val;
    return "NO TRADE";
  };

  const qualityTag = (row: Prediction): "Strong signal" | "Weak signal" | "Avoid" => {
    const conf = confidence(row);
    const signal = normalizeSignal(row);
    if (signal !== "NO TRADE" && conf >= 75) return "Strong signal";
    if (signal !== "NO TRADE" && conf >= 55) return "Weak signal";
    return "Avoid";
  };

  const rr = (row: Prediction): number => {
    const entry = row.entry_price ?? row.latest_price;
    const stop = row.stop_loss ?? entry * 0.98;
    const target = row.take_profit ?? entry * 1.03;
    const signal = normalizeSignal(row);
    const risk = Math.abs(entry - stop);
    if (risk <= 0) return 0;
    const reward = signal === "SELL" ? Math.abs(entry - stop) : Math.abs(target - entry);
    return reward / risk;
  };

  const fetchPrediction = async () => {
    try {
      setLoading(true);
      const [singleRes, listRes] = await Promise.all([
        axios.get(`${API_URL}/prediction/${selectedSymbol}`),
        axios.get(`${API_URL}/predictions`),
      ]);
      setPrediction(singleRes.data ?? null);
      setPredictions(Array.isArray(listRes.data) ? listRes.data : []);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error fetching prediction:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, [selectedSymbol]);

  const availableSymbols = useMemo(() => {
    if (predictions.length) {
      return predictions.map((p) => p.symbol);
    }
    return ["RELIANCE", "TCS", "INFY", "WIPRO", "HDFC", "MARUTI", "BAJAJ-AUTO", "ANANTRAJ"];
  }, [predictions]);

  const handleSearch = () => {
    const sym = searchInput.toUpperCase().trim();
    if (availableSymbols.includes(sym)) {
      setSelectedSymbol(sym);
    }
    setSearchInput("");
  };

  const selectedRow = useMemo(() => {
    const fromList = predictions.find((p) => p.symbol === selectedSymbol);
    return fromList ?? prediction;
  }, [predictions, prediction, selectedSymbol]);

  const trendDirection = useMemo(() => {
    if (!selectedRow) return "Unknown";
    const regime = String(selectedRow.regime ?? "").toLowerCase();
    if (regime.includes("bull")) return "Uptrend";
    if (regime.includes("bear")) return "Downtrend";
    const signal = normalizeSignal(selectedRow);
    if (signal === "BUY") return "Uptrend";
    if (signal === "SELL") return "Downtrend";
    return "Sideways";
  }, [selectedRow]);

  const volumeSpike = useMemo(() => {
    if (!selectedRow) return false;
    return confidence(selectedRow) >= 72;
  }, [selectedRow]);

  const breakoutDetected = useMemo(() => {
    if (!selectedRow) return false;
    const signal = normalizeSignal(selectedRow);
    return signal !== "NO TRADE" && (selectedRow.trade_validity ?? false);
  }, [selectedRow]);

  const tagClass = (tag: "Strong signal" | "Weak signal" | "Avoid") => {
    if (tag === "Strong signal") return "bg-green-500/15 text-green-300 border border-green-500/30";
    if (tag === "Weak signal") return "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30";
    return "bg-red-500/15 text-red-300 border border-red-500/30";
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1>Stock Prediction</h1>
            <p className="text-sm text-muted-foreground mt-1">Actionable trade setup with confidence and reason</p>
            {lastUpdated && <p className="text-xs text-muted-foreground mt-1">Last updated: {lastUpdated}</p>}
          </div>
          <button
            onClick={fetchPrediction}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium bg-accent/60 border border-border rounded-md hover:bg-accent disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-4 space-y-4">
            <div className="stat-card">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Search Symbol</label>
              <div className="flex gap-2 mt-2">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="RELIANCE, TCS..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    className="w-full h-8 pl-8 pr-3 text-sm bg-black border border-border rounded-md text-white placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
                <button
                  onClick={handleSearch}
                  className="px-3 h-8 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  Go
                </button>
              </div>
            </div>

            {selectedRow && (
              <>
                <div className="stat-card">
                  <h2 className="text-2xl font-bold">{selectedRow.symbol}</h2>
                  <p className="text-lg font-semibold text-teal-400 mt-1">{formatCurrency(selectedRow.latest_price)}</p>
                  <button
                    onClick={() => navigate(`/chart/${encodeURIComponent(selectedRow.symbol)}`)}
                    className="mt-2 px-3 py-1.5 rounded-md bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
                  >
                    Open Full Chart
                  </button>

                  <div className="mt-3 flex items-center gap-2 flex-wrap">
                    <span className={normalizeSignal(selectedRow) === "BUY" ? "badge-bullish" : normalizeSignal(selectedRow) === "SELL" ? "badge-bearish" : "badge-neutral"}>
                      Signal: {normalizeSignal(selectedRow)}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${tagClass(qualityTag(selectedRow))}`}>
                      {qualityTag(selectedRow)}
                    </span>
                  </div>

                  <div className="mt-4 space-y-2 text-xs border-t border-border/50 pt-3">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Confidence</span>
                      <span className="font-semibold">{confidence(selectedRow).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Entry</span>
                      <span className="font-semibold">{formatCurrency(selectedRow.entry_price ?? selectedRow.latest_price)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Stop Loss</span>
                      <span className="font-semibold text-red-300">{formatCurrency(selectedRow.stop_loss ?? (selectedRow.latest_price * 0.98))}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Take Profit</span>
                      <span className="font-semibold text-green-300">{formatCurrency(selectedRow.take_profit ?? (selectedRow.latest_price * 1.03))}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Risk / Reward</span>
                      <span className="font-semibold">1 : {rr(selectedRow).toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <div className="stat-card">
                  <h3 className="text-sm font-semibold mb-3">Why this trade?</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between rounded-md border border-border/50 px-3 py-2">
                      <span className="text-muted-foreground">Trend Direction</span>
                      <span className="font-semibold">{trendDirection}</span>
                    </div>
                    <div className="flex items-center justify-between rounded-md border border-border/50 px-3 py-2">
                      <span className="text-muted-foreground">Volume Spike</span>
                      <span className={volumeSpike ? "text-green-300 font-semibold" : "text-yellow-300 font-semibold"}>
                        {volumeSpike ? "Yes" : "No"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between rounded-md border border-border/50 px-3 py-2">
                      <span className="text-muted-foreground">Breakout Detected</span>
                      <span className={breakoutDetected ? "text-green-300 font-semibold" : "text-red-300 font-semibold"}>
                        {breakoutDetected ? "Yes" : "No"}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            )}

            {!loading && (
              <div className="stat-card">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-3">Quick Select</label>
                <div className="grid grid-cols-2 gap-2">
                  {availableSymbols.map((sym) => (
                    <button
                      key={sym}
                      onClick={() => setSelectedSymbol(sym)}
                      className={`px-2 py-1.5 text-xs font-medium rounded transition-colors ${
                        selectedSymbol === sym
                          ? "bg-primary text-primary-foreground"
                          : "bg-accent/50 text-foreground hover:bg-accent"
                      }`}
                    >
                      {sym}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="xl:col-span-8 space-y-4">
            <div className="stat-card !p-0 overflow-hidden">
              <div className="px-4 py-3 border-b border-border/50">
                <h3 className="text-sm font-semibold">Actionable Stock Setups</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Stock</th>
                      <th>Signal</th>
                      <th>Confidence</th>
                      <th>Entry</th>
                      <th>SL</th>
                      <th>TP</th>
                      <th>Risk/Reward</th>
                      <th>Tag</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((row) => {
                      const signal = normalizeSignal(row);
                      const tag = qualityTag(row);
                      return (
                        <tr key={row.symbol} onClick={() => setSelectedSymbol(row.symbol)} className="cursor-pointer">
                          <td className="font-mono-data font-semibold">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/chart/${encodeURIComponent(row.symbol)}`);
                              }}
                              className="hover:text-primary"
                            >
                              {row.symbol}
                            </button>
                          </td>
                          <td>
                            <span className={signal === "BUY" ? "badge-bullish" : signal === "SELL" ? "badge-bearish" : "badge-neutral"}>{signal}</span>
                          </td>
                          <td className="font-mono-data">{confidence(row).toFixed(0)}%</td>
                          <td className="font-mono-data">{formatCurrency(row.entry_price ?? row.latest_price)}</td>
                          <td className="font-mono-data text-red-300">{formatCurrency(row.stop_loss ?? row.latest_price * 0.98)}</td>
                          <td className="font-mono-data text-green-300">{formatCurrency(row.take_profit ?? row.latest_price * 1.03)}</td>
                          <td className="font-mono-data">1 : {rr(row).toFixed(2)}</td>
                          <td>
                            <span className={`text-xs px-2 py-1 rounded ${tagClass(tag)}`}>{tag}</span>
                          </td>
                        </tr>
                      );
                    })}
                    {predictions.length === 0 && (
                      <tr>
                        <td colSpan={8} className="text-center py-6 text-muted-foreground">No stock predictions available</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default StockPrediction;
