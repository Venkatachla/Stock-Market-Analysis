// ============================================================
// MOCK DATA — Comprehensive trading dashboard data
// ============================================================

export interface Prediction {
  symbol: string;
  price: number;
  ml_pred: number;
  probability: number;
  change_pct: number;
  recommendation: "Strong Buy" | "Buy" | "Hold" | "Sell" | "Strong Sell";
  volume: string;
  marketCap: string;
  high52w: number;
  low52w: number;
}

export interface Signal {
  id: string;
  symbol: string;
  type: "BUY" | "SELL";
  confidence: number;
  entryPrice: number;
  targetPrice: number;
  stopLoss: number;
  timestamp: string;
  timeAgo: string;
  accuracy?: number;
}

export interface BacktestStrategy {
  id: string;
  name: string;
  initialCapital: number;
  finalValue: number;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  trades: number;
}

export interface PaperPosition {
  symbol: string;
  shares: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
  status: "Long" | "Short";
}

export interface Trade {
  id: string;
  symbol: string;
  type: "Buy" | "Sell";
  quantity: number;
  price: number;
  total: number;
  timestamp: string;
  pnl?: number;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  time: string;
  sentiment: "positive" | "negative" | "neutral";
}

export const mockRegime = { regime: "Bull" as const, confidence: 78 };

export const mockSentiment = { sentiment: 72, trend: "Improving" };

export const mockPortfolioStats = {
  totalValue: 1247850.32,
  todayGain: 12450.18,
  todayGainPct: 1.01,
  winRate: 67.4,
  sharpeRatio: 2.14,
  cashAvailable: 85420.00,
  buyingPower: 170840.00,
};

export const mockPredictions: Prediction[] = [
  { symbol: "AAPL", price: 178.42, ml_pred: 192.15, probability: 82, change_pct: 7.69, recommendation: "Strong Buy", volume: "52.3M", marketCap: "₹233L Cr", high52w: 199.62, low52w: 143.90 },
  { symbol: "MSFT", price: 378.91, ml_pred: 395.20, probability: 76, change_pct: 4.30, recommendation: "Buy", volume: "28.1M", marketCap: "₹233L Cr", high52w: 384.30, low52w: 309.45 },
  { symbol: "GOOGL", price: 141.80, ml_pred: 155.30, probability: 71, change_pct: 9.52, recommendation: "Buy", volume: "31.7M", marketCap: "₹141L Cr", high52w: 153.78, low52w: 115.83 },
  { symbol: "TSLA", price: 248.50, ml_pred: 232.10, probability: 38, change_pct: -6.60, recommendation: "Sell", volume: "118.5M", marketCap: "₹65L Cr", high52w: 299.29, low52w: 138.80 },
  { symbol: "NVDA", price: 495.22, ml_pred: 548.00, probability: 85, change_pct: 10.66, recommendation: "Strong Buy", volume: "45.2M", marketCap: "₹99L Cr", high52w: 505.48, low52w: 262.20 },
  { symbol: "AMZN", price: 153.42, ml_pred: 165.80, probability: 74, change_pct: 8.07, recommendation: "Buy", volume: "56.8M", marketCap: "₹133L Cr", high52w: 161.73, low52w: 118.35 },
  { symbol: "META", price: 326.49, ml_pred: 345.00, probability: 69, change_pct: 5.67, recommendation: "Buy", volume: "19.4M", marketCap: "₹69L Cr", high52w: 340.47, low52w: 225.39 },
  { symbol: "JPM", price: 158.72, ml_pred: 148.50, probability: 35, change_pct: -6.44, recommendation: "Sell", volume: "12.1M", marketCap: "₹38L Cr", high52w: 172.96, low52w: 135.19 },
];

