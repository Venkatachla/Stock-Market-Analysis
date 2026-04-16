import React, { useEffect, useRef, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { createChart, ColorType, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts';
import { usePolling } from '@/hooks/usePolling';
import { fetchStockDetail, fetchOHLC, fetchIndicators } from '@/services/api';
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

  // Fetch real stock data from backend with autoupdate every 30 seconds
  const { data: stock } = usePolling<StockSignal>(
    () => fetchStockDetail(symbol!),
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
    signal: 'NEUTRAL',
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
        <MetricCard label="Confidence" value={`${(detail.confidence * 100).toFixed(0)}%`} icon={<Activity className="h-4 w-4 text-primary" />} />
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
            <div className="text-lg font-mono text-foreground">{indicators.macd[indicators.macd.length - 1]?.macd.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Signal</div>
            <div className="text-lg font-mono text-foreground">{indicators.macd[indicators.macd.length - 1]?.signal.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Histogram</div>
            <div className={`text-lg font-mono ${(indicators.macd[indicators.macd.length - 1]?.histogram ?? 0) >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
              {indicators.macd[indicators.macd.length - 1]?.histogram.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Trading Action Buttons */}
      <TradingPanel stock={detail} />
    </div>
  );
};

// Trading Panel Component
const TradingPanel: React.FC<{ stock: StockSignal }> = ({ stock }) => {
  const [quantity, setQuantity] = React.useState(1);
  const [loading, setLoading] = React.useState(false);
  const [message, setMessage] = React.useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleTrade = async (action: 'buy' | 'sell') => {
    if (quantity <= 0) {
      setMessage({ type: 'error', text: 'Quantity must be greater than 0' });
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setMessage({ type: 'error', text: 'Please login to trade' });
        setLoading(false);
        return;
      }

      const endpoint = action === 'buy' ? '/api/trading/buy' : '/api/trading/sell';
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          symbol: stock.symbol,
          quantity: quantity,
          price: stock.price
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({
          type: 'success',
          text: `${action.toUpperCase()} successful! ${quantity} shares of ${stock.symbol} @ ₹${stock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
        });
        setQuantity(1);
        setTimeout(() => setMessage(null), 5000);
      } else {
        setMessage({ type: 'error', text: data.detail || `${action} failed` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-6 space-y-4">
      <h2 className="font-semibold text-card-foreground text-lg">Execute Trade</h2>

      {message && (
        <div className={`p-3 rounded-md text-sm ${
          message.type === 'success'
            ? 'bg-signal-buy/20 text-signal-buy border border-signal-buy/50'
            : 'bg-signal-sell/20 text-signal-sell border border-signal-sell/50'
        }`}>
          {message.text}
        </div>
      )}

      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="stock-detail-quantity" className="text-sm text-muted-foreground block mb-2">Quantity</label>
            <input
              id="stock-detail-quantity"
              name="quantity"
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground block mb-2">Price per share</label>
            <div className="px-3 py-2 rounded-md border border-border bg-muted text-foreground">
              ₹{stock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        <div>
          <label className="text-sm text-muted-foreground block mb-2">Total Amount</label>
          <div className="px-3 py-2 rounded-md border border-border bg-muted text-foreground font-mono text-lg">
            ₹{(quantity * stock.price).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => handleTrade('buy')}
          disabled={loading}
          className="flex-1 px-4 py-2.5 rounded-md bg-signal-buy text-white font-medium hover:bg-signal-buy/90 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Processing...' : `BUY ${quantity} @ ₹${stock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`}
        </button>
        <button
          onClick={() => handleTrade('sell')}
          disabled={loading}
          className="flex-1 px-4 py-2.5 rounded-md bg-signal-sell text-white font-medium hover:bg-signal-sell/90 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Processing...' : `SELL ${quantity} @ ₹${stock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`}
        </button>
      </div>

      <p className="text-xs text-muted-foreground text-center">
        💡 Note: Prices shown are real-time from backend. {stock.signal === 'BUY' ? '✓ AI recommends BUY' : stock.signal === 'SELL' ? '✓ AI recommends SELL' : 'Neutral signal'}
      </p>
    </div>
  );
};

export default React.memo(StockDetail);
