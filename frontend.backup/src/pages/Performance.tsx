import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface TradeHistoryRow {
  pnl: number;
}

interface PerfPayload {
  win_rate?: number;
  trade_history?: TradeHistoryRow[];
  drawdown_curve?: number[];
  equity_curve?: number[];
}

const Performance = () => {
  const [payload, setPayload] = useState<PerfPayload | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await axios.get(`${API_URL}/performance/dashboard`);
        setPayload(response.data ?? null);
      } catch (error) {
        console.error("Error loading performance:", error);
        setPayload(null);
      }
    };

    load();
  }, []);

  const trades = payload?.trade_history ?? [];
  const wins = trades.filter((t) => t.pnl > 0);
  const losses = trades.filter((t) => t.pnl < 0);

  const totalProfitPct = useMemo(() => {
    const equity = payload?.equity_curve ?? [];
    if (equity.length < 2 || equity[0] === 0) return 0;
    return ((equity[equity.length - 1] - equity[0]) / equity[0]) * 100;
  }, [payload?.equity_curve]);

  const winRateRaw = payload?.win_rate ?? 0;
  const winRate = winRateRaw <= 1 ? winRateRaw * 100 : winRateRaw;

  const profitFactor = useMemo(() => {
    const grossProfit = wins.reduce((sum, t) => sum + t.pnl, 0);
    const grossLoss = Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0));
    if (grossLoss === 0) return grossProfit > 0 ? grossProfit : 0;
    return grossProfit / grossLoss;
  }, [losses, wins]);

  const drawdown = useMemo(() => {
    const dd = payload?.drawdown_curve ?? [];
    if (!dd.length) return 0;
    return Math.abs(Math.min(...dd)) * 100;
  }, [payload?.drawdown_curve]);

  const systemScore = useMemo(() => {
    const winScore = Math.min(100, winRate);
    const pfScore = Math.min(100, profitFactor * 25);
    const ddScore = Math.max(0, 100 - drawdown * 2);
    return Math.max(0, Math.min(100, (winScore * 0.45) + (pfScore * 0.35) + (ddScore * 0.2)));
  }, [drawdown, profitFactor, winRate]);

  return (
    <AppLayout>
      <div className="space-y-6 max-w-4xl">
        <div>
          <h1>PERFORMANCE</h1>
          <p className="text-sm text-muted-foreground mt-1">Simple scorecard</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="rounded-xl border border-border/60 bg-card p-4">
            <p className="text-xs text-muted-foreground">Total Profit %</p>
            <p className="text-3xl font-bold mt-1">{totalProfitPct.toFixed(2)}%</p>
          </div>
          <div className="rounded-xl border border-border/60 bg-card p-4">
            <p className="text-xs text-muted-foreground">Win Rate</p>
            <p className="text-3xl font-bold mt-1">{winRate.toFixed(2)}%</p>
          </div>
          <div className="rounded-xl border border-border/60 bg-card p-4">
            <p className="text-xs text-muted-foreground">Profit Factor</p>
            <p className="text-3xl font-bold mt-1">{profitFactor.toFixed(2)}</p>
          </div>
          <div className="rounded-xl border border-border/60 bg-card p-4">
            <p className="text-xs text-muted-foreground">Drawdown</p>
            <p className="text-3xl font-bold mt-1">{drawdown.toFixed(2)}%</p>
          </div>
        </div>

        <div className={`rounded-xl border p-5 ${systemScore >= 60 ? "border-green-500/40 bg-green-500/10" : "border-red-500/40 bg-red-500/10"}`}>
          <p className="text-xs uppercase tracking-wide opacity-80">System Score</p>
          <p className="text-4xl font-bold mt-1">{systemScore.toFixed(0)} / 100</p>
          {systemScore < 60 && (
            <p className="mt-2 text-sm font-semibold text-red-300">Do not trade aggressively</p>
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default Performance;
