import { BrowserRouter, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import StockDetail from "./pages/StockDetail";
import Intraday from "./pages/Intraday";
import Settings from "./pages/Settings";
import Watchlist from "./pages/Watchlist";
import Index from "./pages/Index.tsx";
import StockPrediction from "./pages/StockPrediction.tsx";
import Backtest from "./pages/Backtest.tsx";
import PaperTrading from "./pages/PaperTrading.tsx";
import Signals from "./pages/Signals.tsx";
import News from "./pages/News.tsx";
import Login from "./pages/Login.tsx";
import Admin from "./pages/Admin.tsx";
import Performance from "./pages/Performance.tsx";
import RiskOS from "./pages/RiskOS.tsx";
import OptionsLab from "./pages/OptionsLab.tsx";
import AIScanner from "./pages/AIScanner.tsx";
import NotFound from "./pages/NotFound.tsx";

const App = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/scanner" element={<AIScanner />} />
      <Route path="/stock/:symbol" element={<StockDetail />} />
      <Route path="/intraday" element={<Intraday />} />
      <Route path="/watchlist" element={<Watchlist />} />
      <Route path="/options" element={<OptionsLab />} />
      <Route path="/options-lab" element={<OptionsLab />} />
      <Route path="/settings" element={<Settings />} />
      
      {/* Legacy Advanced Routes preserved mapped away from root */}
      <Route path="/trade-now" element={<Index />} />
      <Route path="/stock-prediction" element={<StockPrediction />} />
      <Route path="/backtest" element={<Backtest />} />
      <Route path="/paper-trading" element={<PaperTrading />} />
      <Route path="/signals" element={<Signals />} />
      <Route path="/news" element={<News />} />
      <Route path="/login" element={<Login />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/performance" element={<Performance />} />
      <Route path="/risk-os" element={<RiskOS />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  </BrowserRouter>
);

export default App;
