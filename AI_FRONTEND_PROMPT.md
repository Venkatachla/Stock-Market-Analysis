# 🚀 Stock Market Prediction Frontend - AI Generation Prompt

> Copy this entire prompt and paste into ChatGPT/Claude to generate a complete, production-ready React frontend

---

## SYSTEM PROMPT

You are an expert React + TypeScript fullstack developer specializing in financial dashboards. Generate a complete, production-ready stock market prediction frontend that integrates with a FastAPI backend. The code should be well-structured, typed, performant, and follow best practices.

---

## PROJECT REQUIREMENTS

### Tech Stack
- **Framework:** React 18+ with TypeScript
- **Build Tool:** Vite (already pre-configured in project)
- **Styling:** TailwindCSS (v3.x)
- **HTTP Client:** Axios
- **Charts:** TradingView Lightweight Charts
- **State:** React Context API
- **Date Handling:** date-fns

### Backend API (Already Running)
- **URL:** `http://localhost:8000`
- **Base endpoints available:**
  - `GET /stocks?limit=20` → Stock listings
  - `GET /predict?symbol=RELIANCE.NS` → ML predictions
  - `GET /chart/{symbol}?period=5d` → OHLCV data
  - `GET /portfolio/analytics` → Portfolio metrics
  - `GET /alerts/live?limit=5` → Trading alerts
  - `GET /risk-os/overview` → Risk management data
  - `GET /stocks/top-bulls` → Top performing stocks
  - `GET /scanner_results` → AI identified setups

### Project Structure (Pre-existing)
```
frontend/
├── src/
│   ├── pages/          (To be created)
│   ├── components/     (To be created)
│   ├── services/       (To be created)
│   ├── hooks/          (To be created)
│   ├── utils/          (To be created)
│   ├── App.tsx         (Main app)
│   └── main.tsx        (Entry point)
├── vite.config.ts      (Already configured)
├── tailwind.config.ts  (Already configured)
├── tsconfig.json       (Already configured)
└── package.json        (Already has dependencies)
```

---

## REQUIREMENTS - 5 PAGES

### 1. DASHBOARD PAGE
**File:** `src/pages/Dashboard.tsx`

**Features:**
- Portfolio summary card (Total value, PnL, Day change %)
- Performance metrics grid (1D/1W/1M returns, Sharpe ratio, Drawdown, Win rate)
- Live trading alerts table (Symbol | Signal | Confidence | Entry Price | Time)
- Top performers carousel/grid (Bulls, Bears, Losers)
- Market scanner results (Scrollable list)
- Auto-refresh every 30 seconds

**UI Elements:**
- Cards with shadow effects
- Color-coded badges (🟢 BUY, 🔴 SELL, 🔵 NEUTRAL)
- Confidence progress bars (0-100%)
- Pagination for scanner results
- Loading skeletons while fetching

**API Integration:**
```
GET /portfolio/analytics
GET /alerts/live?limit=5
GET /stocks/top-bulls
GET /stocks/top-bears
GET /stocks/top-losers
GET /scanner_results
```

---

### 2. STOCK DETAIL PAGE
**File:** `src/pages/StockDetail.tsx`

**Features:**
- URL params: `/stock/:symbol` (e.g., `/stock/RELIANCE.NS`)
- Stock header (Logo placeholder, Name, Price, 52W high/low, Dividend yield)
- Split layout:
  - **Left (60%):** Trading View chart with OHLC candles
    - Timeframes: 1D, 5D, 1M, 3M, 1Y, ALL
    - Technical indicators: SMA(20,50,200), EMA(12,26), Bollinger Bands, MACD, RSI, ATR
    - Volume bars below price
    - Indicator toggle checkboxes
  - **Right (40%):** Prediction panel
    - Large signal badge (BUY/SELL/NEUTRAL)
    - Confidence % with progress bar
    - Suggested entry, target, stop loss prices
    - Expected return % (green if positive, red if negative)
    - Model breakdown (XGBoost, LightGBM, RandomForest, LSTM each with signal + confidence)
    - Technical indicators summary
    - Action buttons: Add to Watchlist, Open Trade, View History

- Trading history table (collapsible)
  - Columns: Date | Entry | Exit | Return % | Status
  - Sortable, scrollable

