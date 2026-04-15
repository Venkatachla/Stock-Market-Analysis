import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Response cache
const cache = new Map<string, { data: unknown; timestamp: number }>();

function getCached<T>(key: string, ttlMs: number): T | null {
  const entry = cache.get(key);
  if (entry && Date.now() - entry.timestamp < ttlMs) return entry.data as T;
  return null;
}

function setCache(key: string, data: unknown) {
  cache.set(key, { data, timestamp: Date.now() });
}

const FIVE_MIN = 5 * 60 * 1000;
const ONE_MIN = 60 * 1000;

async function cachedGet<T>(url: string, ttl = FIVE_MIN): Promise<T> {
  const cached = getCached<T>(url, ttl);
  if (cached) return cached;
  const { data } = await api.get<T>(url);
  setCache(url, data);
  return data;
}

// Types
export interface StockSignal {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  signal: 'BUY' | 'SELL' | 'NEUTRAL';
  confidence: number;
  volume: number;
  marketCap?: number;
  sector?: string;
}

export interface OHLC {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicators {
  sma20: number[];
  sma50: number[];
  ema12: number[];
  ema26: number[];
  rsi: number[];
  macd: { macd: number; signal: number; histogram: number }[];
  bollingerBands: { upper: number; middle: number; lower: number }[];
}

export interface PortfolioHolding {
  symbol: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  allocation: number;
  signal: 'BUY' | 'SELL' | 'NEUTRAL';
}

export interface RiskMetrics {
  portfolioVar: number;
  sharpeRatio: number;
  beta: number;
  maxDrawdown: number;
  volatility: number;
  correlationMatrix: Record<string, Record<string, number>>;
}

export interface MarketOverview {
  indices: { name: string; value: number; change: number; changePercent: number }[];
  topGainers: StockSignal[];
  topLosers: StockSignal[];
  mostActive: StockSignal[];
}

// API functions
export const fetchMarketOverview = () => cachedGet<MarketOverview>('/api/market/overview', ONE_MIN);
export const fetchStockSignals = () => cachedGet<StockSignal[]>('/api/signals', ONE_MIN);
export const fetchStockDetail = (symbol: string) => cachedGet<StockSignal>(`/api/stock/${symbol}`, ONE_MIN);
export const fetchOHLC = (symbol: string, period = '1y') => cachedGet<OHLC[]>(`/api/stock/${symbol}/ohlc?period=${period}`, FIVE_MIN);
export const fetchIndicators = (symbol: string) => cachedGet<TechnicalIndicators>(`/api/stock/${symbol}/indicators`, FIVE_MIN);
export const fetchPortfolio = () => cachedGet<PortfolioHolding[]>('/api/portfolio', FIVE_MIN);
export const fetchRiskMetrics = () => cachedGet<RiskMetrics>('/api/risk', FIVE_MIN);
export const fetchDiscovery = (filters?: Record<string, string>) => {
  const params = new URLSearchParams(filters);
  return cachedGet<StockSignal[]>(`/api/discovery?${params}`, FIVE_MIN);
};

export default api;
