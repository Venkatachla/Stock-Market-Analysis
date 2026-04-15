import { Bell, Activity, TrendingUp, TrendingDown } from "lucide-react";
import { SearchBar } from "./SearchBar";
import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

export function Header() {
  const [tickerData, setTickerData] = useState<{symbol: string, price: number, change: number}[]>([]);

  useEffect(() => {
    let active = true;
    const fetchPrices = async () => {
      try {
        // Fetch a couple of top stocks to simulate a ticker
        const symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"];
        const promises = symbols.map(sym => axios.get(`${API_URL}/chart/${sym}?period=5d&interval=1d`).catch(() => null));
        const results = await Promise.all(promises);
        
        if (active) {
          const newData = results.map((res, i) => {
            if (res && res.data?.candles && res.data.candles.length >= 2) {
              const candles = res.data.candles;
              const latest = candles[candles.length - 1];
              const prev = candles[candles.length - 2];
              return {
                symbol: symbols[i],
                price: latest.close,
                change: ((latest.close - prev.close) / prev.close) * 100
              };
            }
            return null;
          }).filter(Boolean) as any;
          if (newData.length > 0) setTickerData(newData);
        }
      } catch (e) {
        console.error(e);
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 30000); // Update every 30s
    return () => { active = false; clearInterval(interval); };
  }, []);

  return (
    <header className="h-14 border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-4 sticky top-0 z-40">
      <div className="flex-1 flex items-center overflow-hidden">
        {/* Live Market Ticker */}
        <div className="flex items-center gap-4 animate-marquee whitespace-nowrap">
          {tickerData.length > 0 ? tickerData.map((t, idx) => (
            <div key={idx} className="flex items-center gap-1.5 text-xs font-semibold">
              <span className="text-muted-foreground">{t.symbol}</span>
              <span>₹{t.price.toFixed(2)}</span>
              <span className={t.change >= 0 ? "text-green-500" : "text-red-500"}>
                {t.change >= 0 ? "+" : ""}{t.change.toFixed(2)}%
              </span>
            </div>
          )) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-muted/40 border border-border/40">
              <Activity className="h-3.5 w-3.5 text-green-500 animate-pulse" />
              <span className="text-xs font-medium text-green-500">Market Live</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 flex justify-center">
        <SearchBar />
      </div>

      <div className="flex-1 flex justify-end items-center gap-3">
        <button className="relative p-2 rounded-full hover:bg-muted/50 text-muted-foreground transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-primary ring-2 ring-background"></span>
        </button>
      </div>
    </header>
  );
}