**API Integration:**
```
GET /chart/{symbol}?period=5d&interval=1d
GET /candles?symbol={symbol}&limit=200
GET /predict?symbol={symbol}
```

---

### 3. STOCKS DISCOVERY PAGE
**File:** `src/pages/StockBrowser.tsx`

**Features:**
- Search bar with autocomplete (search by symbol/name)
- Filter tabs: All | Top Bulls | Top Bears | Top Losers | Watchlist | Scanner Results
- Sortable table with columns:
  - Symbol
  - Company Name
  - Current Price (₹)
  - Day Change (%)
  - ML Signal (BUY/SELL/NEUTRAL)
  - Confidence (%)
  - Volume (Millions)
  - Actions (View, Add to Watchlist, Set Alert)
- Pagination (20 per page)
- Row color coding (Green for BUY, Red for SELL, Blue for NEUTRAL)
- Click row to navigate to stock detail page
- Bulk actions: Compare stocks, Add all to watchlist

**API Integration:**
```
GET /stocks?limit=20&offset=0
GET /stocks/search?q={query}
GET /stocks/top-bulls
GET /stocks/top-bears
GET /stocks/top-losers
GET /scanner_results
```

---

### 4. RISK MANAGEMENT PAGE (Risk-OS)
**File:** `src/pages/RiskOS.tsx`

**Features:**
- Risk metrics cards:
  - Risk per trade (₹ amount)
  - Daily trading limit (₹ amount)
  - Max trades per day
  - Active setups (X / Max)
  - Current exposure % (with warning if > 80%)
  - Confidence threshold (> X%)

- Position sizing calculator:
  - Inputs: Account size, Risk %, Entry price, Stop loss
  - Output: Suggested position size in units and ₹

- Active positions monitor (table):
  - Symbol | Quantity | Entry | Current | PnL | Exposure % | Action (Close)

- Correlation heatmap:
  - Shows correlation matrix between held stocks
  - Color scale: Blue (low correlation, good) → Red (high correlation, redundant)

- Alert settings:
  - Max daily loss threshold (STOP TRADING trigger)
  - Daily profit target (CLOSE ALL POSITIONS trigger)
  - Notifications on risk breach, signal reversal

**API Integration:**
```
GET /risk-os/overview
```

---

### 5. PORTFOLIO ANALYSIS PAGE
**File:** `src/pages/Portfolio.tsx`

**Features:**
- Portfolio summary section:
  - Total value (₹)
  - Total invested (₹)
  - Cash available (₹)
  - Unrealized PnL (₹)
  - Day change %
  - YTD return %

- Holdings breakdown:
  - Pie chart showing sector allocation
  - Toggle to show/hide cash
  - Click sector to filter table

- Holdings table (sortable):
  - Symbol | Quantity | Avg Cost | Current | Total Value | Return % | Actions
  - Context menu: Sell, Add More, Set Alert, Analyze

- Performance chart:
  - Equity curve (line chart of portfolio value over time)
  - Timeframes: 1M, 3M, 6M, 1Y, All
  - Overlay benchmark line (e.g., NIFTY 50)
  - Drawdown visualization below

- Rebalancing recommendations:
  - Compare current vs target allocation
  - Suggest trades to rebalance
  - One-click apply

- Export options:
  - Download CSV
  - Generate PDF report

**API Integration:**
```
GET /portfolio/analytics
```

---

## COMPONENT ARCHITECTURE (Generate These)

### Layout Components (`src/components/Layout/`)
1. **Header.tsx**
   - Logo + Branding
   - Search bar (symbol search)
   - User menu (Settings, Logout, Theme toggle)
   - Responsive hamburger menu for mobile

2. **Sidebar.tsx**
   - Navigation links: Dashboard, Stocks, Analysis, Risk, Portfolio, Settings
   - Active link highlighting
   - Collapse/expand toggle
   - User initials avatar

3. **Footer.tsx**
   - Copyright, links, version

