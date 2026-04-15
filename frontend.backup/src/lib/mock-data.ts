import { StockPrediction, BacktestResult, PaperTrade, Signal, NewsItem, Regime } from '@/types';

export const mockPredictions: StockPrediction[] = [
  {
    symbol: 'RELIANCE',
    prob_up: 0.72,
    prob_down: 0.28,
    confidence: 0.85,
    signal: 'BUY',
    regime: 'BULL',
    sentiment_score: 0.68,
    latest_price: 2850.50,
    date: new Date().toISOString().split('T')[0],
  },
  {
    symbol: 'TCS',
    prob_up: 0.65,
    prob_down: 0.35,
    confidence: 0.78,
    signal: 'BUY',
    regime: 'BULL',
    sentiment_score: 0.55,
    latest_price: 4120.25,
    date: new Date().toISOString().split('T')[0],
  },
  {
    symbol: 'INFY',
    prob_up: 0.58,
    prob_down: 0.42,
    confidence: 0.72,
    signal: 'HOLD',
    regime: 'SIDEWAYS',
    sentiment_score: 0.45,
    latest_price: 2340.75,
    date: new Date().toISOString().split('T')[0],
  },
  {
    symbol: 'WIPRO',
    prob_up: 0.42,
    prob_down: 0.58,
    confidence: 0.81,
    signal: 'SELL',
    regime: 'BEAR',
    sentiment_score: 0.32,
    latest_price: 385.90,
    date: new Date().toISOString().split('T')[0],
  },
  {
    symbol: 'HDFC',
    prob_up: 0.69,
    prob_down: 0.31,
    confidence: 0.87,
    signal: 'BUY',
    regime: 'BULL',
    sentiment_score: 0.72,
    latest_price: 2620.00,
    date: new Date().toISOString().split('T')[0],
  },
];

export const mockSignals: Signal[] = [
  {
    symbol: 'RELIANCE',
    prob_up: 0.72,
    sector: 'Energy',
    regime: 'BULL',
    signal_type: 'BUY',
    confidence: 0.85,
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    symbol: 'TCS',
    prob_up: 0.65,
    sector: 'Tech',
    regime: 'BULL',
    signal_type: 'BUY',
    confidence: 0.78,
    timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
  },
  {
    symbol: 'HDFC',
    prob_up: 0.69,
    sector: 'Finance',
    regime: 'BULL',
    signal_type: 'BUY',
    confidence: 0.87,
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
  },
  {
    symbol: 'WIPRO',
    prob_up: 0.42,
    sector: 'Tech',
    regime: 'BEAR',
    signal_type: 'SELL',
    confidence: 0.81,
    timestamp: new Date(Date.now() - 20 * 60000).toISOString(),
  },
  {
    symbol: 'INFY',
    prob_up: 0.58,
    sector: 'Tech',
    regime: 'SIDEWAYS',
    signal_type: 'HOLD',
    confidence: 0.72,
    timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
  },
  {
    symbol: 'ITC',
    prob_up: 0.68,
    sector: 'Retail',
    regime: 'BULL',
    signal_type: 'BUY',
    confidence: 0.76,
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
  },
  {
    symbol: 'SUNPHARMA',
    prob_up: 0.55,
    sector: 'Pharma',
    regime: 'SIDEWAYS',
    signal_type: 'HOLD',
    confidence: 0.68,
    timestamp: new Date(Date.now() - 35 * 60000).toISOString(),
  },
  {
    symbol: 'MARUTI',
    prob_up: 0.45,
    sector: 'Auto',
    regime: 'BEAR',
    signal_type: 'SELL',
    confidence: 0.74,
    timestamp: new Date(Date.now() - 40 * 60000).toISOString(),
  },
  {
    symbol: 'BAJAJFINSV',
    prob_up: 0.71,
    sector: 'Finance',
    regime: 'BULL',
    signal_type: 'BUY',
    confidence: 0.83,
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
  },
  {
    symbol: 'TITAN',
    prob_up: 0.64,
    sector: 'Retail',
    regime: 'BULL',
    signal_type: 'BUY',
    confidence: 0.79,
    timestamp: new Date(Date.now() - 50 * 60000).toISOString(),
  },
];

