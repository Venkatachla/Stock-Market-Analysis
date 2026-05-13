// Mock data for when API is unavailable
import type { StockSignal, MarketOverview, PortfolioHolding, RiskMetrics, OHLC, TechnicalIndicators } from '@/services/api';

const signals: StockSignal[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', price: 2456.75, change: 34.20, changePercent: 1.41, signal: 'BUY', confidence: 0.85, volume: 12500000, marketCap: 1660000000000, sector: 'Energy' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', price: 3890.50, change: -22.30, changePercent: -0.57, signal: 'NEUTRAL', confidence: 0.62, volume: 3200000, marketCap: 1420000000000, sector: 'IT' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', price: 1678.25, change: 15.60, changePercent: 0.94, signal: 'BUY', confidence: 0.78, volume: 8900000, marketCap: 950000000000, sector: 'Banking' },
  { symbol: 'INFY', name: 'Infosys', price: 1456.80, change: -18.45, changePercent: -1.25, signal: 'SELL', confidence: 0.72, volume: 6700000, marketCap: 610000000000, sector: 'IT' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', price: 1023.40, change: 8.90, changePercent: 0.88, signal: 'BUY', confidence: 0.81, volume: 9800000, marketCap: 720000000000, sector: 'Banking' },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever', price: 2567.90, change: -5.30, changePercent: -0.21, signal: 'NEUTRAL', confidence: 0.55, volume: 2100000, marketCap: 600000000000, sector: 'FMCG' },
  { symbol: 'SBIN', name: 'State Bank of India', price: 623.15, change: 12.80, changePercent: 2.10, signal: 'BUY', confidence: 0.88, volume: 15600000, marketCap: 560000000000, sector: 'Banking' },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel', price: 1534.60, change: -28.70, changePercent: -1.84, signal: 'SELL', confidence: 0.69, volume: 4300000, marketCap: 480000000000, sector: 'Telecom' },
  { symbol: 'ITC', name: 'ITC Limited', price: 445.30, change: 3.20, changePercent: 0.72, signal: 'BUY', confidence: 0.74, volume: 11200000, marketCap: 550000000000, sector: 'FMCG' },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', price: 1789.45, change: -9.15, changePercent: -0.51, signal: 'NEUTRAL', confidence: 0.58, volume: 3800000, marketCap: 350000000000, sector: 'Banking' },
];

export const mockMarketOverview: MarketOverview = {
  indices: [
    { name: 'NIFTY 50', value: 22456.80, change: 156.30, changePercent: 0.70 },
    { name: 'SENSEX', value: 73890.45, change: 512.65, changePercent: 0.70 },
    { name: 'NIFTY BANK', value: 48234.15, change: -189.40, changePercent: -0.39 },
    { name: 'NIFTY IT', value: 34567.90, change: -234.50, changePercent: -0.67 },
  ],
  topGainers: signals.filter(s => s.change > 0).sort((a, b) => b.changePercent - a.changePercent).slice(0, 5),
  topLosers: signals.filter(s => s.change < 0).sort((a, b) => a.changePercent - b.changePercent).slice(0, 5),
  mostActive: [...signals].sort((a, b) => b.volume - a.volume).slice(0, 5),
};

export const mockSignals = signals;

export const mockPortfolio: PortfolioHolding[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', quantity: 50, avgPrice: 2380.00, currentPrice: 2456.75, pnl: 3837.50, pnlPercent: 3.23, allocation: 25.5, signal: 'BUY' },
  { symbol: 'TCS', name: 'TCS', quantity: 30, avgPrice: 3950.00, currentPrice: 3890.50, pnl: -1785.00, pnlPercent: -1.51, allocation: 24.2, signal: 'NEUTRAL' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', quantity: 60, avgPrice: 1620.00, currentPrice: 1678.25, pnl: 3495.00, pnlPercent: 3.60, allocation: 20.9, signal: 'BUY' },
  { symbol: 'INFY', name: 'Infosys', quantity: 40, avgPrice: 1510.00, currentPrice: 1456.80, pnl: -2128.00, pnlPercent: -3.52, allocation: 12.1, signal: 'SELL' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', quantity: 80, avgPrice: 985.00, currentPrice: 1023.40, pnl: 3072.00, pnlPercent: 3.90, allocation: 17.0, signal: 'BUY' },
];

export const mockRisk: RiskMetrics = {
  portfolioVar: -2.34,
  sharpeRatio: 1.45,
  beta: 1.12,
  maxDrawdown: -8.67,
  volatility: 18.5,
  correlationMatrix: {
    RELIANCE: { RELIANCE: 1, TCS: 0.35, HDFCBANK: 0.52, INFY: 0.28, ICICIBANK: 0.61 },
    TCS: { RELIANCE: 0.35, TCS: 1, HDFCBANK: 0.22, INFY: 0.85, ICICIBANK: 0.18 },
    HDFCBANK: { RELIANCE: 0.52, TCS: 0.22, HDFCBANK: 1, INFY: 0.15, ICICIBANK: 0.78 },
    INFY: { RELIANCE: 0.28, TCS: 0.85, HDFCBANK: 0.15, INFY: 1, ICICIBANK: 0.12 },
    ICICIBANK: { RELIANCE: 0.61, TCS: 0.18, HDFCBANK: 0.78, INFY: 0.12, ICICIBANK: 1 },
  },
};

export function generateMockOHLC(days = 250): OHLC[] {
  const data: OHLC[] = [];
  let price = 2400;
  const now = new Date();
  const baseDate = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  for (let i = days; i >= 0; i--) {
    const date = new Date(baseDate);
    date.setUTCDate(date.getUTCDate() - i);
    if (date.getUTCDay() === 0 || date.getUTCDay() === 6) continue;
    const change = (Math.random() - 0.48) * 60;
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * 30;
    const low = Math.min(open, close) - Math.random() * 30;
    data.push({
      time: date.toISOString().split('T')[0],
      open: +open.toFixed(2),
      high: +high.toFixed(2),
      low: +low.toFixed(2),
      close: +close.toFixed(2),
      volume: Math.floor(5000000 + Math.random() * 15000000),
    });
    price = close;
  }
  return data;
}

export function generateMockIndicators(ohlc: OHLC[]): TechnicalIndicators {
  const closes = ohlc.map(c => c.close);
  const sma = (data: number[], period: number) => data.map((_, i) => i < period - 1 ? data[i] : data.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period);
  return {
    sma20: sma(closes, 20),
    sma50: sma(closes, 50),
    ema12: sma(closes, 12),
    ema26: sma(closes, 26),
    rsi: closes.map(() => 30 + Math.random() * 40),
    macd: closes.map(() => ({ macd: (Math.random() - 0.5) * 20, signal: (Math.random() - 0.5) * 15, histogram: (Math.random() - 0.5) * 10 })),
    bollingerBands: closes.map((c) => ({ upper: c + 50 + Math.random() * 30, middle: c, lower: c - 50 - Math.random() * 30 })),
  };
}