### Common Components (`src/components/Common/`)
1. **Card.tsx** - Reusable card wrapper with shadow, border, padding
2. **Button.tsx** - Primary, secondary, danger buttons with loading states
3. **Badge.tsx** - Signal badges (BUY=green, SELL=red, NEUTRAL=blue)
4. **ProgressBar.tsx** - Confidence/percentage visualization
5. **Spinner.tsx** - Loading indicator
6. **Alert.tsx** - Toast notification component (Success, Error, Info)
7. **Table.tsx** - Reusable sortable table component
8. **Modal.tsx** - Popup dialogs

### Dashboard Components (`src/components/Dashboard/`)
1. **PortfolioSummary.tsx** - Shows portfolio metrics
2. **PerformanceMetrics.tsx** - Grid of 1D/1W/1M returns, Sharpe, Drawdown, Win rate
3. **AlertsTable.tsx** - Live alerts with pagination
4. **TopPerformers.tsx** - Bulls, Bears, Losers carousel
5. **MarketScanner.tsx** - AI identified setups list

### Stock Detail Components (`src/components/StockDetail/`)
1. **ChartView.tsx** - TradingView chart with indicators
2. **PredictionPanel.tsx** - Signal, confidence, entry/target/SL prices
3. **ModelBreakdown.tsx** - Individual model predictions (accordion)
4. **TechnicalIndicators.tsx** - RSI, MACD, BB summary
5. **TradingHistory.tsx** - Past trades table (collapsible)
6. **TradeForm.tsx** - Execute trade dialog

### Stock Browser Components (`src/components/StockBrowser/`)
1. **StockTable.tsx** - Sortable stock listings
2. **FilterTabs.tsx** - Tab selection (All, Bulls, Bears, etc.)
3. **SearchBar.tsx** - Search with autocomplete
4. **Pagination.tsx** - Page navigation

### Risk Management Components (`src/components/RiskOS/`)
1. **RiskMetrics.tsx** - Risk overview cards
2. **PositionSizer.tsx** - Calculator widget
3. **CorrelationHeatmap.tsx** - Correlation matrix visualization
4. **ActivePositions.tsx** - Current positions monitor
5. **AlertSettings.tsx** - Risk threshold configuration

### Portfolio Components (`src/components/Portfolio/`)
1. **PortfolioSummary.tsx** - Value, PnL, duration overview
2. **HoldingsTable.tsx** - Individual holdings with actions
3. **SectorPieChart.tsx** - Sector allocation chart
4. **PerformanceChart.tsx** - Equity curve with benchmark
5. **RebalancingRecommendations.tsx** - Suggested trades
6. **ExportButtons.tsx** - CSV/PDF export controls

---

## SERVICES & UTILITIES (Generate These)

### `src/services/api.ts`
Create Axios instance with:
- Base URL: `http://localhost:8000`
- Error interceptors (4xx, 5xx handling)
- All API endpoints as typed functions:
  ```typescript
  getStocks(limit, offset)
  searchStocks(query)
  predictStock(symbol)
  getChartData(symbol, period)
  getPortfolioAnalytics()
  getAlerts(limit)
  getRiskOS()
  ```

### `src/hooks/useStocks.ts`
- Fetch stocks with auto-refresh (30s)
- Caching + error handling
- Return: { data, loading, error }

### `src/hooks/usePredictions.ts`
- Fetch ML predictions
- Return model breakdown

### `src/hooks/useChartData.ts`
- Fetch and cache OHLCV data
- Format for TradingView chart

### `src/utils/formatters.ts`
- Format currency (₹ with commas)
- Format percentage (±X.XX%)
- Format large numbers (M, K suffixes)
- Format dates (DD/MM/YYYY, relative time)

### `src/utils/constants.ts`
- Colors (BUY=green, SELL=red, NEUTRAL=blue)
- API endpoints
- Chart timeframes
- Technical indicators list

---

## STYLING REQUIREMENTS

