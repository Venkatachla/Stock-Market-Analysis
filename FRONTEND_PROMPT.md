# Stock Market Prediction Frontend - Comprehensive Specification

## 1. PROJECT OVERVIEW
Build a **professional-grade stock market prediction dashboard** for NSE (National Stock Exchange) equities using React + TypeScript + Vite with real-time ML predictions and technical analysis.

**Target Users:** Active traders, portfolio managers, retail investors
**Key Value:** ML-powered buy/sell signals, portfolio analytics, risk management, real-time market scanner

---

## 2. TECHNICAL STACK

### Frontend:
- **Framework:** React 18+ with TypeScript
- **Builder:** Vite (fast HMR, optimized builds)
- **UI Library:** TailwindCSS for styling
- **State Management:** React Context API or Zustand
- **Charts:** TradingView Lightweight Charts or Chart.js
- **HTTP Client:** Axios or Fetch API
- **Date handling:** date-fns

### Backend API (Already Provided):
- **URL:** `http://localhost:8000`
- **Authentication:** None (demo mode)
- **Response Format:** JSON

---

## 3. CORE UI PAGES & LAYOUTS

### Page 1: DASHBOARD (Home)
**Purpose:** High-level portfolio overview and market scanner

**Layout:**
```
┌─ Header with Logo, Search Bar, User Menu ──────────────────┐
├─ Sidebar: Navigation (Dashboard, Stocks, Analysis, Risk)    │
├─ Main Content:                                              │
│  ├─ Portfolio Summary Card                                  │
│  │  ├─ Total Portfolio Value (₹)                           │
│  │  ├─ Day's PnL & Percentage                              │
│  │  ├─ Holdings Count                                       │
│  │  └─ Diversification Score (%)                           │
│  │                                                          │
│  ├─ Performance Metrics (Grid)                             │
│  │  ├─ Returns (1D / 1W / 1M / YTD)                       │
│  │  ├─ Sharpe Ratio                                        │
│  │  ├─ Max Drawdown                                        │
│  │  └─ Win Rate %                                          │
│  │                                                          │
│  ├─ Live Trading Alerts (Table)                           │
│  │  ├─ Symbol | Signal | Confidence | Entry Price | Time  │
│  │  └─ Action buttons: View Details, Add to Watchlist    │
│  │                                                          │
│  ├─ Top Performers (Carousel/Grid)                        │
│  │  ├─ Top 5 Bulls (Green: ↑10%+)                        │
│  │  ├─ Top 5 Bears (Red: ↓10%-)                          │
│  │  └─ Top 5 Losers (By confidence reversal)              │
│  │                                                          │
│  └─ Market Scanner Results (List)                         │
│     ├─ Screened Stocks by ML Criteria                     │
│     ├─ Pagination (20 per page)                           │
│     └─ Click to view stock detail                         │
└────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Real-time portfolio metrics update every 30 seconds
- Color-coded signals: Green (BUY), Red (SELL), Blue (NEUTRAL)
- Confidence bars (0-100%)
- Quick add to watchlist functionality

---

### Page 2: STOCK DETAIL / ANALYSIS
**Purpose:** Deep dive into individual stock prediction and technical analysis

**Layout:**
```
┌─ Back Button | Symbol (e.g., RELIANCE.NS) | Refresh ───────┐
├─ Stock Header                                               │
│  ├─ Company Logo + Name                                     │
│  ├─ Current Price (₹) | Change % | Market Cap              │
│  ├─ 52W High/Low | Div Yield                               │
│  └─ Sentiment Gauge (Bull/Neutral/Bear)                    │
│                                                             │
├─ Main Section (Split Layout):                              │
│  ├─ LEFT: Chart View (60%)                                 │
│  │  ├─ Trading View Chart or Chart.js                      │
│  │  │  ├─ Display: Candles (OHLC)                         │
│  │  │  ├─ Timeframes: 1D, 5D, 1M, 3M, 1Y, ALL            │
│  │  │  ├─ Technical Overlays:                             │
│  │  │  │  ├─ SMA (20, 50, 200)                           │
│  │  │  │  ├─ EMA (12, 26)                                │
│  │  │  │  ├─ Bollinger Bands                             │
│  │  │  │  ├─ MACD                                        │
│  │  │  │  ├─ RSI                                         │
│  │  │  │  └─ ATR                                         │
│  │  │  └─ Volume bars below price chart                  │
│  │  │                                                    │
│  │  └─ Chart Controls:                                   │
│  │     ├─ Zoom In/Out                                    │
│  │     ├─ Indicator Toggle                              │
│  │     └─ Timeframe Selector                            │
│  │                                                      │
│  └─ RIGHT: Prediction Panel (40%)                       │
│     ├─ ML Prediction Card                               │
│     │  ├─ Signal: BUY / SELL / NEUTRAL (Large Badge)  │
│     │  ├─ Confidence: 95% (Progress Bar)               │
│     │  ├─ Suggested Entry Price (₹)                    │
│     │  ├─ Target Price (₹)                             │
│     │  ├─ Stop Loss (₹)                                │
│     │  └─ Expected Return: +5.2% (Green/Red)          │
│     │                                                  │
│     ├─ Model Breakdown (Accordion)                     │
│     │  ├─ XGBoost: BUY @ 78% confidence               │
│     │  ├─ LightGBM: BUY @ 92% confidence              │
│     │  ├─ Random Forest: NEUTRAL @ 65% conf           │
│     │  └─ LSTM: SELL @ 48% conf                       │
│     │                                                  │
│     ├─ Technical Indicators Summary                    │
│     │  ├─ RSI: 65 (Neutral zone)                      │
│     │  ├─ MACD: Bullish Crossover                     │
│     │  ├─ BB: Price near Upper Band                   │
│     │  └─ Trend: Strong Uptrend                       │
│     │                                                  │
│     └─ Action Buttons                                  │
│        ├─ 📊 Add to Watchlist                         │
│        ├─ 💼 Open Trade                               │
│        └─ 📋 View History                             │
│                                                       │
├─ Bottom Section: Trading History (Collapsible)        │
│  ├─ Date | Entry Price | Exit Price | Return % | Status  │
│  └─ Sort by Date, Return, Status                     │
│                                                       │
└───────────────────────────────────────────────────────┘
```

**Features:**
- Real-time price updates (WebSocket optional)
- Smooth chart transitions between timeframes
- Indicator tooltips on hover
- One-click trade execution (demo mode)
- Responsive to mobile (chart on top, panel below)

---

### Page 3: STOCKS DISCOVERY
**Purpose:** Browse, search, filter all available NSE stocks

**Layout:**
```
┌─ Search Bar (Search by Symbol/Name) ──┐
├─ Filter Tabs:                          │
│  ├─ All Stocks                         │
│  ├─ 📈 Top Bulls (Bullish Signals)    │
│  ├─ 📉 Top Bears (Bearish Signals)    │
│  ├─ 🔴 Top Losers (High Loss % Today) │
│  ├─ ⭐ Watchlist                      │
│  └─ 🤖 Scanner Results                │
│                                        │
├─ Columns (Sortable):                  │
│  ├─ Symbol                             │
│  ├─ Company Name                       │
│  ├─ Current Price (₹)                 │
│  ├─ Day Change (%)                    │
│  ├─ ML Signal (BUY/SELL/NEUTRAL)     │
│  ├─ Confidence (%)                    │
│  ├─ Volume (Millions)                 │
│  └─ Actions (View, Watchlist, Alert)  │
│                                        │
├─ Pagination: 20 stocks per page        │
│  ├─ Previous | Page 1 of 7 | Next      │
│  └─ Jump to page                       │
│                                        │
└─ Bulk Actions (Select Multiple)        │
   ├─ Compare                            │
   └─ Add All to Watchlist              │