export const mockSignals: Signal[] = [
  { id: "s1", symbol: "NVDA", type: "BUY", confidence: 92, entryPrice: 495.22, targetPrice: 548.00, stopLoss: 470.00, timestamp: "2026-03-14T09:32:00Z", timeAgo: "2h ago" },
  { id: "s2", symbol: "AAPL", type: "BUY", confidence: 85, entryPrice: 178.42, targetPrice: 192.15, stopLoss: 172.00, timestamp: "2026-03-14T09:15:00Z", timeAgo: "2h ago" },
  { id: "s3", symbol: "TSLA", type: "SELL", confidence: 78, entryPrice: 248.50, targetPrice: 220.00, stopLoss: 262.00, timestamp: "2026-03-14T08:45:00Z", timeAgo: "3h ago" },
  { id: "s4", symbol: "GOOGL", type: "BUY", confidence: 74, entryPrice: 141.80, targetPrice: 155.30, stopLoss: 135.00, timestamp: "2026-03-14T08:30:00Z", timeAgo: "3h ago" },
  { id: "s5", symbol: "AMZN", type: "BUY", confidence: 81, entryPrice: 153.42, targetPrice: 165.80, stopLoss: 147.00, timestamp: "2026-03-14T08:00:00Z", timeAgo: "4h ago" },
  { id: "s6", symbol: "JPM", type: "SELL", confidence: 72, entryPrice: 158.72, targetPrice: 148.50, stopLoss: 165.00, timestamp: "2026-03-14T07:30:00Z", timeAgo: "4h ago" },
  { id: "s7", symbol: "META", type: "BUY", confidence: 68, entryPrice: 326.49, targetPrice: 345.00, stopLoss: 315.00, timestamp: "2026-03-14T07:00:00Z", timeAgo: "5h ago" },
  { id: "s8", symbol: "MSFT", type: "BUY", confidence: 79, entryPrice: 378.91, targetPrice: 395.20, stopLoss: 370.00, timestamp: "2026-03-14T06:45:00Z", timeAgo: "5h ago" },
  { id: "s9", symbol: "AMD", type: "BUY", confidence: 66, entryPrice: 118.45, targetPrice: 132.00, stopLoss: 112.00, timestamp: "2026-03-13T15:00:00Z", timeAgo: "18h ago" },
  { id: "s10", symbol: "CRM", type: "SELL", confidence: 61, entryPrice: 215.30, targetPrice: 198.00, stopLoss: 225.00, timestamp: "2026-03-13T14:30:00Z", timeAgo: "19h ago" },
  { id: "s11", symbol: "DIS", type: "BUY", confidence: 58, entryPrice: 92.45, targetPrice: 105.00, stopLoss: 87.00, timestamp: "2026-03-13T13:00:00Z", timeAgo: "20h ago" },
  { id: "s12", symbol: "NFLX", type: "SELL", confidence: 55, entryPrice: 485.20, targetPrice: 450.00, stopLoss: 500.00, timestamp: "2026-03-13T12:00:00Z", timeAgo: "21h ago" },
];

export const mockBacktestStrategies: BacktestStrategy[] = [
  { id: "b1", name: "Momentum + RSI Crossover", initialCapital: 100000, finalValue: 187450, totalReturn: 87.45, sharpeRatio: 2.31, maxDrawdown: -12.4, winRate: 68.2, trades: 342 },
  { id: "b2", name: "Mean Reversion (Bollinger)", initialCapital: 100000, finalValue: 156230, totalReturn: 56.23, sharpeRatio: 1.87, maxDrawdown: -18.7, winRate: 62.1, trades: 518 },
  { id: "b3", name: "MACD + Volume Breakout", initialCapital: 100000, finalValue: 143890, totalReturn: 43.89, sharpeRatio: 1.54, maxDrawdown: -22.3, winRate: 57.8, trades: 276 },
  { id: "b4", name: "ML Ensemble (XGBoost)", initialCapital: 100000, finalValue: 212340, totalReturn: 112.34, sharpeRatio: 2.78, maxDrawdown: -9.8, winRate: 71.5, trades: 198 },
  { id: "b5", name: "Pairs Trading (Statistical)", initialCapital: 100000, finalValue: 134560, totalReturn: 34.56, sharpeRatio: 1.42, maxDrawdown: -15.6, winRate: 59.3, trades: 445 },
  { id: "b6", name: "Trend Following (EMA)", initialCapital: 100000, finalValue: 167890, totalReturn: 67.89, sharpeRatio: 2.05, maxDrawdown: -14.2, winRate: 64.7, trades: 312 },
  { id: "b7", name: "Options Straddle Strategy", initialCapital: 100000, finalValue: 128750, totalReturn: 28.75, sharpeRatio: 1.18, maxDrawdown: -25.1, winRate: 52.4, trades: 156 },
  { id: "b8", name: "Sector Rotation Model", initialCapital: 100000, finalValue: 149200, totalReturn: 49.20, sharpeRatio: 1.72, maxDrawdown: -16.8, winRate: 61.0, trades: 89 },
];

