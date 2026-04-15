import { useEffect, useState } from "react";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface RiskOverview {
  status: string;
  capital: number;
  risk_per_trade_pct: number;
  risk_per_trade_amount: number;
  daily_risk_budget: number;
  max_trades_per_day: number;
  confidence_threshold: number;
  active_setups: number;
  buy_setups: number;
  sell_setups: number;
  avg_confidence: number;
  mode_flags: {
    swing_enabled: boolean;
    intraday_enabled: boolean;
  };
  updated_at: string;
}

const currency = (n: number) => `₹${Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;

const RiskOS = () => {
  const [capital, setCapital] = useState(100000);
  const [overview, setOverview] = useState<RiskOverview | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/risk-os/overview`, { params: { capital } });
      setOverview(res.data);
    } catch {
      setOverview(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <AppLayout>
      <div className="space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1>RISK OS</h1>
            <p className="text-sm text-muted-foreground mt-1">Risk-first execution engine for disciplined trading</p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground">Capital</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value || 0))}
              className="w-36 rounded-md border border-border/60 bg-card px-2 py-1 text-sm"
            />
            <button
              onClick={load}
              disabled={loading}
              className="rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-sm font-semibold hover:bg-primary/90 disabled:opacity-60"
            >
              Refresh
            </button>
          </div>
        </div>

        {!overview && !loading && (
          <div className="stat-card text-sm text-muted-foreground">Unable to load Risk OS data right now.</div>
        )}

        {overview && (
          <>
            <div className={`rounded-xl border p-4 ${overview.status === "EXECUTE" ? "border-green-500/40 bg-green-500/10" : overview.status === "PAUSED" ? "border-yellow-500/40 bg-yellow-500/10" : "border-red-500/40 bg-red-500/10"}`}>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">System Status</p>
              <p className="text-2xl font-bold mt-1">{overview.status}</p>
              <p className="text-sm text-muted-foreground mt-1">Updated: {new Date(overview.updated_at).toLocaleString()}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
              <div className="stat-card"><p className="text-xs text-muted-foreground">Risk / Trade</p><p className="text-xl font-semibold mt-1">{currency(overview.risk_per_trade_amount)}</p><p className="text-xs text-muted-foreground">{overview.risk_per_trade_pct.toFixed(2)}%</p></div>
              <div className="stat-card"><p className="text-xs text-muted-foreground">Daily Risk Budget</p><p className="text-xl font-semibold mt-1">{currency(overview.daily_risk_budget)}</p><p className="text-xs text-muted-foreground">Max trades: {overview.max_trades_per_day}</p></div>
              <div className="stat-card"><p className="text-xs text-muted-foreground">Active Setups</p><p className="text-xl font-semibold mt-1">{overview.active_setups}</p><p className="text-xs text-muted-foreground">BUY {overview.buy_setups} | SELL {overview.sell_setups}</p></div>
              <div className="stat-card"><p className="text-xs text-muted-foreground">Avg Confidence</p><p className="text-xl font-semibold mt-1">{overview.avg_confidence.toFixed(1)}%</p><p className="text-xs text-muted-foreground">Threshold: {overview.confidence_threshold.toFixed(0)}%</p></div>
            </div>

            <div className="stat-card">
              <h3 className="text-base">Execution Rules</h3>
              <ul className="mt-3 text-sm text-muted-foreground space-y-1">
                <li>1. Never exceed daily risk budget.</li>
                <li>2. Stop trading after hitting max trades or risk budget.</li>
                <li>3. Take only setups above confidence threshold.</li>
                <li>4. Keep modes aligned: swing {overview.mode_flags.swing_enabled ? "ON" : "OFF"}, intraday {overview.mode_flags.intraday_enabled ? "ON" : "OFF"}.</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
};

export default RiskOS;