```

**Features:**
- Real-time sorting (Price, Change%, Signal, Confidence)
- Color-coded rows (Green for BUY, Red for SELL)
- Quick preview on hover
- Keyboard shortcuts for navigation

---

### Page 4: RISK MANAGEMENT (Risk-OS)
**Purpose:** Portfolio risk control, position sizing, exposure management

**Layout:**
```
┌─ Risk Overview Dashboard ────────────────────────────────┐
│                                                          │
├─ Risk Metrics (Cards):                                  │
│  ├─ Risk per Trade: ₹500 (2% of portfolio)             │
│  ├─ Daily Trading Limit: ₹10,000 (4% of portfolio)    │
│  ├─ Max Trades per Day: 5                              │
│  ├─ Active Setups: 3 / 5                               │
│  ├─ Current Exposure: 65% / 80%                        │
│  └─ Confidence Threshold: > 70%                        │
│                                                         │
├─ Position Sizing Calculator:                           │
│  ├─ Account Size: ₹250,000                            │
│  ├─ Risk %: 2% (Slider)                               │
│  ├─ Entry Price: ₹1,500                               │
│  ├─ Stop Loss: ₹1,450                                 │
│  └─ Suggested Position Size: 333 shares (₹500K risk) │
│                                                        │
├─ Active Positions Monitor:                            │
│  ├─ Symbol | Entry | Current | PnL | Exposure% | ...  │
│  └─ Close Position button                             │
│                                                        │
├─ Correlation Heatmap (Multiple Holdings):             │
│  ├─ Shows correlation between held stocks             │
│  ├─ Red: High correlation (Reduce redundancy)         │
│  └─ Blue: Low correlation (Good diversification)      │
│                                                        │
└─ Alert Settings:                                       │
   ├─ Max Daily Loss: -₹5,000 (FULL STOP)               │
   ├─ Daily Profit Target: +₹10,000 (CLOSE ALL)         │
   └─ Notify on: Risk Threshold Breach, Signal Reversal │
