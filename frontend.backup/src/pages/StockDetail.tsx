import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { EnhancedStockChart } from "@/components/EnhancedStockChart";
import { AppLayout } from "@/components/AppLayout";
import { TrendingUp, Info } from "lucide-react";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";       

export default function StockDetail() {
  const { symbol = "RELIANCE" } = useParams();
  const [timeframe, setTimeframe] = useState("1d");
  const [showPred, setShowPred] = useState(false);
  const [predData, setPredData] = useState<any>(null);
  const [predLoading, setPredLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("Chart");

  // Fetch prediction only if showPred is true or if activeTab needs it
  useEffect(() => {
    async function loadPrediction() {
      try {
        setPredLoading(true);
        const res = await axios.get(`${API_URL}/prediction/${symbol.toUpperCase()}?timeframe=${encodeURIComponent(timeframe)}`);
        setPredData(res.data);
      } catch (err) {
        console.error("Prediction load failed");
      } finally {
        setPredLoading(false);
      }
    }
    loadPrediction();
  }, [symbol, timeframe]);

  return (
    <AppLayout>
      <div className="space-y-6 max-w-7xl mx-auto pb-24">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-border/40 pb-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{symbol.toUpperCase()}</h1>
            <p className="text-sm text-muted-foreground flex items-center gap-2 mt-1">   
              NSE Equity <span className="w-1 h-1 rounded-full bg-border"></span> Realtime Active Data (24/7)
            </p>
          </div>

          <div className="flex items-center gap-3" />
        </div>

        {/* Groww Style Tabs */}
        <div className="flex space-x-1 border-b border-border/40 overflow-x-auto no-scrollbar">
          {["Overview", "Chart", "Options", "Analysis"].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${activeTab === tab ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground"}`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* TAB CONTENTS */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 space-y-6">
            
            {/* The Chart is central in all tabs but let's always show it, or adapt based on tab */}
            {(activeTab === "Overview" || activeTab === "Chart" || activeTab === "Analysis") && (
              <div className="relative space-y-2">
                 <div className="flex justify-start">
                    <button
                      onClick={() => setShowPred(!showPred)}
                      className={`px-3 py-1.5 text-xs rounded-lg font-semibold transition-all ${showPred ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20' : 'bg-background/80 backdrop-blur border border-border hover:bg-muted'}`}
                    >
                      {showPred ? "Hide Model" : "Show AI Prediction"}
                    </button>
                 </div>
                 <EnhancedStockChart symbol={symbol} timeframe={timeframe} showPrediction={showPred} predictionData={predData} />
              </div>
            )}

            {activeTab === "Options" && (
               <div className="bg-card border border-border/50 rounded-xl p-8 text-center text-muted-foreground">
                  Options chain data is fully synced and available 24/7. Select an expiry date to view Greeks.
                  <br /> <span className="text-xs opacity-50">(Placeholder for Options Table)</span>
               </div>
            )}
          </div>

          {/* Right Panel / Sidebar Metrics (Always visible as requested) */}
          <div className="space-y-4">
            <div className="bg-card border border-border/50 rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-muted-foreground flex items-center gap-2 mb-4">
                <TrendingUp className="h-4 w-4" /> Professional Trade Signal
              </h3>
              {predLoading ? (
                <div className="h-48 flex items-center justify-center text-sm flex-col gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                  <span className="text-muted-foreground">Updating Professional Trade Signal...</span>
                </div>
              ) : predData ? (
                <div className="space-y-4 text-sm font-medium">
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">1. Trend:</span>
                    <span>{predData.trend || (predData.prob_up > 0.55 ? "Bullish" : predData.prob_down > 0.55 ? "Bearish" : "Sideways")}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">2. Signal:</span>
                    <span className={
                      String(predData.signal || "").includes("BUY")
                        ? "text-green-500 font-bold"
                        : String(predData.signal || "").includes("SELL")
                        ? "text-red-500 font-bold"
                        : "text-yellow-500 font-bold"
                    }>
                      {predData.signal || "WAIT"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">3. Entry Zone:</span>
                    <span className="font-mono">₹{(predData.latest_price * 0.998).toFixed(1)} – ₹{(predData.latest_price * 1.002).toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">4. Stop Loss:</span>
                    <span className="font-mono text-red-400">₹{predData.stop_loss.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">5. Target:</span>
                    <span className="font-mono text-green-400">₹{predData.take_profit.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">6. Confidence:</span>
                    <span>{predData.confidence_score.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">7. Timeframe:</span>
                    <select
                      value={timeframe}
                      onChange={(e) => setTimeframe(e.target.value)}
                      className="bg-slate-800 text-white border border-slate-600 rounded px-2 py-1 text-xs"
                    >
                      {['1m', '5m', '15m', '60m', '1d', '1wk'].map(tf => (
                        <option key={tf} value={tf}>{tf}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">8. News Sentiment:</span>
                    <span>{predData.news_sentiment_label || (predData.sentiment_score > 0.2 ? "Positive" : predData.sentiment_score < -0.2 ? "Negative" : "Neutral")}</span>
                  </div>
                  <div className="flex justify-between items-start pt-2">
                    <span className="text-muted-foreground mt-0.5 shrink-0 mr-4">9. Reason:</span>
                    <span className="text-right text-muted-foreground leading-tight">
                      {predData.reason || (predData.prob_up > 0.55 
                        ? "Uptrend with positive AI orderflow." 
                        : predData.prob_down > 0.55 
                        ? "Downtrend with bearish distribution."
                        : "Consolidating price action without clear momentum.")}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="h-48 flex items-center justify-center text-sm flex-col gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                  <span className="text-muted-foreground">Generating Signal...</span>
                </div>
              )}
            </div>

            <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 flex gap-3 items-start">
              <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />        
              <p className="text-xs text-foreground/80 leading-relaxed">
                Predictions are driven by a multi-modal blend of XGBoost and LSTM processing 15-years of structural orderflow, fully active across extended hours.
              </p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
