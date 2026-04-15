import { useEffect, useMemo, useRef, useState } from "react";
import { createChart, ColorType, type IChartApi, type ISeriesApi, type CandlestickData, type HistogramData, type UTCTimestamp, LineStyle, Time, CandlestickSeries, HistogramSeries, LineSeries } from "lightweight-charts";
import axios from "axios";
import { Maximize, Minimize } from "lucide-react";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface EnhancedChartProps {
  symbol: string;
  timeframe: string;
  predictionData?: any;
  showPrediction?: boolean;
}

export function EnhancedStockChart({ symbol, timeframe, predictionData, showPrediction }: EnhancedChartProps) {
  const chartEl = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const predictionLineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sma20Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const sma50Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const ema20Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sma200Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const ema50Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const vwapRef = useRef<ISeriesApi<"Line"> | null>(null);

  const [candles, setCandles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [hasMoreHistory, setHasMoreHistory] = useState(true);
  const [error, setError] = useState("");
  const [indicators, setIndicators] = useState({ sma20: true, sma50: false, sma200: false, ema20: false, ema50: false, bb: false, vwap: false });
  const [showIndicatorMenu, setShowIndicatorMenu] = useState(false);
  const isLiveRef = useRef<boolean>(false);

  const interval = timeframe === "1d" || timeframe === "1wk" ? timeframe : timeframe;

  const toTs = (t: any): UTCTimestamp => {
    if (typeof t === "string") return Math.floor(new Date(t).getTime() / 1000) as UTCTimestamp;
    if (typeof t === "number" && t > 1000000000000) return Math.floor(t / 1000) as UTCTimestamp;
    return Number(t) as UTCTimestamp;
  };

  const normalizedCandles = useMemo(() => {
    const rows = candles.map(c => ({
      time: toTs(c.time),
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
      volume: Number(c.volume || 0),
    })).sort((a, b) => Number(a.time) - Number(b.time));

    const unique: typeof rows = [];
    const seen = new Set<number>();
    for (const r of rows) {
      const key = Number(r.time);
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(r);
      }
    }
    return unique;
  }, [candles]);

  const calcSMA = (period: number) => {
    const out: { time: UTCTimestamp; value: number }[] = [];
    let rolling = 0;
    for (let i = 0; i < normalizedCandles.length; i++) {
      rolling += normalizedCandles[i].close;
      if (i >= period) rolling -= normalizedCandles[i - period].close;
      if (i >= period - 1) out.push({ time: normalizedCandles[i].time, value: rolling / period });
    }
    return out;
  };

  const calcEMA = (period: number) => {
    const out: { time: UTCTimestamp; value: number }[] = [];
    if (normalizedCandles.length === 0) return out;
    const k = 2 / (period + 1);
    let ema = normalizedCandles[0].close;
    for (let i = 0; i < normalizedCandles.length; i++) {
      ema = normalizedCandles[i].close * k + ema * (1 - k);
      if (i >= period - 1) out.push({ time: normalizedCandles[i].time, value: ema });
    }
    return out;
  };

  const calcVWAP = () => {
    const out: { time: UTCTimestamp; value: number }[] = [];
    let cumPV = 0;
    let cumV = 0;
    for (const c of normalizedCandles) {
      const typical = (c.high + c.low + c.close) / 3;
      const vol = Math.max(c.volume || 0, 0);
      cumPV += typical * vol;
      cumV += vol;
      if (cumV > 0) out.push({ time: c.time, value: cumPV / cumV });
    }
    return out;
  };

  const calcBB = (period = 20, mult = 2) => {
    const upper: { time: UTCTimestamp; value: number }[] = [];
    const lower: { time: UTCTimestamp; value: number }[] = [];
    for (let i = period - 1; i < normalizedCandles.length; i++) {
      const slice = normalizedCandles.slice(i - period + 1, i + 1).map(x => x.close);
      const mean = slice.reduce((a, b) => a + b, 0) / period;
      const variance = slice.reduce((a, b) => a + ((b - mean) ** 2), 0) / period;
      const stdev = Math.sqrt(variance);
      upper.push({ time: normalizedCandles[i].time, value: mean + mult * stdev });
      lower.push({ time: normalizedCandles[i].time, value: mean - mult * stdev });
    }
    return { upper, lower };
  };

  // Load initial candles from the new optimized endpoint
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setLoading(true);
        setError("");
        const res = await axios.get(`${API_URL}/candles?symbol=${symbol}&interval=${interval}&limit=200`);
        if (active && res.data?.data) {
          setCandles(res.data.data);
          setHasMoreHistory(res.data.data.length >= 200);
        }
      } catch (e: any) {
        if (active) setError(e.response?.data?.detail || "Error loading chart");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [symbol, timeframe]);

  // Load History on scroll left
  const loadMoreHistory = async () => {
    if (loadingHistory || !hasMoreHistory || candles.length === 0) return;
    try {
      setLoadingHistory(true);
      const oldestTime = candles[0].time;
      const res = await axios.get(`${API_URL}/candles/history?symbol=${symbol}&interval=${interval}&before=${oldestTime}&limit=200`);
      if (res.data?.data?.length) {
         setCandles(prev => [...res.data.data, ...prev]);
         if (res.data.data.length < 200) setHasMoreHistory(false);
      } else {
         setHasMoreHistory(false);
      }
    } catch (e) {
      console.error("History fetch error:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (!chartEl.current) return;
    const chart = createChart(chartEl.current, {
      layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: "#9ca3af" },
      grid: { vertLines: { color: "rgba(255, 255, 255, 0.05)" }, horzLines: { color: "rgba(255, 255, 255, 0.05)" } },
      width: chartEl.current.clientWidth,
      height: Math.max(chartEl.current.clientHeight, 500),
      crosshair: { mode: 0 },
      timeScale: { timeVisible: true, borderColor: "rgba(255,255,255,0.1)" },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.1)" }
    });

    const candSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e", downColor: "#ef4444", borderVisible: false,
      wickUpColor: "#22c55e", wickDownColor: "#ef4444",
    });

    const volSeries = chart.addSeries(HistogramSeries, {
      color: "#26a69a", priceFormat: { type: "volume" },
      priceScaleId: "",
    });
    chart.priceScale("").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    const pLine = chart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 2,
      lineStyle: LineStyle.Dashed,
    });

    const sma20 = chart.addSeries(LineSeries, { color: '#22c55e', lineWidth: 1 });
    const sma50 = chart.addSeries(LineSeries, { color: '#f59e0b', lineWidth: 1 });
    const ema20 = chart.addSeries(LineSeries, { color: '#60a5fa', lineWidth: 1 });
    const ema50 = chart.addSeries(LineSeries, { color: '#38bdf8', lineWidth: 1 });
    const sma200 = chart.addSeries(LineSeries, { color: '#f97316', lineWidth: 1 });
    const bbU = chart.addSeries(LineSeries, { color: '#a78bfa', lineWidth: 1, lineStyle: LineStyle.Dotted });
    const bbL = chart.addSeries(LineSeries, { color: '#a78bfa', lineWidth: 1, lineStyle: LineStyle.Dotted });
    const vwap = chart.addSeries(LineSeries, { color: '#10b981', lineWidth: 1 });

    chartRef.current = chart;
    candleRef.current = candSeries;
    volumeRef.current = volSeries;
    predictionLineRef.current = pLine;
    sma20Ref.current = sma20;
    sma50Ref.current = sma50;
    ema20Ref.current = ema20;
    ema50Ref.current = ema50;
    sma200Ref.current = sma200;
    bbUpperRef.current = bbU;
    bbLowerRef.current = bbL;
    vwapRef.current = vwap;

    // Load history when scrolling left
    chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
       if (range && range.from < 10) {
          loadMoreHistory();
       }
    });

    const ro = new ResizeObserver((entries) => {
      if (entries.length === 0 || !chartRef.current) return;
      chartRef.current.applyOptions({
        width: entries[0].contentRect.width,
        height: Math.max(entries[0].contentRect.height, 300),
      });
    });
    ro.observe(chartEl.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current) return;
    chartRef.current.applyOptions({
      layout: {
        background: { type: ColorType.Solid, color: isFullscreen ? "#0b1220" : "transparent" },
        textColor: "#9ca3af",
      },
    });
  }, [isFullscreen]);

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current || !normalizedCandles.length) return;

    try {
      candleRef.current.setData(normalizedCandles);
      volumeRef.current.setData(normalizedCandles.map(c => ({
        time: c.time as UTCTimestamp,
        value: c.volume || 0,
        color: c.close >= c.open ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"
      })));
      
      if (!isLiveRef.current) {
         chartRef.current?.timeScale().fitContent();
      }
    } catch(err) {
      console.error(err);
    }
  }, [candles]);

  useEffect(() => {
    if (!normalizedCandles.length) return;
    if (sma20Ref.current) sma20Ref.current.setData(indicators.sma20 ? calcSMA(20) : []);
    if (sma50Ref.current) sma50Ref.current.setData(indicators.sma50 ? calcSMA(50) : []);
    if (sma200Ref.current) sma200Ref.current.setData(indicators.sma200 ? calcSMA(200) : []);
    if (ema20Ref.current) ema20Ref.current.setData(indicators.ema20 ? calcEMA(20) : []);
    if (ema50Ref.current) ema50Ref.current.setData(indicators.ema50 ? calcEMA(50) : []);
    const bb = calcBB(20, 2);
    if (bbUpperRef.current) bbUpperRef.current.setData(indicators.bb ? bb.upper : []);
    if (bbLowerRef.current) bbLowerRef.current.setData(indicators.bb ? bb.lower : []);
    if (vwapRef.current) vwapRef.current.setData(indicators.vwap ? calcVWAP() : []);
  }, [normalizedCandles, indicators]);

  // Live Polling for Market Updates
  useEffect(() => {
    if (candles.length === 0 || !candleRef.current) return;
    const intervalId = setInterval(async () => {
      try {
        const res = await axios.get(`${API_URL}/candles?symbol=${symbol}&interval=${interval}&limit=1`);
        if (res.data?.data?.length > 0) {
          isLiveRef.current = true;
          const tick = res.data.data[res.data.data.length - 1];
          let t = tick.time;
          if (typeof t === "string") t = Math.floor(new Date(t).getTime() / 1000);
          else if (t > 1000000000000) t = Math.floor(t / 1000);
          
          if (candleRef.current) {
            candleRef.current.update({ time: t, open: tick.open, high: tick.high, low: tick.low, close: tick.close });
          }
          if (volumeRef.current) {
            volumeRef.current.update({ time: t, value: tick.volume || 0, color: tick.close >= tick.open ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)" });
          }
        }
      } catch(e){}
    }, 10000);
    return () => clearInterval(intervalId);
  }, [symbol, interval, candles.length]);

  useEffect(() => {
    if (predictionLineRef.current && showPrediction && candles.length > 0) {
      const lastCandle = candles[candles.length - 1];
      const t = Math.floor(new Date(lastCandle.time).getTime() / 1000);
      // Dummy visual projection for representation
      const dummyLine = [
        { time: t as UTCTimestamp, value: lastCandle.close },
        { time: (t + 86400) as UTCTimestamp, value: lastCandle.close * 1.02 },
        { time: (t + 86400 * 2) as UTCTimestamp, value: lastCandle.close * 1.05 }
      ];
      predictionLineRef.current.setData(dummyLine);
    } else if (predictionLineRef.current) {
      predictionLineRef.current.setData([]);
    }
  }, [showPrediction, candles]);

  const toggleFullscreen = () => setIsFullscreen(!isFullscreen);

  const containerClasses = isFullscreen
    ? "fixed inset-0 z-50 bg-slate-950 p-3 box-border"
    : "relative w-full h-[560px] rounded-xl bg-card border border-border/50 p-2 overflow-hidden";

  return (
    <div className={containerClasses}>
      <div className="absolute top-4 right-4 z-20">
        <button 
          onClick={toggleFullscreen} 
          className="p-2 rounded-lg bg-secondary/80 hover:bg-secondary text-foreground backdrop-blur-md transition-all shadow-sm border border-border/50 cursor-pointer"
        >
          {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
        </button>
      </div>
      <div className="absolute top-4 left-4 z-20">
        <button
          onClick={() => setShowIndicatorMenu(v => !v)}
          className="px-2 py-1 text-xs rounded border bg-secondary/70 border-border text-foreground"
        >
          Indicators
        </button>
        {showIndicatorMenu && (
          <div className="mt-2 w-40 rounded-md border border-border/60 bg-card shadow-lg p-2 space-y-1">
            {[{ key: 'sma20', label: 'SMA 20' }, { key: 'sma50', label: 'SMA 50' }, { key: 'sma200', label: 'SMA 200' }, { key: 'ema20', label: 'EMA 20' }, { key: 'ema50', label: 'EMA 50' }, { key: 'bb', label: 'BB 20' }, { key: 'vwap', label: 'VWAP' }].map((item) => (
              <label key={item.key} className="flex items-center gap-2 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  checked={Boolean(indicators[item.key as keyof typeof indicators])}
                  onChange={() => setIndicators((prev) => ({ ...prev, [item.key]: !prev[item.key as keyof typeof prev] }))}
                />
                <span>{item.label}</span>
              </label>
            ))}
          </div>
        )}
      </div>
      {loading && <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/50 backdrop-blur-sm"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}
      {error && <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/80 text-red-400">{error}</div>}
      <div ref={chartEl} className={`w-full ${isFullscreen ? 'h-[calc(100vh-24px)]' : 'h-full'}`} />
    </div>
  );
}
