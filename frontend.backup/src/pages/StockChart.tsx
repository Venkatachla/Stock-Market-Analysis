import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import { useParams } from "react-router-dom";
import { createChart, ColorType, type IChartApi, type ISeriesApi, type CandlestickData, type HistogramData, type UTCTimestamp, CandlestickSeries, HistogramSeries } from "lightweight-charts";
import { AppLayout } from "@/components/AppLayout";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface CandleRow {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const PERIODS = ["1mo", "3mo", "6mo", "1y", "2y", "5y"];
const INTERVALS = ["5m", "15m", "1h", "1d", "1wk"];

const StockChart = () => {
  const params = useParams();
  const symbol = String(params.symbol || "RELIANCE").toUpperCase();

  const [period, setPeriod] = useState("6mo");
  const [interval, setInterval] = useState("1d");
  const [candles, setCandles] = useState<CandleRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const chartEl = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const latest = useMemo(() => (candles.length ? candles[candles.length - 1] : null), [candles]);

  const load = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await axios.get(`${API_URL}/chart/${symbol}`, { params: { period, interval } });
      const rows = Array.isArray(res.data?.candles) ? (res.data.candles as CandleRow[]) : [];
      setCandles(rows);
    } catch (e: any) {
      setCandles([]);
      setError(String(e?.response?.data?.detail || "Unable to load chart data"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [symbol, period, interval]);

  useEffect(() => {
    if (!chartEl.current) return;

    const chart = createChart(chartEl.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#0d111a" },
        textColor: "#d7deed",
      },
      grid: {
        vertLines: { color: "rgba(160, 175, 205, 0.12)" },
        horzLines: { color: "rgba(160, 175, 205, 0.12)" },
      },
      width: chartEl.current.clientWidth,
      height: 560,
      rightPriceScale: {
        borderColor: "rgba(160, 175, 205, 0.3)",
      },
      timeScale: {
        borderColor: "rgba(160, 175, 205, 0.3)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 0,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "rgba(59, 130, 246, 0.45)",
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });

    chart.priceScale("").applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleRef.current = candleSeries;
    volumeRef.current = volumeSeries;

    const onResize = () => {
      if (!chartEl.current || !chartRef.current) return;
      chartRef.current.applyOptions({ width: chartEl.current.clientWidth });
    };

    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current) return;

    // Deduplicate and sort chronologically just in case to prevent library crashes
    const uniqueCandles: CandleRow[] = [];
    const seenTimes = new Set<number>();
    
    [...candles].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()).forEach(c => {
      const t = Math.floor(new Date(c.time).getTime() / 1000);
      if (!seenTimes.has(t)) {
        seenTimes.add(t);
        uniqueCandles.push(c);
      }
    });

    const candleData: CandlestickData[] = uniqueCandles
      .filter((c) => c.open > 0 && c.high > 0 && c.low > 0 && c.close > 0)
      .map((c) => ({
        time: Math.floor(new Date(c.time).getTime() / 1000) as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));

    const volumeData: HistogramData[] = uniqueCandles.map((c) => ({
      time: Math.floor(new Date(c.time).getTime() / 1000) as UTCTimestamp,
      value: c.volume || 0,
      color: c.close >= c.open ? "rgba(34,197,94,0.45)" : "rgba(239,68,68,0.45)",
    }));

    try {
      candleRef.current.setData(candleData);
      volumeRef.current.setData(volumeData);
      chartRef.current?.timeScale().fitContent();
    } catch (err) {
      console.error("Lightweight charts failed to render data:", err);
    }
  }, [candles]);

  return (
    <AppLayout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1>{symbol} Chart</h1>
            <p className="text-sm text-muted-foreground mt-1">Live OHLC chart with volume, similar to TradingView layout</p>
          </div>
          <div className="flex items-center gap-2">
            <select value={period} onChange={(e) => setPeriod(e.target.value)} className="h-9 rounded-md border border-border/60 bg-card px-3 text-sm">
              {PERIODS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <select value={interval} onChange={(e) => setInterval(e.target.value)} className="h-9 rounded-md border border-border/60 bg-card px-3 text-sm">
              {INTERVALS.map((i) => (
                <option key={i} value={i}>{i}</option>
              ))}
            </select>
            <button onClick={load} disabled={loading} className="h-9 rounded-md bg-primary text-primary-foreground px-3 text-sm font-semibold hover:bg-primary/90 disabled:opacity-60">
              Refresh
            </button>
          </div>
        </div>

        {latest && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            <div className="stat-card"><p className="text-xs text-muted-foreground">Open</p><p className="font-mono-data mt-1">₹{Number(latest.open || 0).toFixed(2)}</p></div>
            <div className="stat-card"><p className="text-xs text-muted-foreground">High</p><p className="font-mono-data mt-1">₹{Number(latest.high || 0).toFixed(2)}</p></div>
            <div className="stat-card"><p className="text-xs text-muted-foreground">Low</p><p className="font-mono-data mt-1">₹{Number(latest.low || 0).toFixed(2)}</p></div>
            <div className="stat-card"><p className="text-xs text-muted-foreground">Close</p><p className="font-mono-data mt-1">₹{Number(latest.close || 0).toFixed(2)}</p></div>
            <div className="stat-card"><p className="text-xs text-muted-foreground">Volume</p><p className="font-mono-data mt-1">{Math.round(Number(latest.volume || 0)).toLocaleString("en-IN")}</p></div>
          </div>
        )}

        <div className="rounded-xl border border-border/60 bg-card p-2">
          <div ref={chartEl} className="w-full" />
        </div>

        {loading && <div className="text-sm text-muted-foreground">Loading chart...</div>}
        {error && <div className="text-sm text-red-300">{error}</div>}
      </div>
    </AppLayout>
  );
};

export default StockChart;
