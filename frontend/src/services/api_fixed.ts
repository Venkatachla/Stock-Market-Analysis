/**
 * FIXED API Service - All endpoints using fetch with proper CORS headers
 * Location: frontend/src/services/api_fixed.ts
 */

const API_BASE_URL = 'http://localhost:8000';

// Add request/response logging
const logRequest = (method: string, url: string, body?: any) => {
  console.log(`📤 [${method}] ${url}`, body || '');
};

const logResponse = (status: number, data: any) => {
  console.log(`📥 [${status}]`, data);
};

const logError = (error: any) => {
  console.error('❌ API Error:', error);
};

/**
 * Generic fetch wrapper with proper CORS headers
 */
async function apiCall<T>(
  endpoint: string,
  method: string = 'GET',
  body?: any,
  token?: string
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const options: RequestInit = {
    method,
    headers,
    mode: 'cors',
    credentials: 'include',
  };

  if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    options.body = JSON.stringify(body);
  }

  logRequest(method, url, body);

  try {
    const response = await fetch(url, options);
    
    // Handle non-JSON responses
    const contentType = response.headers.get('content-type');
    let data: any;

    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    logResponse(response.status, data);

    if (!response.ok) {
      logError({
        status: response.status,
        statusText: response.statusText,
        data
      });
      throw new Error(data?.detail || `API Error: ${response.status} ${response.statusText}`);
    }

    return data as T;
  } catch (error) {
    logError(error);
    throw error;
  }
}

// ==================== AUTH ENDPOINTS ====================

export interface AuthResponse {
  token: string;
  user_id: number;
  email: string;
  name: string;
  tier: string;
  is_admin: boolean;
}

/**
 * Sign up a new user
 */
export async function signup(
  email: string,
  password: string,
  name: string
): Promise<AuthResponse> {
  return apiCall<AuthResponse>('/api/auth/signup', 'POST', {
    email,
    password,
    name,
  });
}

/**
 * Login user
 */
export async function login(email: string, password: string): Promise<AuthResponse> {
  return apiCall<AuthResponse>('/api/auth/login', 'POST', {
    email,
    password,
  });
}

/**
 * Get current user info
 */
export async function getMe(token: string): Promise<any> {
  return apiCall('/api/auth/me', 'GET', undefined, token);
}

// ==================== SIGNAL ENDPOINTS ====================

export interface StockSignal {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  signal_type: 'BUY' | 'SELL';
  confidence: number;
  reason: string;
  volume?: number;
}

export interface SignalsResponse {
  signals: StockSignal[];
  total: number;
  buy_count: number;
  sell_count: number;
  timestamp: string;
}

/**
 * Fetch all active buy/sell signals with real prices
 */
export async function fetchMarketOverview(): Promise<SignalsResponse> {
  return apiCall<SignalsResponse>('/api/signals/active');
}

/**
 * Fetch stock signals (same as market overview)
 */
export async function fetchStockSignals(): Promise<SignalsResponse> {
  return apiCall<SignalsResponse>('/api/signals/active');
}

/**
 * Fetch single stock detail with signal
 */
export async function fetchStockDetail(symbol: string): Promise<StockSignal | null> {
  try {
    const response = await fetchMarketOverview();
    return response.signals.find(s => s.symbol === symbol) || null;
  } catch (error) {
    console.error(`Error fetching detail for ${symbol}:`, error);
    return null;
  }
}

// ==================== PORTFOLIO ENDPOINTS ====================

export interface Holding {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  total_investment: number;
  current_value: number;
  pnl: number;
  pnl_percent: number;
}

export interface Portfolio {
  total_value: number;
  wallet_balance: number;
  holdings: Holding[];
  number_of_holdings: number;
}

/**
 * Fetch user portfolio
 */
export async function fetchPortfolio(token: string): Promise<Portfolio> {
  return apiCall<Portfolio>('/portfolio', 'GET', undefined, token);
}

/**
 * Fetch wallet balance
 */
export async function fetchWallet(token: string): Promise<any> {
  return apiCall('/wallet', 'GET', undefined, token);
}

/**
 * Fetch transaction history
 */
export async function fetchTransactions(token: string): Promise<any> {
  return apiCall('/portfolio/transactions', 'GET', undefined, token);
}

// ==================== TRADING ENDPOINTS ====================

export interface TradeResponse {
  status: string;
  transaction_id: number;
  symbol: string;
  quantity: number;
  price: number;
  total: number;
  timestamp: string;
}

/**
 * Buy stock
 */
export async function buyStock(
  symbol: string,
  quantity: number,
  token: string
): Promise<TradeResponse> {
  return apiCall<TradeResponse>(
    '/api/trading/buy',
    'POST',
    { symbol, quantity },
    token
  );
}

/**
 * Sell stock
 */
export async function sellStock(
  symbol: string,
  quantity: number,
  token: string
): Promise<TradeResponse> {
  return apiCall<TradeResponse>(
    '/api/trading/sell',
    'POST',
    { symbol, quantity },
    token
  );
}

// ==================== PAYMENT ENDPOINTS ====================

export interface OrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  timestamp: string;
}

/**
 * Create payment order
 */
export async function createPaymentOrder(
  amount: number,
  token: string
): Promise<OrderResponse> {
  return apiCall<OrderResponse>(
    '/api/payment/create-order',
    'POST',
    { amount },
    token
  );
}

/**
 * Verify payment
 */
export async function verifyPayment(
  paymentData: any,
  token: string
): Promise<any> {
  return apiCall(
    '/api/payment/verify',
    'POST',
    paymentData,
    token
  );
}

// ==================== SYSTEM ENDPOINTS ====================

/**
 * Health check
 */
export async function healthCheck(): Promise<any> {
  return apiCall('/health');
}

/**
 * Get API info
 */
export async function getApiInfo(): Promise<any> {
  return apiCall('/');
}

export default {
  // Auth
  signup,
  login,
  getMe,

  // Signals
  fetchMarketOverview,
  fetchStockSignals,
  fetchStockDetail,

  // Portfolio
  fetchPortfolio,
  fetchWallet,
  fetchTransactions,

  // Trading
  buyStock,
  sellStock,

  // Payment
  createPaymentOrder,
  verifyPayment,

  // System
  healthCheck,
  getApiInfo,
};