export const mockPaperPositions: PaperPosition[] = [
  { symbol: "NVDA", shares: 50, entryPrice: 482.30, currentPrice: 495.22, pnl: 646.00, pnlPct: 2.68, status: "Long" },
  { symbol: "AAPL", shares: 100, entryPrice: 172.15, currentPrice: 178.42, pnl: 627.00, pnlPct: 3.64, status: "Long" },
  { symbol: "MSFT", shares: 30, entryPrice: 385.00, currentPrice: 378.91, pnl: -182.70, pnlPct: -1.58, status: "Long" },
  { symbol: "GOOGL", shares: 75, entryPrice: 138.20, currentPrice: 141.80, pnl: 270.00, pnlPct: 2.60, status: "Long" },
  { symbol: "TSLA", shares: 40, entryPrice: 255.80, currentPrice: 248.50, pnl: -292.00, pnlPct: -2.85, status: "Short" },
  { symbol: "AMZN", shares: 60, entryPrice: 148.90, currentPrice: 153.42, pnl: 271.20, pnlPct: 3.03, status: "Long" },
];

export const mockTrades: Trade[] = [
  { id: "t1", symbol: "NVDA", type: "Buy", quantity: 50, price: 482.30, total: 24115.00, timestamp: "2026-03-12 10:15" },
  { id: "t2", symbol: "AAPL", type: "Buy", quantity: 100, price: 172.15, total: 17215.00, timestamp: "2026-03-11 14:22" },
  { id: "t3", symbol: "TSLA", type: "Sell", quantity: 40, price: 255.80, total: 10232.00, timestamp: "2026-03-10 09:45" },
  { id: "t4", symbol: "MSFT", type: "Buy", quantity: 30, price: 385.00, total: 11550.00, timestamp: "2026-03-09 11:30" },
  { id: "t5", symbol: "GOOGL", type: "Buy", quantity: 75, price: 138.20, total: 10365.00, timestamp: "2026-03-08 15:10" },
  { id: "t6", symbol: "META", type: "Sell", quantity: 25, price: 318.40, total: 7960.00, timestamp: "2026-03-07 13:55", pnl: 425.00 },
  { id: "t7", symbol: "AMZN", type: "Buy", quantity: 60, price: 148.90, total: 8934.00, timestamp: "2026-03-06 10:05" },
];

export const mockNews: NewsItem[] = [
  { id: "n1", title: "NVIDIA reports record data center revenue driven by AI demand", source: "Reuters", time: "1h ago", sentiment: "positive" },
  { id: "n2", title: "Federal Reserve signals potential rate cuts in Q2 2026", source: "CNBC", time: "2h ago", sentiment: "positive" },
  { id: "n3", title: "Apple announces next-gen M5 chip, shares rally in pre-market", source: "Bloomberg", time: "3h ago", sentiment: "positive" },
  { id: "n4", title: "Tesla faces regulatory scrutiny over autonomous driving claims", source: "WSJ", time: "4h ago", sentiment: "negative" },
  { id: "n5", title: "S&P 500 hits new all-time high on strong earnings season", source: "MarketWatch", time: "5h ago", sentiment: "positive" },
  { id: "n6", title: "JPMorgan warns of commercial real estate risks in Q2", source: "Financial Times", time: "6h ago", sentiment: "negative" },
  { id: "n7", title: "Microsoft Azure cloud revenue exceeds expectations", source: "TechCrunch", time: "7h ago", sentiment: "positive" },
  { id: "n8", title: "Crude oil prices stabilize amid OPEC+ production agreement", source: "Reuters", time: "8h ago", sentiment: "neutral" },
];