```

**Features:**
- Real-time risk calculation
- Position sizing assistant
- Risk-reward ratio calculator
- Correlation analysis
- Risk alert triggers

---

### Page 5: PORTFOLIO ANALYSIS
**Purpose:** Detailed portfolio composition, performance tracking, rebalancing

**Layout:**
```
┌─ Portfolio Summary ──────────────────────────────────┐
│ Total Value: ₹250,000 | Invested: ₹180,000      │
│ Cash: ₹70,000 | PnL: ₹1,250 (+0.5% YTD)         │
└──────────────────────────────────────────────────────┘

├─ Holdings Breakdown (Pie Chart):
│  ├─ Sector allocation (Tech, Finance, Energy, etc.)
│  ├─ Click to filter by sector
│  └─ Show/Hide cash position

├─ Individual Holdings Table:
│  ├─ Symbol | Qty | Avg Cost | Current | Total Val | Return% | Actions
│  ├─ Sortable by any column
│  └─ Context menu: Sell, Add More, Set Alert, Analyze

├─ Performance Chart:
│  ├─ Equity Curve (Portfolio Value over time)
│  ├─ Timeframes: 1M, 3M, 6M, 1Y, All
│  ├─ Overlay benchmark (NIFTY 50)
│  └─ Drawdown visualization

├─ Rebalancing Recommendations:
│  ├─ Current allocation vs target allocation
│  ├─ Suggested trades to rebalance
│  └─ One-click apply button

└─ Export Options:
   ├─ Download CSV
   └─ Generate PDF report
```

---

## 4. CORE API ENDPOINTS & INTEGRATION

### Stock Data Endpoints:
```
GET /stocks?limit=20&offset=0
→ Returns: [{symbol, name, price, change%, volume, ema_signal}]

GET /stocks/search?q=RELIANCE
→ Returns: [{symbol, name, price, change%}]

GET /stocks/top-bulls?limit=5
→ Returns: Top bullish stocks

GET /stocks/top-bears?limit=5
→ Returns: Top bearish stocks

GET /stocks/top-losers?limit=5
→ Returns: Biggest losers
```

### Prediction Endpoints:
```
GET /predict?symbol=RELIANCE.NS
→ Returns: {
     symbol, 
     signal: "BUY" | "SELL" | "NEUTRAL",
     confidence: 0-100,
     entry_price, target_price, stop_loss,
     models: {
       xgboost: {signal, confidence},
       lightgbm: {signal, confidence},
       random_forest: {signal, confidence},
       lstm: {signal, confidence}
     }
   }

POST /predict
Body: {symbols: ["RELIANCE.NS", "INFY.NS"]}
→ Returns: [{symbol, signal, confidence, ...}]
```

### Chart Data Endpoints:
```
GET /chart/{symbol}?period=5d&interval=1d
→ Returns: [{datetime, open, high, low, close, volume}]

GET /candles?symbol=RELIANCE.NS&limit=200
→ Returns: Historical candlestick data
```

### Portfolio & Alerts:
```
GET /portfolio/analytics
→ Returns: {
     portfolio_value, total_invested, cash,
     unrealized_pnl, day_change_pct,
     diversification_score, holdings_count
   }

GET /alerts/live?limit=5
→ Returns: [{symbol, signal, confidence, entry_price, time, status}]

GET /scanner_results
→ Returns: [{symbol, name, signal, confidence, setup_type}]
```

### Risk Management:
```
GET /risk-os/overview
→ Returns: {
     risk_per_trade, daily_limit, max_trades_per_day,
     active_setups, current_exposure, confidence_threshold
   }
