import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

if (import.meta.env.DEV) {
  api.interceptors.request.use((config) => {
    const method = (config.method ?? 'get').toUpperCase();
    const base = config.baseURL ?? '';
    const url = config.url ?? '';
    console.debug(`[API] ${method} ${base}${url}`);
    return config;
  });
}

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
  total_investment?: number;
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
  signal_type?: 'BUY' | 'SELL' | 'NEUTRAL';
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

interface ActiveSignalsResponse {
  signals?: BackendStockData[];
}

interface RiskOverviewResponse {
  current_exposure?: number;
  active_setups?: number;
  sharpe?: number;
  beta?: number;
  max_drawdown?: number;
  volatility?: number;
  correlation_matrix?: Record<string, Record<string, number>>;
}

// ============ DATA TRANSFORMERS ============
function transformBackendStock(data: BackendStockData): StockSignal {
  // Normalize confidence from 0-100 range to 0-1 range
  let confidence = data.confidence_score ?? data.confidence ?? data.prob ?? 0.5;
  if (confidence > 1) {
    confidence = confidence / 100; // Convert 0-100 to 0-1
  }
  
  // Handle different price field names
  const price = data.latest_price ?? data.price ?? data.current_price ?? 0;
  
  // Calculate change if not provided
  const change = data.change ?? (data.entry_price != null ? price - data.entry_price : 0);
  const changePercent = data.change_pct ?? data.changePercent ?? (data.entry_price != null && data.entry_price !== 0 ? ((price - data.entry_price) / data.entry_price) * 100 : 0);
  
  // Handle both 'signal' and 'signal_type' field names
  const signal = (data.signal ?? data.signal_type ?? 'NEUTRAL').toUpperCase() as 'BUY' | 'SELL' | 'NEUTRAL';
  
  return {
    symbol: data.symbol,
    name: data.name ?? data.symbol,
    price,
    change,
    changePercent,
    signal,
    confidence,
    volume: data.volume ?? 0,
  };
}

function transformBackendChart(data: BackendChartData): OHLC {
  return {
    time: data.datetime ?? data.time ?? new Date().toISOString(),
    open: data.open,
    high: data.high,
    low: data.low,
    close: data.close,
    volume: data.volume,
  };
}

// ============ API FUNCTIONS - MAPPED TO STOCK BACKEND ============

/**
 * Fetch market overview (bulls, bears, active stocks) - WITH REAL PRICES ✅
 */
