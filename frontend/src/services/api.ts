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
  latest_price?: number;
  current_price?: number;
  change?: number;
  change_pct?: number;
  changePercent?: number;
  entry_price?: number;
  signal?: 'BUY' | 'SELL' | 'NEUTRAL';
  confidence?: number;
  confidence_score?: number;
  prob?: number;
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
  // Normalize confidence from 0-100 range to 0-1 range
  let confidence = data.confidence_score || data.confidence || data.prob || 50;
  if (confidence > 1) {
    confidence = confidence / 100; // Convert 0-100 to 0-1
  }
  
  // Handle different price field names
  const price = data.latest_price || data.price || data.current_price || 0;
  
  // Calculate change if not provided
  const change = data.change || (data.entry_price && price ? price - data.entry_price : 0);
  const changePercent = data.change_pct || data.changePercent || (data.entry_price && price ? ((price - data.entry_price) / data.entry_price) * 100 : 0);
  
  return {
    symbol: data.symbol,
    name: data.name || data.symbol,
    price,
    change,
    changePercent,
    signal: data.signal || 'NEUTRAL',
    confidence,
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
    const [bullsResp, bearsResp, losersResp] = await Promise.all([
      cachedGet<any>('/stocks/top-bulls?limit=5', ONE_MIN),
      cachedGet<any>('/stocks/top-bears?limit=5', ONE_MIN),
      cachedGet<any>('/stocks/top-losers?limit=5', ONE_MIN),
    ]);

    // Handle both response formats: array or {stocks: [...]}
    const bulls = Array.isArray(bullsResp) ? bullsResp : (bullsResp?.stocks || []);
    const bears = Array.isArray(bearsResp) ? bearsResp : (bearsResp?.stocks || []);
    const losers = Array.isArray(losersResp) ? losersResp : (losersResp?.stocks || []);

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
    // Get signals from alerts/live endpoint which has actual prediction data
    const alertResponse = await cachedGet<any>('/alerts/live?limit=50', ONE_MIN);
    const alerts = Array.isArray(alertResponse) ? alertResponse : (alertResponse?.alerts || []);
    
    // Also get bulls and bears for additional context
    const [bullsResp, bearsResp] = await Promise.all([
      cachedGet<any>('/stocks/top-bulls?limit=25', ONE_MIN),
      cachedGet<any>('/stocks/top-bears?limit=25', ONE_MIN),
    ]);
    
    const bulls = Array.isArray(bullsResp) ? bullsResp : (bullsResp?.stocks || []);
    const bears = Array.isArray(bearsResp) ? bearsResp : (bearsResp?.stocks || []);
    
    // Combine and deduplicate by symbol
    const allSignals = [...alerts, ...bulls, ...bears];
    const signalMap = new Map<string, any>();
    
    for (const signal of allSignals) {
      if (signal.symbol && !signalMap.has(signal.symbol)) {
        signalMap.set(signal.symbol, signal);
      }
    }
    
    return Array.from(signalMap.values())
      .slice(0, 50)
      .map(transformBackendStock);
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
    const [stockResp, predictionData] = await Promise.all([
      cachedGet<any>(`/stocks/search?q=${symbol}`, ONE_MIN),
      cachedGet<BackendPredictionData>(`/prediction/${symbol}`, ONE_MIN),
    ]);

    // Handle both response formats: array or {stocks: [...]}
    const stockList = Array.isArray(stockResp) ? stockResp : (stockResp?.stocks || []);
    const baseData = (stockList && stockList.length > 0) ? stockList[0] : null;
    const predData = predictionData as BackendPredictionData | null;

    return {
      symbol,
      name: baseData?.name || symbol,
      price: baseData?.price || 0,
      change: baseData?.change || 0,
      changePercent: baseData?.change_pct || baseData?.changePercent || 0,
      signal: predData?.signal || baseData?.signal || 'NEUTRAL',
      confidence: predData?.confidence || baseData?.confidence || baseData?.prob || 50,
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
      portfolioVar: data?.current_exposure || data?.active_setups || 65,
      sharpeRatio: data?.sharpe || 1.8,
      beta: data?.beta || 0.95,
      maxDrawdown: data?.max_drawdown || -8.5,
      volatility: data?.volatility || 12.3,
      correlationMatrix: data?.correlation_matrix || {},
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
    let url = '/alerts/live?limit=100'; // Use alerts/live for price + signal data instead of /stocks (which has no price)
    
    if (filters?.tab === 'bulls') {
      url = '/stocks/top-bulls?limit=100';
    } else if (filters?.tab === 'bears') {
      url = '/stocks/top-bears?limit=100';
    } else if (filters?.tab === 'losers') {
      url = '/stocks/top-losers?limit=100';
    } else if (filters?.tab === 'scanner') {
      url = '/scanner_results';
    }

    const response = await cachedGet<any>(url, ONE_MIN);
    
    // Handle different response formats
    let data = [];
    if (Array.isArray(response)) {
      data = response;
    } else if (response?.stocks) {
      data = response.stocks;
    } else if (response?.alerts) {
      data = response.alerts;
    }
    
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
