export type Regime = 'BULL' | 'BEAR' | 'SIDEWAYS' | 'UNKNOWN';

export interface StockPrediction {
  symbol: string;
  prob_up: number;
  prob_down: number;
  confidence: number;
  signal: 'BUY' | 'SELL' | 'HOLD';
  regime: Regime;
  sentiment_score: number;
  latest_price: number;
  date: string;
}

export interface BacktestResult {
  total_return: number;
  win_rate: number;
  max_drawdown: number;
  sharpe: number;
  sortino: number;
  profit_factor: number;
  avg_trade_return: number;
  num_trades: number;
  monthly_returns: Record<string, number>;
  equity_curve: number[];
  drawdown_curve: number[];
}

export interface PaperTrade {
  id: string;
  symbol: string;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  pnl: number;
  return_pct: number;
  entry_date: string;
  exit_date?: string;
  status: 'OPEN' | 'CLOSED';
}

export interface Signal {
  symbol: string;
  prob_up: number;
  sector: string;
  regime: Regime;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  timestamp: string;
}

export interface TechnicalIndicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  sma_20: number;
  sma_50: number;
  sma_200: number;
  bb_high: number;
  bb_low: number;
  bb_mid: number;
  atr: number;
}

export interface NewsItem {
  headline: string;
  sentiment: number;
  source: string;
  timestamp: string;
}