export const mockBacktestResult: BacktestResult = {
  total_return: 0.2450,
  win_rate: 0.6875,
  max_drawdown: 0.1250,
  sharpe: 1.8520,
  sortino: 2.4510,
  profit_factor: 1.8750,
  avg_trade_return: 0.0382,
  num_trades: 64,
  monthly_returns: {
    '2025-09': 0.023,
    '2025-10': 0.018,
    '2025-11': 0.035,
    '2025-12': 0.031,
    '2026-01': 0.021,
    '2026-02': 0.026,
    '2026-03': 0.018,
  },
  equity_curve: [
    100000, 102300, 104100, 103200, 106500, 108900, 112400, 115800, 118200, 120500, 119300, 122450, 124500,
  ],
  drawdown_curve: [
    0, -0.002, -0.001, -0.0125, -0.001, 0, 0, 0, 0, 0, -0.012, -0.005, 0,
  ],
};

export const mockPaperTrades: PaperTrade[] = [
  {
    id: '1',
    symbol: 'RELIANCE',
    entry_price: 2800,
    exit_price: 2850.5,
    quantity: 10,
    pnl: 505,
    return_pct: 0.018,
    entry_date: '2026-03-10',
    exit_date: '2026-03-14',
    status: 'CLOSED',
  },
  {
    id: '2',
    symbol: 'TCS',
    entry_price: 4100,
    quantity: 5,
    pnl: 101.25,
    return_pct: 0.0049,
    entry_date: '2026-03-12',
    status: 'OPEN',
  },
  {
    id: '3',
    symbol: 'HDFC',
    entry_price: 2550,
    exit_price: 2620,
    quantity: 8,
    pnl: 560,
    return_pct: 0.0275,
    entry_date: '2026-03-08',
    exit_date: '2026-03-13',
    status: 'CLOSED',
  },
  {
    id: '4',
    symbol: 'ITC',
    entry_price: 395,
    exit_price: 412.5,
    quantity: 25,
    pnl: 437.5,
    return_pct: 0.0443,
    entry_date: '2026-03-05',
    exit_date: '2026-03-14',
    status: 'CLOSED',
  },
  {
    id: '5',
    symbol: 'INFY',
    entry_price: 2350,
    quantity: 6,
    pnl: -36,
    return_pct: -0.0255,
    entry_date: '2026-03-11',
    status: 'OPEN',
  },
];

export const mockNewsItems: NewsItem[] = [
  {
    headline: 'Reliance Q4 profit beats expectations',
    sentiment: 0.85,
    source: 'Reuters',
    timestamp: new Date(Date.now() - 2 * 60 * 60000).toISOString(),
  },
  {
    headline: 'TCS announces dividend hike',
    sentiment: 0.72,
    source: 'ET',
    timestamp: new Date(Date.now() - 4 * 60 * 60000).toISOString(),
  },
  {
    headline: 'Tech sector faces headwinds',
    sentiment: -0.65,
    source: 'Bloomberg',
    timestamp: new Date(Date.now() - 6 * 60 * 60000).toISOString(),
  },
  {
    headline: 'HDFC merger progresses on track',
    sentiment: 0.58,
    source: 'ET',
    timestamp: new Date(Date.now() - 8 * 60 * 60000).toISOString(),
  },
];

export const mockStockData = (symbol: string) => {
  const basePrice = mockPredictions.find(p => p.symbol === symbol)?.latest_price || 2500;
  const data = [];
  for (let i = 120; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const variation = (Math.random() - 0.5) * 100;
    data.push({
      date: date.toISOString().split('T')[0],
      close: basePrice + variation,
      open: basePrice + variation - 20,
      high: basePrice + variation + 30,
      low: basePrice + variation - 45,
      volume: Math.floor(Math.random() * 5000000) + 1000000,
    });
  }
  return data;
};

export const mockRegime: Regime = 'BULL';

export const mockSentiment = {
  bullish: 0.65,
  bearish: 0.20,
  neutral: 0.15,
  score: 0.58,
};
