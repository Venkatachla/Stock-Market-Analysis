import React, { useCallback, useEffect, useRef, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { createChart, ColorType, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts';
import { usePolling } from '@/hooks/usePolling';
import { fetchStockDetail, fetchOHLC, fetchIndicators } from '@/services/api';
import TradingModal from '@/components/TradingModal';
import { mockSignals, generateMockOHLC, generateMockIndicators } from '@/utils/mockData';
import { formatCurrency, formatPercent, formatLargeNumber } from '@/utils/format';
import { LoadingState, SignalBadge, MetricCard } from '@/components/common/StatusComponents';
import { ArrowLeft, TrendingUp, TrendingDown, BarChart3, Activity } from 'lucide-react';
import type { StockSignal, OHLC, TechnicalIndicators } from '@/services/api';

const StockDetail: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const chartRef = useRef<HTMLDivElement>(null);
  const volumeChartRef = useRef<HTMLDivElement>(null);
  const rsiChartRef = useRef<HTMLDivElement>(null);
  const [tradingOpen, setTradingOpen] = React.useState(false);
  const [tradingMode, setTradingMode] = React.useState<'BUY' | 'SELL'>('BUY');
  const token = localStorage.getItem('auth_token') || '';
  const [notification, setNotification] = React.useState<{ type: 'success' | 'error', message: string } | null>(null);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const pollStockDetail = useCallback(
    () => fetchStockDetail(symbol!),
    [symbol]
  );

  // Fetch real stock data from backend with autoupdate every 30 seconds
  const { data: stock } = usePolling<StockSignal>(
    pollStockDetail,
    30000
  );

  // Generate OHLC data for chart (this is mock data for demo)
  const ohlcData = useMemo(() => generateMockOHLC(250), []);
  const indicators = useMemo(() => generateMockIndicators(ohlcData), [ohlcData]);
  
  // Use real stock data
  const detail = stock ?? {
    symbol: symbol || 'N/A',
    name: symbol || 'N/A',
    price: 0,
    change: 0,
    changePercent: 0,
    signal: 'NEUTRAL' as const,
    confidence: 0,
    volume: 0
  };

  // Main candlestick chart
  useEffect(() => {
    if (!chartRef.current || ohlcData.length === 0) return;
    const container = chartRef.current;
    const isDark = document.documentElement.classList.contains('dark');
    const chart = createChart(container, {
      width: container.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: isDark ? '#1a1f2e' : '#ffffff' },
        textColor: isDark ? '#9ca3af' : '#6b7280',
      },
      grid: {
        vertLines: { color: isDark ? '#1f2937' : '#f3f4f6' },
        horzLines: { color: isDark ? '#1f2937' : '#f3f4f6' },
      },
      crosshair: { mode: 0 },
      timeScale: { borderColor: isDark ? '#374151' : '#e5e7eb' },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });
    candleSeries.setData(ohlcData.map(d => ({ time: d.time, open: d.open, high: d.high, low: d.low, close: d.close })) as any);

    // SMA 20
    const sma20Series = chart.addSeries(LineSeries, { color: '#3b82f6', lineWidth: 1 });
    sma20Series.setData(
      indicators.sma20.map((v, i) => ({ time: ohlcData[i].time, value: v })).filter((_, i) => i >= 19) as any
    );

    // SMA 50
    const sma50Series = chart.addSeries(LineSeries, { color: '#f59e0b', lineWidth: 1 });
    sma50Series.setData(
      indicators.sma50.map((v, i) => ({ time: ohlcData[i].time, value: v })).filter((_, i) => i >= 49) as any
    );

    // Bollinger Bands
    const bbUpper = chart.addSeries(LineSeries, { color: '#8b5cf6', lineWidth: 1, lineStyle: 2 });
    bbUpper.setData(indicators.bollingerBands.map((b, i) => ({ time: ohlcData[i].time, value: b.upper })) as any);
    const bbLower = chart.addSeries(LineSeries, { color: '#8b5cf6', lineWidth: 1, lineStyle: 2 });
    bbLower.setData(indicators.bollingerBands.map((b, i) => ({ time: ohlcData[i].time, value: b.lower })) as any);

    chart.timeScale().fitContent();

    const handleResize = () => chart.applyOptions({ width: container.clientWidth });
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [ohlcData, indicators]);

  // Volume chart
  useEffect(() => {
    if (!volumeChartRef.current || ohlcData.length === 0) return;
    const container = volumeChartRef.current;
    const isDark = document.documentElement.classList.contains('dark');
    const chart = createChart(container, {
      width: container.clientWidth, height: 120,
      layout: { background: { type: ColorType.Solid, color: isDark ? '#1a1f2e' : '#ffffff' }, textColor: isDark ? '#9ca3af' : '#6b7280' },
      grid: { vertLines: { visible: false }, horzLines: { color: isDark ? '#1f2937' : '#f3f4f6' } },
      timeScale: { borderColor: isDark ? '#374151' : '#e5e7eb' },
    });
    const volSeries = chart.addSeries(HistogramSeries, { color: '#3b82f680' });
    volSeries.setData(ohlcData.map(d => ({
      time: d.time, value: d.volume,
      color: d.close >= d.open ? '#22c55e80' : '#ef444480',
    })) as any);
    chart.timeScale().fitContent();
    const handleResize = () => chart.applyOptions({ width: container.clientWidth });
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [ohlcData]);

  // RSI chart
  useEffect(() => {
    if (!rsiChartRef.current || indicators.rsi.length === 0) return;
    const container = rsiChartRef.current;
    const isDark = document.documentElement.classList.contains('dark');
    const chart = createChart(container, {
      width: container.clientWidth, height: 150,
      layout: { background: { type: ColorType.Solid, color: isDark ? '#1a1f2e' : '#ffffff' }, textColor: isDark ? '#9ca3af' : '#6b7280' },
      grid: { vertLines: { visible: false }, horzLines: { color: isDark ? '#1f2937' : '#f3f4f6' } },
      timeScale: { borderColor: isDark ? '#374151' : '#e5e7eb' },
    });
    const rsiSeries = chart.addSeries(LineSeries, { color: '#a855f7', lineWidth: 2 });
    rsiSeries.setData(indicators.rsi.map((v, i) => ({ time: ohlcData[i].time, value: v })) as any);

    // Overbought/Oversold lines
    const ob = chart.addSeries(LineSeries, { color: '#ef444460', lineWidth: 1, lineStyle: 2 });
    ob.setData(ohlcData.map(d => ({ time: d.time, value: 70 })) as any);
    const os = chart.addSeries(LineSeries, { color: '#22c55e60', lineWidth: 1, lineStyle: 2 });
    os.setData(ohlcData.map(d => ({ time: d.time, value: 30 })) as any);

    chart.timeScale().fitContent();
    const handleResize = () => chart.applyOptions({ width: container.clientWidth });
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [ohlcData, indicators]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/" className="p-2 rounded-md hover:bg-accent transition-colors" aria-label="Back to dashboard">
          <ArrowLeft className="h-5 w-5 text-muted-foreground" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-3">
            {detail.symbol}
            <SignalBadge signal={detail.signal} />
          </h1>
          <p className="text-sm text-muted-foreground">{detail.name}</p>
        </div>
      </div>

      {/* Price stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Price" value={formatCurrency(detail.price)} change={formatPercent(detail.changePercent)} positive={detail.change >= 0}
          icon={detail.change >= 0 ? <TrendingUp className="h-4 w-4 text-signal-buy" /> : <TrendingDown className="h-4 w-4 text-signal-sell" />} />
        <MetricCard label="Volume" value={formatLargeNumber(detail.volume)} icon={<BarChart3 className="h-4 w-4 text-primary" />} />
        <MetricCard label="Confidence" value={`${typeof detail.confidence === "number" ? (detail.confidence * 100).toFixed(0) : "0"}%`} icon={<Activity className="h-4 w-4 text-primary" />} />
        <MetricCard label="Market Cap" value={detail.marketCap ? formatLargeNumber(detail.marketCap) : 'N/A'} />
      </div>

      {/* Candlestick Chart */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold text-card-foreground mb-3">Price Chart (Candlestick + SMA + Bollinger)</h2>
        <div ref={chartRef} className="w-full" />
      </div>

      {/* Volume */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold text-card-foreground mb-3">Volume</h2>
        <div ref={volumeChartRef} className="w-full" />
      </div>

      {/* RSI */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold text-card-foreground mb-3">RSI (14)</h2>
        <div ref={rsiChartRef} className="w-full" />
      </div>

      {/* MACD Table */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold text-card-foreground mb-3">MACD (Latest)</h2>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-muted-foreground">MACD</div>
            <div className="text-lg font-mono text-foreground">{typeof indicators.macd[indicators.macd.length - 1]?.macd === "number" ? indicators.macd[indicators.macd.length - 1].macd.toFixed(2) : "0.00"}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Signal</div>
            <div className="text-lg font-mono text-foreground">{typeof indicators.macd[indicators.macd.length - 1]?.signal === "number" ? indicators.macd[indicators.macd.length - 1].signal.toFixed(2) : "0.00"}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Histogram</div>
            <div className={`text-lg font-mono ${(indicators.macd[indicators.macd.length - 1]?.histogram ?? 0) >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
              {typeof indicators.macd[indicators.macd.length - 1]?.histogram === "number" ? indicators.macd[indicators.macd.length - 1].histogram.toFixed(2) : "0.00"}
            </div>
          </div>
        </div>
      </div>

      {/* Trading Action Buttons */}
      <div className="rounded-lg border border-border bg-card p-6 space-y-4">
        <h2 className="font-semibold text-card-foreground text-lg text-center mb-4">Execute Trade</h2>
        {notification && (
          <div className={`p-3 rounded-md text-sm mb-4 ${
            notification.type === 'success'
              ? 'bg-signal-buy/20 text-signal-buy border border-signal-buy/50'
              : 'bg-signal-sell/20 text-signal-sell border border-signal-sell/50'
          }`}>
            {notification.message}
          </div>
        )}
        <div className="flex gap-4">
          <button
            onClick={() => { setTradingMode('BUY'); setTradingOpen(true); }}
            className="flex-1 px-6 py-3 rounded-lg bg-signal-buy text-white font-bold hover:bg-signal-buy/90 transition-all transform hover:scale-[1.02]"
          >
            BUY {detail.symbol}
          </button>
          <button
            onClick={() => { setTradingMode('SELL'); setTradingOpen(true); }}
            className="flex-1 px-6 py-3 rounded-lg bg-signal-sell text-white font-bold hover:bg-signal-sell/90 transition-all transform hover:scale-[1.02]"
          >
            SELL {detail.symbol}
          </button>
        </div>
      </div>

      <TradingModal
        key={`${detail.symbol}-${detail.price}-${tradingOpen}`}
        isOpen={tradingOpen}
        onClose={() => setTradingOpen(false)}
        symbol={detail.symbol}
        currentPrice={Number(detail.price)}
        mode={tradingMode}
        token={token}
        onSuccess={(msg) => { showNotification('success', msg); }}
        onError={(msg) => { showNotification('error', msg); }}
      />
    </div>
  );
};


export default React.memo(StockDetail);
