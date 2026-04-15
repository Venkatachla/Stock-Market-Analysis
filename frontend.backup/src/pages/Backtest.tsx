import { useEffect, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { StatCard } from "@/components/StatCard";
import { formatPercent } from "@/lib/formatters";
import { Activity, ArrowDown, RefreshCw, Target, TrendingUp } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

const chartTooltipStyle = {
  backgroundColor: "hsl(216 33% 12%)",
  border: "1px solid hsl(218 19% 27%)",
  borderRadius: "6px",
  color: "hsl(220 14% 90%)",
};

interface BacktestPayload {
  total_return?: number;
  win_rate?: number;
  profit_factor?: number;
  max_drawdown?: number;
  num_trades?: number;
  benchmark_return?: number;
  equity_curve?: number[];
  drawdown_curve?: number[];
}

const Backtest = () => {
  const [result, setResult] = useState<BacktestPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchBacktest = async (manual = false) => {
    try {
      if (manual) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const response = await axios.get(`${API_URL}/backtest`);
      setResult(response.data ?? null);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error fetching backtest:", error);
      setResult(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchBacktest(false);
  }, []);

  const totalReturn = (result?.total_return ?? 0) * 100;
  const benchmarkReturn = (result?.benchmark_return ?? 0) * 100;
  const winRateRaw = result?.win_rate ?? 0;
  const winRate = winRateRaw <= 1 ? winRateRaw * 100 : winRateRaw;
  const maxDrawdown = Math.abs(result?.max_drawdown ?? 0) * 100;

  const equitySeries = (result?.equity_curve ?? []).map((equity, index) => ({
    idx: index + 1,
    equity,
  }));

  const ddSeries = (result?.drawdown_curve ?? []).map((drawdown, index) => ({
    idx: index + 1,
    drawdown: drawdown * 100,
  }));

  const compareSeries = [
    { label: "Strategy", value: totalReturn },
    { label: "Buy & Hold", value: benchmarkReturn },
  ];

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1>Backtest Results</h1>
            <p className="text-sm text-muted-foreground mt-1">Know quickly if this strategy deserves capital</p>
            {lastUpdated && <p className="text-xs text-muted-foreground mt-1">Last updated: {lastUpdated}</p>}
          </div>
          <button
            onClick={() => fetchBacktest(true)}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium bg-accent/60 border border-border rounded-md hover:bg-accent disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard title="Total Return" value={formatPercent(totalReturn)} icon={<TrendingUp className="h-4 w-4" />} />
          <StatCard title="Win Rate" value={`${winRate.toFixed(1)}%`} icon={<Target className="h-4 w-4" />} />
          <StatCard title="Profit Factor" value={(result?.profit_factor ?? 0).toFixed(2)} icon={<Activity className="h-4 w-4" />} />
          <StatCard title="Max Drawdown" value={`${maxDrawdown.toFixed(2)}%`} icon={<ArrowDown className="h-4 w-4" />} />
          <StatCard title="Trades" value={String(result?.num_trades ?? 0)} icon={<Activity className="h-4 w-4" />} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="stat-card">
            <h3 className="text-sm font-semibold mb-4">Equity Curve</h3>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={equitySeries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(218 19% 27% / 0.3)" />
                  <XAxis dataKey="idx" tick={{ fill: "hsl(218 11% 65%)", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "hsl(218 11% 65%)", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Line type="monotone" dataKey="equity" stroke="#3B82F6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="stat-card">
            <h3 className="text-sm font-semibold mb-4">Drawdown Curve</h3>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ddSeries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(218 19% 27% / 0.3)" />
                  <XAxis dataKey="idx" tick={{ fill: "hsl(218 11% 65%)", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "hsl(218 11% 65%)", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                  <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [`${v.toFixed(2)}%`]} />
                  <Area type="monotone" dataKey="drawdown" stroke="#EF4444" fill="#EF4444" fillOpacity={0.15} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <h3 className="text-sm font-semibold mb-4">Strategy vs Buy & Hold</h3>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={compareSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(218 19% 27% / 0.3)" />
                <XAxis dataKey="label" tick={{ fill: "hsl(218 11% 65%)", fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: "hsl(218 11% 65%)", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [`${v.toFixed(2)}%`]} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="value" stroke="#10B981" strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Verdict: {totalReturn > benchmarkReturn ? "Strategy is currently worth using." : "Strategy needs more tuning before live use."}
          </p>
        </div>
      </div>
    </AppLayout>
  );
};

export default Backtest;
