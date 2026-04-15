import { useEffect, useRef, useState, memo } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, UTCTimestamp, CandlestickSeries } from "lightweight-charts";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface MiniCandlestickProps {
  symbol: string;
  timeframe?: string; // e.g. "1d", "15m"
  period?: string;    // e.g. "1mo", "5d"
}

// Wrap in memo to prevent unnecessary re-renders for identical symbols
export const MiniCandlestick = memo(({ symbol, timeframe = "1d", period = "1mo" }: MiniCandlestickProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [candles, setCandles] = useState<any[]>([]);

  useEffect(() => {
    let active = true;
    async function loadData() {
      try {
        const res = await axios.get(`${API_URL}/chart/${symbol}?period=${period}&interval=${timeframe}`);
        if (active && res.data?.candles) {
          // Keep only the last 30 candles for speed and clean look
          const recentCandles = res.data.candles.slice(-30);
          setCandles(recentCandles);
        }
      } catch (err) {
        // silently fail for mini charts not to pollute logs
      }
    }
    loadData();
    return () => { active = false; };
  }, [symbol, timeframe, period]);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    chartRef.current = createChart(chartContainerRef.current, {
      width: 100,
      height: 40,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "transparent",
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      rightPriceScale: { visible: false },
      timeScale: { visible: false },
      crosshair: {
        mode: 0,
        vertLine: { visible: false },
        horzLine: { visible: false },
      },
      handleScroll: false,
      handleScale: false,
    });

    seriesRef.current = chartRef.current.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    }) as any;

    return () => {
      chartRef.current?.remove();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (seriesRef.current && candles.length > 0) {
      const formatted = candles.map(c => ({
        time: Math.floor(new Date(c.time).getTime() / 1000) as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close
      }));
      // lightweight charts requires strictly ascending time
      const unique = formatted.reduce((acc, current) => {
        const x = acc.find((item: any) => item.time === current.time);
        if (!x) {
          acc.push(current);
        }
        return acc;
      }, []);

      unique.sort((a: any, b: any) => a.time - b.time);
      seriesRef.current.setData(unique);
      chartRef.current?.timeScale().fitContent();
    }
  }, [candles]);

  return (
    <div ref={chartContainerRef} className="w-[100px] h-[40px] opacity-80 group-hover:opacity-100 transition-opacity" />
  );
});
