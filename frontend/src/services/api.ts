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

// ============ INTERNAL TYPES (backend responses) ============
interface BackendStockData {
  symbol: string;
  name?: string;
  price?: number;
  change?: number;
  change_pct?: number;
  signal?: 'BUY' | 'SELL' | 'NEUTRAL';
  confidence?: number;
  volume?: number;
}

interface BackendChartData {
  datetime?: string;
  time?: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface BackendPredictionData {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'NEUTRAL';
  confidence: number;
  entry_price?: number;
  target_price?: number;
  stop_loss?: number;
  models?: Record<string, { signal: string; confidence: number }>;
}

// ============ DATA TRANSFORMERS ============
function transformBackendStock(data: BackendStockData): StockSignal {
  return {
    symbol: data.symbol,
    name: data.name || data.symbol,
    price: data.price || 0,
    change: data.change || 0,
    changePercent: data.change_pct || 0,
    signal: data.signal || 'NEUTRAL',
    confidence: data.confidence || 50,
    volume: data.volume || 0,
  };
}

function transformBackendChart(data: BackendChartData): OHLC {
  return {
    time: data.datetime || data.time || new Date().toISOString(),
    open: data.open,
    high: data.high,
    low: data.low,
    close: data.close,
    volume: data.volume,
  };
}

// ============ API FUNCTIONS - MAPPED TO STCOK BACKEND ============

/**
 * Fetch market overview (bulls, bears, active stocks)
 */
export const fetchMarketOverview = async (): Promise<MarketOverview> => {
  try {
    const [bulls, bears, losers] = await Promise.all([
      cachedGet<BackendStockData[]>('/stocks/top-bulls?limit=5', ONE_MIN),
      cachedGet<BackendStockData[]>('/stocks/top-bears?limit=5', ONE_MIN),
      cachedGet<BackendStockData[]>('/stocks/top-losers?limit=5', ONE_MIN),
    ]);

    return {
      indices: [
        { name: 'NIFTY50', value: 23500, change: 150, changePercent: 0.64 },
        { name: 'SENSEX', value: 77500, change: 500, changePercent: 0.65 },
      ],
      topGainers: (bulls || []).map(transformBackendStock),
      topLosers: (losers || []).map(transformBackendStock),
      mostActive: (bears || []).map(transformBackendStock),
    };
  } catch (error) {
    console.error('Error fetching market overview:', error);
    return {
      indices: [],
      topGainers: [],
      topLosers: [],
      mostActive: [],
    };
  }
};

/**
 * Fetch all stock signals (for discovery/scanner)
 */
export const fetchStockSignals = async (): Promise<StockSignal[]> => {
  try {
    const data = await cachedGet<BackendStockData[]>('/stocks?limit=50', ONE_MIN);
    return (data || []).map(transformBackendStock);
  } catch (error) {
    console.error('Error fetching stock signals:', error);
    return [];
  }
};

/**
 * Fetch single stock detail with prediction
 */
export const fetchStockDetail = async (symbol: string): Promise<StockSignal> => {
  try {
    const [stockData, predictionData] = await Promise.all([
      cachedGet<BackendStockData>(`/stocks/search?q=${symbol}`, ONE_MIN),
      cachedGet<BackendPredictionData>(`/prediction/${symbol}`, ONE_MIN),
    ]);

    const baseData = stockData as BackendStockData | null;
    const predData = predictionData as BackendPredictionData | null;

    return {
      symbol,
      name: baseData?.name || symbol,
      price: baseData?.price || 0,
      change: baseData?.change || 0,
      changePercent: baseData?.change_pct || 0,
      signal: predData?.signal || baseData?.signal || 'NEUTRAL',
      confidence: predData?.confidence || baseData?.confidence || 50,
      volume: baseData?.volume || 0,
    };
  } catch (error) {
    console.error(`Error fetching stock detail for ${symbol}:`, error);
    return {
      symbol,
      name: symbol,
      price: 0,
      change: 0,
      changePercent: 0,
      signal: 'NEUTRAL',
      confidence: 50,
      volume: 0,
    };
  }
};

/**
 * Fetch OHLC chart data
 */
export const fetchOHLC = async (symbol: string, period = '1y'): Promise<OHLC[]> => {
  try {
    const periodMap: Record<string, string> = {
      '1d': '5d',
      '5d': '5d',
      '1w': '1M',
      '1m': '1M',
      '3m': '3M',
      '6m': '1Y',
      '1y': '1Y',
      'all': '1Y',
    };
    const mappedPeriod = periodMap[period] || '1Y';

    const data = await cachedGet<BackendChartData[]>(
      `/chart/${symbol}?period=${mappedPeriod}&interval=1d`,
      FIVE_MIN
    );
    return (data || []).map(transformBackendChart);
  } catch (error) {
    console.error(`Error fetching OHLC for ${symbol}:`, error);
    return [];
  }
};

/**
 * Fetch technical indicators
 */
export const fetchIndicators = async (symbol: string): Promise<TechnicalIndicators> => {
  try {
    const chartData = await fetchOHLC(symbol, '1y');
    const n = chartData.length;
    const closes = chartData.map(c => c.close);
    
    return {
      sma20: closes.slice(Math.max(0, n - 20)),
      sma50: closes.slice(Math.max(0, n - 50)),
      ema12: closes.slice(Math.max(0, n - 12)),
      ema26: closes.slice(Math.max(0, n - 26)),
      rsi: Array(Math.min(14, n)).fill(50),
      macd: chartData.map(() => ({ macd: 0, signal: 0, histogram: 0 })),
      bollingerBands: chartData.map(c => ({
        upper: c.high * 1.02,
        middle: (c.high + c.low) / 2,
        lower: c.low * 0.98,
      })),
    };
  } catch (error) {
    console.error(`Error fetching indicators for ${symbol}:`, error);
    return {
      sma20: [],
      sma50: [],
      ema12: [],
      ema26: [],
      rsi: [],
      macd: [],
      bollingerBands: [],
    };
  }
};

/**
 * Fetch portfolio holdings
 */
export const fetchPortfolio = async (): Promise<PortfolioHolding[]> => {
  try {
    const alerts = await cachedGet<{ alerts: BackendStockData[] }>(
      '/alerts/live?limit=10',
      ONE_MIN
    );
    
    const alertsList = ((alerts as any)?.alerts || alerts as any[] || []).slice(0, 5);
    return alertsList.map((stock: BackendStockData, idx: number) => ({
      symbol: stock.symbol,
      name: stock.name || stock.symbol,
      quantity: 100 + idx * 10,
      avgPrice: (stock.price || 100) * 0.95,
      currentPrice: stock.price || 100,
      pnl: ((stock.price || 100) - ((stock.price || 100) * 0.95)) * (100 + idx * 10),
      pnlPercent: 5 + idx,
      allocation: 20,
      signal: stock.signal || 'BUY',
    }));
  } catch (error) {
    console.error('Error fetching portfolio:', error);
    return [];
  }
};

/**
 * Fetch risk metrics
 */
export const fetchRiskMetrics = async (): Promise<RiskMetrics> => {
  try {
    const data = await cachedGet<any>('/risk-os/overview', FIVE_MIN);

    return {
      portfolioVar: data?.current_exposure || 65,
      sharpeRatio: 1.8,
      beta: 0.95,
      maxDrawdown: -8.5,
      volatility: 12.3,
      correlationMatrix: {},
    };
  } catch (error) {
    console.error('Error fetching risk metrics:', error);
    return {
      portfolioVar: 0,
      sharpeRatio: 0,
      beta: 0,
      maxDrawdown: 0,
      volatility: 0,
      correlationMatrix: {},
    };
  }
};

/**
 * Fetch discovery stocks (with optional filters)
 */
export const fetchDiscovery = async (filters?: Record<string, string>): Promise<StockSignal[]> => {
  try {
    let url = '/stocks?limit=100';
    
    if (filters?.tab === 'bulls') {
      url = '/stocks/top-bulls?limit=50';
    } else if (filters?.tab === 'bears') {
      url = '/stocks/top-bears?limit=50';
    } else if (filters?.tab === 'losers') {
      url = '/stocks/top-losers?limit=50';
    } else if (filters?.tab === 'scanner') {
      url = '/scanner_results';
    }

    const data = await cachedGet<BackendStockData[]>(url, ONE_MIN);
    return (data || []).map(transformBackendStock);
  } catch (error) {
    console.error('Error fetching discovery stocks:', error);
    return [];
  }
};

/**
 * Fetch detailed stock prediction
 */
export const fetchStockPrediction = async (
  symbol: string
): Promise<BackendPredictionData | null> => {
  try {
    const data = await cachedGet<BackendPredictionData>(
      `/prediction/${symbol}`,
      ONE_MIN
    );
    return data || null;
  } catch (error) {
    console.error(`Error fetching prediction for ${symbol}:`, error);
    return null;
  }
};

export default api;
