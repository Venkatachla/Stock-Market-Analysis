import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";
import { OptionChain } from "@/components/OptionChain";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface OptionItem {
  symbol: string;
  underlying_price: number;
  expiry: string | null;
  direction: "CALL" | "PUT";
  strike: number;
  probability_up: number;
  confidence: number;
  expected_move: number;
  implied_volatility: number;
  put_call_ratio: number;
  liquidity_oi: number;
  edge_pct: number;
  risk_reward_proxy: number;
  opportunity_score: number;
  note: string;
}

const formatCurrency = (v: number) => `₹${Number(v || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;

const OptionsLab = () => {
  const [items, setItems] = useState<OptionItem[]>([]);
  const [selected, setSelected] = useState<OptionItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [showChain, setShowChain] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/options/opportunities`, { params: { limit: 15 } });
      const rows = Array.isArray(res.data?.items) ? (res.data.items as OptionItem[]) : [];
      setItems(rows);
      setSelected(rows[0] ?? null);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch {
      setItems([]);
      setSelected(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const ranked = useMemo(() => [...items].sort((a, b) => b.opportunity_score - a.opportunity_score), [items]);

  return (
    <AppLayout>
      <div className="space-y-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1>OPTIONS LAB</h1>
            <p className="text-sm text-muted-foreground mt-1">Directional options opportunities ranked by edge, confidence, and liquidity</p>
            <p className="text-xs text-muted-foreground mt-1">Updated: {lastUpdated || "--"}</p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-sm font-semibold hover:bg-primary/90 disabled:opacity-60"
          >
            Refresh
          </button>
        </div>

        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-3 text-xs text-yellow-200">
          Options are high-risk instruments. This section gives probabilistic setups, not guaranteed future predictions.
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          <div className="xl:col-span-8 space-y-3">
            {ranked.map((it) => {
              const active = selected?.symbol === it.symbol && selected?.strike === it.strike;
              return (
                <div
                  key={`${it.symbol}-${it.expiry}-${it.strike}-${it.direction}`}
                  onClick={() => setSelected(it)}
                  className={`rounded-xl border p-4 cursor-pointer ${active ? "border-primary/60 bg-primary/10" : "border-border/60 bg-card"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-lg font-bold">{it.symbol}</p>
                      <p className="text-xs text-muted-foreground">Expiry: {it.expiry || "N/A"}</p>
                    </div>
                    <span className={it.direction === "CALL" ? "badge-bullish" : "badge-bearish"}>{it.direction}</span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm mt-3">
                    <div><p className="text-xs text-muted-foreground">Strike</p><p className="font-mono-data">{formatCurrency(it.strike)}</p></div>
                    <div><p className="text-xs text-muted-foreground">Edge</p><p className="font-mono-data">{it.edge_pct.toFixed(1)}%</p></div>
                    <div><p className="text-xs text-muted-foreground">Confidence</p><p className="font-mono-data">{it.confidence.toFixed(1)}%</p></div>
                    <div><p className="text-xs text-muted-foreground">Expected Move</p><p className="font-mono-data">{formatCurrency(it.expected_move)}</p></div>
                    <div><p className="text-xs text-muted-foreground">Score</p><p className="font-mono-data">{it.opportunity_score.toFixed(1)}</p></div>
                  </div>
                </div>
              );
            })}

            {!loading && ranked.length === 0 && (
              <div className="stat-card text-sm text-muted-foreground">No options opportunities available right now.</div>
            )}
          </div>

          <div className="xl:col-span-4">
            <div className="rounded-xl border border-border/60 bg-card p-4 sticky top-4">
              <h3 className="text-sm font-semibold">Contract Details</h3>
              {selected ? (
                <div className="space-y-2 mt-3 text-sm">
                  <div className="flex justify-between"><span className="text-muted-foreground">Symbol</span><span>{selected.symbol}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Direction</span><span className={selected.direction === "CALL" ? "badge-bullish" : "badge-bearish"}>{selected.direction}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Underlying</span><span>{formatCurrency(selected.underlying_price)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Strike</span><span>{formatCurrency(selected.strike)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Probability Up</span><span>{(selected.probability_up * 100).toFixed(2)}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Implied Volatility</span><span>{selected.implied_volatility.toFixed(2)}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">PCR</span><span>{selected.put_call_ratio.toFixed(3)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Liquidity (OI)</span><span>{selected.liquidity_oi.toLocaleString("en-IN")}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">R/R Proxy</span><span>1 : {selected.risk_reward_proxy.toFixed(2)}</span></div>
                  <p className="text-xs text-muted-foreground pt-2 border-t border-border/50">{selected.note}</p>
                  <button 
                    onClick={() => setShowChain(selected.symbol)}
                    className="w-full mt-4 bg-primary text-primary-foreground py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors"
                  >
                    View F&O Option Chain
                  </button>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground mt-3">Select a row to inspect details.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    
      {showChain && <OptionChain symbol={showChain} onClose={() => setShowChain(null)} />}
    </AppLayout>
  );
};

export default OptionsLab;