// Chart data generators
export const generatePriceHistory = (basePrice: number, days: number = 60) => {
  const data = [];
  let price = basePrice * 0.85;
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    price += (Math.random() - 0.45) * (basePrice * 0.02);
    price = Math.max(price, basePrice * 0.7);
    data.push({
      date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      price: Math.round(price * 100) / 100,
    });
  }
  return data;
};

export const cumulativeReturnsData = [
  { month: "Jan", momentum: 2.1, meanRev: 1.5, mlEnsemble: 3.2, trendFollow: 1.8 },
  { month: "Feb", momentum: 5.4, meanRev: 3.2, mlEnsemble: 7.8, trendFollow: 4.1 },
  { month: "Mar", momentum: 4.2, meanRev: 5.8, mlEnsemble: 12.1, trendFollow: 6.5 },
  { month: "Apr", momentum: 8.7, meanRev: 7.1, mlEnsemble: 18.4, trendFollow: 9.2 },
  { month: "May", momentum: 12.3, meanRev: 6.8, mlEnsemble: 24.6, trendFollow: 11.8 },
  { month: "Jun", momentum: 15.8, meanRev: 9.4, mlEnsemble: 31.2, trendFollow: 15.3 },
  { month: "Jul", momentum: 18.2, meanRev: 12.1, mlEnsemble: 38.5, trendFollow: 18.7 },
  { month: "Aug", momentum: 22.5, meanRev: 14.5, mlEnsemble: 45.1, trendFollow: 22.1 },
  { month: "Sep", momentum: 20.1, meanRev: 16.8, mlEnsemble: 42.3, trendFollow: 20.4 },
  { month: "Oct", momentum: 25.4, meanRev: 19.2, mlEnsemble: 52.8, trendFollow: 25.8 },
  { month: "Nov", momentum: 30.2, meanRev: 22.5, mlEnsemble: 61.4, trendFollow: 30.5 },
  { month: "Dec", momentum: 35.8, meanRev: 25.1, mlEnsemble: 72.1, trendFollow: 35.2 },
];

export const annualReturnsData = [
  { year: "2022", return: -8.2 },
  { year: "2023", return: 24.5 },
  { year: "2024", return: 42.1 },
  { year: "2025", return: 31.8 },
  { year: "2026 YTD", return: 12.3 },
];

export const monthlyPerformanceData = [
  { month: "Oct", return: 3.2 },
  { month: "Nov", return: -1.8 },
  { month: "Dec", return: 4.5 },
  { month: "Jan", return: 2.1 },
  { month: "Feb", return: -0.7 },
  { month: "Mar", return: 1.9 },
];

export const drawdownData = [
  { month: "Jan", drawdown: 0 },
  { month: "Feb", drawdown: -2.1 },
  { month: "Mar", drawdown: -5.4 },
  { month: "Apr", drawdown: -3.2 },
  { month: "May", drawdown: -1.1 },
  { month: "Jun", drawdown: 0 },
  { month: "Jul", drawdown: -4.8 },
  { month: "Aug", drawdown: -7.2 },
  { month: "Sep", drawdown: -9.8 },
  { month: "Oct", drawdown: -6.5 },
  { month: "Nov", drawdown: -3.1 },
  { month: "Dec", drawdown: -1.2 },
];

export const portfolioAllocation = [
  { name: "NVDA", value: 24.7, fill: "#3B82F6" },
  { name: "AAPL", value: 17.8, fill: "#10B981" },
  { name: "MSFT", value: 11.4, fill: "#8B5CF6" },
  { name: "GOOGL", value: 10.6, fill: "#F59E0B" },
  { name: "AMZN", value: 9.2, fill: "#EF4444" },
  { name: "Other", value: 26.3, fill: "#6B7280" },
];