### Colors (TailwindCSS)
- **Primary:** Blue (#3B82F6)
- **Success/BUY:** Green (#10B981)
- **Danger/SELL:** Red (#EF4444)
- **Neutral:** Gray (#6B7280)
- **Background:** Light gray (#F3F4F6)
- **Text:** Dark gray (#1F2937)

### Typography
- **Headings (H1-H4):** Inter Bold
- **Body:** Inter Regular
- **Small:** Inter Light

### Spacing
- Use TailwindCSS spacing: 4px (1 unit), 8px (2 units), etc.
- Card padding: 20px (5 units)
- Section margins: 32px (8 units)

### Responsive Design
- **Desktop:** 1920px+
- **Tablet:** 768px+
- **Mobile:** 320px+

---

## FUNCTIONALITY REQUIREMENTS

### Real-Time Updates
- Dashboard: Auto-refresh every 30 seconds
- Charts: Manual refresh + 1-minute auto-refresh
- Prices: Update from API polling (not WebSocket)

### Data Handling
- Handle API errors gracefully (show error messages)
- Loading states (skeletons, spinners)
- Empty states (no results, no alerts)
- Network timeout (5s) with retry logic

### User Experience
- Keyboard navigation (Tab, Enter, Escape)
- Tooltips on hover (indicators, confidence)
- Toast notifications (Success, Error, Info)
- Dark mode support (toggle in header)
- Mobile-responsive (hamburger menu, stacked layout)

### Performance
- Lazy load pages (code splitting)
- Memoize expensive components (React.memo)
- Virtual scrolling for large tables (1000+ rows)
- Image optimization (next/image or lazy loading)
- CSS optimization (TailwindCSS purging)

---

## ROUTING

Create React Router setup in `App.tsx`:
```
/                    → Dashboard
/stocks              → Stock Browser
/stock/:symbol       → Stock Detail
/risk-os             → Risk Management
/portfolio           → Portfolio Analysis
/watchlist           → Watchlist (optional)
/settings            → Settings (optional)
404                  → Not Found page
```

---

## STATE MANAGEMENT

Use React Context API with hooks:
```typescript
// AppContext
useApp() → {
  user, portfolio, alerts, watchlist, theme, settings
  setTheme(), addToWatchlist(), removeAlert()
}
```

---

## DELIVERABLES

Generate and provide:

1. ✅ **Complete folder structure** (`components/`, `pages/`, `services/`, `hooks/`, `utils/`)
2. ✅ **All 5 pages** (Dashboard, StockDetail, StockBrowser, RiskOS, Portfolio)
3. ✅ **20+ reusable components** (cards, buttons, tables, charts, modals)
4. ✅ **API service** with all endpoints typed
5. ✅ **Custom hooks** for data fetching (useStocks, usePredictions, useChartData)
6. ✅ **Context setup** for global state
7. ✅ **Utility functions** (formatters, validators, constants)
8. ✅ **Main App.tsx** with routing
9. ✅ **TailwindCSS styling** (dark mode support)
10. ✅ **TypeScript types** and interfaces

---

## CODE QUALITY STANDARDS

- ✅ **TypeScript:** Strict mode enabled, all components typed
- ✅ **Naming:** PascalCase for components, camelCase for variables/functions
- ✅ **Comments:** JSDoc for complex functions, inline for tricky logic
- ✅ **Error Handling:** Try-catch, error boundaries, validation
- ✅ **Performance:** Memoization, lazy loading, code splitting
- ✅ **Accessibility:** Semantic HTML, ARIA labels, keyboard navigation
- ✅ **Styling:** Consistent spacing, colors, responsive design

---

## INSTALLATION INSTRUCTIONS

After code generation:

1. **Copy generated files** to `frontend/src/` (existing project)
2. **Install dependencies:**
   ```bash
   cd frontend
   npm install --legacy-peer-deps
   ```
3. **Update tsconfig.json** if needed (strict mode)
4. **Start development server:**
   ```bash
   npm run dev
   ```
5. **Open browser:**
   ```
   http://localhost:5173
   ```

---

## NOTES

- **API Endpoint:** Backend already running on `http://localhost:8000`
- **No Authentication:** Skip login/auth for MVP (demo mode)
- **Test Data:** Use real NSE stock data from backend
- **Chart Library:** Use TradingView Lightweight Charts (lightweight, free)
- **State:** Don't over-engineer; use Context API (sufficient for this scope)

---

## FINAL OUTPUT FORMAT

Provide code in this order:
1. `App.tsx` (routing setup)
2. `components/` (all components, organized by folder)
3. `pages/` (all 5 pages)
4. `services/` (api.ts)
5. `hooks/` (custom hooks)
6. `utils/` (formatters, constants)
7. `contexts/` (AppContext)
8. Installation + running instructions

**Start generation now!**

---