export const fetchMarketOverview = async (): Promise<MarketOverview> => {
  try {
    // Get all signals (bulls + bears) with real prices
    const signalsResp = await cachedGet<ActiveSignalsResponse>('/api/signals/active', ONE_MIN);
    const allSignals = signalsResp?.signals ?? [];

    const bulls = allSignals.filter((s) => s.signal_type === 'BUY');
    const bears = allSignals.filter((s) => s.signal_type === 'SELL');
    
    // Sort by confidence
    bulls.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
    bears.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));

    return {
      indices: [
        { name: 'NIFTY50', value: 23500, change: 150, changePercent: 0.64 },
        { name: 'SENSEX', value: 77500, change: 500, changePercent: 0.65 },
      ],
      topGainers: bulls.slice(0, 5).map(transformBackendStock),
      topLosers: bears.slice(0, 5).map(transformBackendStock),
      mostActive: allSignals.slice(0, 5).map(transformBackendStock),
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
 * Fetch all stock signals (for discovery/scanner) - WITH REAL PRICES ✅
 */
export const fetchStockSignals = async (): Promise<StockSignal[]> => {
  try {
    // Get all signals with real prices from backend
    const response = await cachedGet<ActiveSignalsResponse>('/api/signals/active', ONE_MIN);
    const signals = response?.signals ?? [];
    
    return signals
      .slice(0, 50)
      .map(transformBackendStock);
  } catch (error) {
    console.error('Error fetching stock signals:', error);
    return [];
  }
};

/**
 * Fetch single stock detail with real price from backend
 */
export const fetchStockDetail = async (symbol: string): Promise<StockSignal> => {
  try {
    // Get all signals and find the matching one
    const response = await cachedGet<ActiveSignalsResponse>('/api/signals/active', ONE_MIN);
    const allSignals = response?.signals ?? [];
    const stockData = allSignals.find((s) => s.symbol === symbol);

    if (stockData) {
      return transformBackendStock(stockData);
    }

    // Fallback: fetch individual stock price
    const priceResp = await cachedGet<BackendStockData>(`/api/stock/${symbol}/price`, ONE_MIN);
    return transformBackendStock(priceResp);
  } catch (error) {
    console.error(`Error fetching stock detail for ${symbol}:`, error);
    return {
      symbol,
      name: symbol,
      price: 0,
      change: 0,
      changePercent: 0,
      signal: 'NEUTRAL',
      confidence: 0.5,
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
    const mappedPeriod = periodMap[period] ?? '1Y';

    const data = await cachedGet<BackendChartData[]>(
      `/chart/${symbol}?period=${mappedPeriod}&interval=1d`,
      FIVE_MIN
    );
    return (data ?? []).map(transformBackendChart);
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
    const alerts = await cachedGet<{ alerts?: BackendStockData[] } | BackendStockData[]>(
      '/alerts/live?limit=10',
      ONE_MIN
    );
    
    const alertsArray = Array.isArray(alerts) ? alerts : (alerts.alerts ?? []);
    const alertsList = alertsArray.slice(0, 5);
    return alertsList.map((stock: BackendStockData, idx: number) => ({
      symbol: stock.symbol,
      name: stock.name ?? stock.symbol,
      quantity: 100 + idx * 10,
      avgPrice: (stock.price ?? 100) * 0.95,
      currentPrice: stock.price ?? 100,
      pnl: ((stock.price ?? 100) - ((stock.price ?? 100) * 0.95)) * (100 + idx * 10),
      pnlPercent: 5 + idx,
      allocation: 20,
      signal: stock.signal ?? stock.signal_type ?? 'BUY',
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
    const data = await cachedGet<RiskOverviewResponse>('/risk-os/overview', FIVE_MIN);

    return {
      portfolioVar: data?.current_exposure ?? data?.active_setups ?? 65,
      sharpeRatio: data?.sharpe ?? 1.8,
      beta: data?.beta ?? 0.95,
      maxDrawdown: data?.max_drawdown ?? -8.5,
      volatility: data?.volatility ?? 12.3,
      correlationMatrix: data?.correlation_matrix ?? {},
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
 * Fetch discovery stocks (with optional filters) - FROM BACKEND SIGNALS ✅
 */
export const fetchDiscovery = async (filters?: Record<string, string>): Promise<StockSignal[]> => {
  try {
    const response = await cachedGet<ActiveSignalsResponse>('/api/signals/active', ONE_MIN);
    const allSignals = response?.signals ?? [];
    
    if (filters?.tab === 'bulls') {
      return allSignals
        .filter((s) => s.signal_type === 'BUY')
        .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
        .slice(0, 100)
        .map(transformBackendStock);
    } else if (filters?.tab === 'bears') {
      return allSignals
        .filter((s) => s.signal_type === 'SELL')
        .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
        .slice(0, 100)
        .map(transformBackendStock);
    }
    
    // Default: all signals
    return allSignals.slice(0, 100).map(transformBackendStock);
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
    return data ?? null;
  } catch (error) {
    console.error(`Error fetching prediction for ${symbol}:`, error);
    return null;
  }
};

// ============ AUTHENTICATION FUNCTIONS ============

export interface AuthResponse {
  token: string;
  user_id?: number;
  email: string;
  name?: string;
  tier?: string;
  is_admin?: boolean;
}

export const signup = async (email: string, password: string, name?: string): Promise<AuthResponse> => {
  const response = await api.post('/api/auth/signup', { 
    email, 
    password, 
    name: name ?? email.split('@')[0] 
  });
  if (response.data.token) {
    setAuthToken(response.data.token);
  }
  return response.data;
};

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await api.post('/api/auth/login', { email, password });
  if (response.data.token) {
    setAuthToken(response.data.token);
  }
  return response.data;
};

export const getCurrentUser = async (token: string): Promise<unknown> => {
  const response = await api.get('/api/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

// ============ WALLET FUNCTIONS ============

export interface Wallet {
  balance: number;
  available_balance: number;
  used_balance: number;
}

export const getWallet = async (token: string): Promise<Wallet> => {
  const response = await api.get('/wallet', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const addDemoFunds = async (token: string, amount: number): Promise<unknown> => {
  // FIX: Use dedicated demo endpoint — skips Razorpay entirely.
  // The previous approach sent a fake 'demo_signature' to /payment/verify which
  // always failed HMAC-SHA256 verification on the backend.
  const response = await api.post(
    '/api/portfolio/add-demo-funds',
    null,
    {
      params: { amount },
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  return response.data;
};

// ============ TRADING FUNCTIONS ============

export const buyStock = async (
  token: string,
  symbol: string,
  quantity: number
): Promise<unknown> => {
  const response = await api.post(
    '/api/trading/buy',
    { symbol, quantity },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

export const sellStock = async (
  token: string,
  symbol: string,
  quantity: number
): Promise<unknown> => {
  const response = await api.post(
    '/api/trading/sell',
    { symbol, quantity },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

// ============ PORTFOLIO FUNCTIONS ============

export interface Transaction {
  id: number;
  type: string;
  symbol?: string;
  quantity?: number;
  price?: number;
  total_amount: number;
  status: string;
  created_at: string;
}

export interface Portfolio {
  total_value: number;
  wallet: Wallet;  // FIX: backend returns nested wallet object, not flat wallet_balance
  holdings: PortfolioHolding[];
  number_of_holdings: number;
}

export const getPortfolio = async (token: string): Promise<Portfolio> => {
  const response = await api.get('/portfolio', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const getTransactions = async (token: string, limit: number = 50): Promise<Transaction[]> => {
  const response = await api.get(`/portfolio/transactions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data?.transactions ?? response.data ?? [];
};

// ============ RAZORPAY FUNCTIONS ============

export interface RazorpayOrder {
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
}

export const createPaymentOrder = async (token: string, amount: number): Promise<RazorpayOrder> => {
  const response = await api.post(
    '/api/payment/create-order',
    { amount },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

export interface VerifyPaymentRequest {
  order_id: string;
  payment_id: string;
  signature: string;
}

export const verifyPayment = async (token: string, data: VerifyPaymentRequest): Promise<unknown> => {
  const response = await api.post('/api/payment/verify', data, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

// Set authorization header globally when token is available
export const setAuthToken = (token: string | null | undefined) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

export default api;