```

---

## 5. COMPONENT ARCHITECTURE

### High-Level Structure:
```
src/
├── components/
│   ├── Layout/
│   │   ├─ Header.tsx (Logo, Search, User Menu)
│   │   ├─ Sidebar.tsx (Navigation)
│   │   └─ Footer.tsx
│   │
│   ├── Common/
│   │   ├─ Card.tsx (Reusable card component)
│   │   ├─ Button.tsx
│   │   ├─ Badge.tsx (Signal badges: BUY/SELL/NEUTRAL)
│   │   ├─ ProgressBar.tsx (Confidence indicator)
│   │   ├─ Spinner.tsx (Loading state)
│   │   └─ Alert.tsx (Toast notifications)
│   │
│   ├── Dashboard/
│   │   ├─ PortfolioSummary.tsx
│   │   ├─ PerformanceMetrics.tsx
│   │   ├─ AlertsTable.tsx
│   │   ├─ TopPerformers.tsx
│   │   └─ MarketScanner.tsx
│   │
│   ├── StockDetail/
│   │   ├─ ChartView.tsx (Main price chart)
│   │   ├─ PredictionPanel.tsx
│   │   ├─ ModelBreakdown.tsx
│   │   ├─ TechnicalIndicators.tsx
│   │   ├─ TradingHistory.tsx
│   │   └─ TradeForm.tsx (Execute trade)
│   │
│   ├── StockBrowser/
│   │   ├─ StockTable.tsx
│   │   ├─ FilterTabs.tsx
│   │   ├─ SearchBar.tsx
│   │   └─ Pagination.tsx
│   │
│   ├── RiskOS/
│   │   ├─ RiskMetrics.tsx
│   │   ├─ PositionSizer.tsx
│   │   ├─ CorrelationHeatmap.tsx
│   │   ├─ ActivePositions.tsx
│   │   └─ AlertSettings.tsx
│   │
│   └── Portfolio/
│       ├─ PortfolioSummary.tsx
│       ├─ HoldingsTable.tsx
│       ├─ PerformanceChart.tsx
│       ├─ RebalancingRecommendations.tsx
│       └─ ExportButtons.tsx
│
├── pages/
│   ├─ Dashboard.tsx
│   ├─ StockDetail.tsx
│   ├─ StockBrowser.tsx
│   ├─ RiskOS.tsx
│   ├─ Portfolio.tsx
│   └─ Settings.tsx
│
├── services/
│   ├─ api.ts (Axios instance + all endpoints)
│   ├─ chartService.ts (Chart data processing)
│   └─ calculators.ts (Risk, position sizing calculations)
│
├── hooks/
│   ├─ useStocks.ts (Fetch stocks, auto-refresh)
│   ├─ usePredictions.ts (Fetch predictions)
│   ├─ usePortfolio.ts (Portfolio data)
│   └─ useChartData.ts (Chart data with caching)
│
├── contexts/
│   ├─ PortfolioContext.tsx
│   └─ AlertContext.tsx
│
├── utils/
│   ├─ formatters.ts (₹, %, decimals)
│   ├─ validators.ts
│   └─ constants.ts (Colors, themes, API URLs)
│
└── App.tsx (Routes, theme provider)
```

---

## 6. KEY FEATURES & REQUIREMENTS

### Real-Time Updates:
- ✅ Portfolio values update every 30s
- ✅ Price updates via API polling (not WebSocket for MVP)
- ✅ Alerts appear instantly when new signals generated
- ✅ Charts refresh on demand (manual + auto 1min)

### Data Visualization:
- ✅ Price charts with technical indicators (TradingView recommended)
- ✅ Correlation heatmaps (seaborn-style)
- ✅ Equity curves (line charts)
- ✅ Pie charts (sector allocation)
- ✅ Bar charts (performance by symbol)

### User Experience:
- ✅ Responsive design (Desktop: 1920px+, Tablet: 768px+, Mobile: 320px+)
- ✅ Dark mode + Light mode toggle
- ✅ Keyboard shortcuts (e.g., `/` to search, `N` for new trade)
- ✅ Loading skeletons (not blank screens)
- ✅ Toast notifications (Success, Error, Info messages)
- ✅ Error boundaries + fallback UI

### Performance:
- ✅ Lazy load pages (code splitting)
- ✅ Memoize expensive components (React.memo)
- ✅ Virtual scrolling for large tables (1000+ rows)
- ✅ Cache API responses (5min TTL for stock lists, 1min for predictions)
- ✅ Bundle size < 500KB (gzipped)

---

## 7. STATE MANAGEMENT FLOW

### Global State (Context or Zustand):
```
AppStore {
  user: { id, name, portfolio_value, cash }
  portfolio: { holdings, totalValue, PnL }
  alerts: [{ id, symbol, signal, time, read }]
  watchlist: [symbol...]
  theme: "light" | "dark"
  settings: { currency, language, notifications }
}
```

### Component State:
- Chart timeframe, indicators toggled
- Table sorting, filtering
- Form inputs
- Loading, error states

---

## 8. STYLING & THEME

### Color Scheme:
- **Primary:** #1F2937 (Dark Gray)
- **Accent:** #3B82F6 (Blue)
- **Success:** #10B981 (Green) - for BUY signals
- **Danger:** #EF4444 (Red) - for SELL signals
- **Neutral:** #6B7280 (Gray) - for NEUTRAL signals
- **Background:** #F3F4F6 (Light Gray)

### Typography:
- **Headings:** Inter Bold (24px, 20px, 18px)
- **Body:** Inter Regular (16px)
- **Small:** Inter Regular (14px, 12px)

### Spacing:
- Use TailwindCSS: 4px, 8px, 12px, 16px, 24px, 32px units

---

## 9. DEPLOYMENT

### Development:
```bash
npm install
npm run dev
# Runs on http://localhost:5173
```

### Production Build:
```bash
npm run build
# Output: dist/
```

### Hosting Options:
- Vercel (recommended for React)
- Netlify
- AWS S3 + CloudFront
- Docker container

---

## 10. TESTING REQUIREMENTS

### Unit Tests:
- Component rendering
- API service mocking
- Utility functions (formatters, calculators)

### E2E Tests:
- User login flow
- Stock search and view
- Trade execution
- Alert generation

### Performance Tests:
- Lighthouse score > 80
- Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1

---

## 11. ACCESSIBILITY (A11Y)

- ✅ WCAG 2.1 AA compliance
- ✅ Semantic HTML (buttons, labels, headings)
- ✅ ARIA labels for icons
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Color contrast ratio > 4.5:1
- ✅ Focus indicators visible

---

## 12. DELIVERABLES

### Phase 1 (MVP - 1 week):
- ✅ Dashboard with portfolio summary
- ✅ Stock browser with search
- ✅ Prediction integration (show signal + confidence)
- ✅ Basic styling with TailwindCSS

### Phase 2 (2 weeks):
- ✅ Stock detail page with chart
- ✅ Technical indicators overlay
- ✅ Model breakdown display
- ✅ Risk management module

### Phase 3 (1 week):
- ✅ Portfolio analysis page
- ✅ Mobile responsiveness
- ✅ Dark mode
- ✅ Real-time updates

---

## 13. DEVELOPMENT CHECKLIST

- [ ] Setup React + Vite + TypeScript project
- [ ] Install TailwindCSS, Axios, date-fns
- [ ] Create folder structure (components, pages, services, hooks, contexts)
- [ ] Build Layout (Header, Sidebar, Footer)
- [ ] Build Dashboard page (cards, alerts, scanner)
- [ ] Build Stock Browser (table, search, filters)
- [ ] Build Stock Detail (chart, predictions, indicators)
- [ ] Integrate all API endpoints
- [ ] Add real-time polling (30s refresh)
- [ ] Implement error handling + retries
- [ ] Add loading states + skeletons
- [ ] Style with TailwindCSS (light + dark mode)
- [ ] Add responsive design (mobile, tablet, desktop)
- [ ] Setup Redux or Context for state
- [ ] Add toast notifications
- [ ] Test all pages + API flows
- [ ] Optimize performance (lazy load, memoize, cache)
- [ ] Deploy to Vercel/Netlify

---

## 14. NEXT STEPS

1. **Use this prompt** with Claude or ChatGPT to generate complete React boilerplate
2. **Copy generated code** into your `frontend/src/` directory
3. **Install dependencies:** `npm install`
4. **Run backend API:** `python -m uvicorn api.server:app --reload`
5. **Start frontend:** `npm run dev`
6. **Test:** Open http://localhost:5173 and verify all pages work

---

## 15. CUSTOMIZATION NOTES

If you prefer:
- **Different chart library:** Replace TradingView with Chart.js, Recharts, or ApexCharts
- **Different styling:** Swap TailwindCSS for Material-UI, Chakra UI, or styled-components
- **State management:** Use Redux, Jotai, or Recoil instead of Context API
- **Mobile app:** Use React Native for iOS/Android version

---

**This prompt is ready to be used with any AI code generator or as a detailed specification for manual development.**

