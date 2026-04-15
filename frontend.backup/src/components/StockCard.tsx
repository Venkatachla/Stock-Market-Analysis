import { Link } from "react-router-dom";
import { Heart, Activity } from "lucide-react";
import { MiniCandlestick } from "./MiniCandlestick";
import { useBulkSignals } from "@/hooks/useBulkSignals";

interface StockCardProps {
  symbol: string;
  price: number;
  change: number;
  isWatchlisted: boolean;
  onToggleWatchlist: (e: React.MouseEvent, symbol: string) => void;
  initialSignal?: string;
  initialProb?: number;
}

export function StockCard({ symbol, price, change, isWatchlisted, onToggleWatchlist, initialSignal, initialProb }: StockCardProps) {
  const { signals } = useBulkSignals();

  const rSymbol = String(symbol || "");
  // Prefer provided values, fallback to bulk cache, display loading if neither
  const finalSignal = initialSignal || signals[rSymbol]?.signal;
  const finalProb = initialProb ?? (signals[rSymbol]?.prob ? signals[rSymbol].prob / 100 : undefined);

  const renderBadge = () => {
    if (!finalSignal) {
      return (
        <span className="inline-flex items-center gap-1 font-medium bg-muted/50 text-muted-foreground px-2 py-0.5 rounded text-[10px]">
          <Activity className="h-3 w-3 animate-pulse" />
          CALC
        </span>
      );
    }
    
    const p = finalProb ? (finalProb * 100).toFixed(0) : '--';
    const sig = String(finalSignal || "").toUpperCase();
    if (sig.includes("BUY")) {
       if ((finalProb && finalProb >= 0.65) || sig.includes("STRONG BUY") || sig.includes("VERY STRONG BUY")) {
         return (
            <span className="inline-flex items-center gap-1 font-bold bg-green-500/20 text-green-500 border border-green-500/40 px-2 py-0.5 rounded text-[10px] shadow-[0_0_10px_rgba(34,197,94,0.2)]">
              🟢 {sig.includes("VERY STRONG") ? "VERY STRONG BUY" : "STRONG BUY"} {p}%
            </span>
         );
       }
       return (
          <span className="inline-flex items-center gap-1 font-semibold bg-green-500/10 text-green-500 px-2 py-0.5 rounded text-[10px]">
            🟢 BUY {p}%
          </span>
       );
    }
    
    if (sig.includes("SELL")) {
      if (sig.includes("STRONG SELL") || sig.includes("VERY STRONG SELL")) {
        return (
          <span className="inline-flex items-center gap-1 font-bold bg-red-500/20 text-red-500 border border-red-500/40 px-2 py-0.5 rounded text-[10px] shadow-[0_0_10px_rgba(239,68,68,0.2)]">
            🔴 {sig.includes("VERY STRONG") ? "VERY STRONG SELL" : "STRONG SELL"} {p}%
          </span>
        );
      }
      return (
          <span className="inline-flex items-center gap-1 font-semibold bg-red-500/10 text-red-500 px-2 py-0.5 rounded text-[10px]">
            🔴 SELL {p}%
          </span>
      );
    }

    return (
        <span className="inline-flex items-center gap-1 font-medium bg-muted/50 text-muted-foreground px-2 py-0.5 rounded text-[10px]">
          ⚪ HOLD
        </span>
    );
  };

  return (
    <Link 
      to={`/stock/${rSymbol}`} 
      className="grid grid-cols-12 gap-2 md:gap-4 px-4 md:px-6 py-4 items-center hover:bg-muted/30 transition-colors group cursor-pointer"
    >
       <div className="col-span-5 md:col-span-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-muted border border-border/50 flex items-center justify-center text-sm font-bold shadow-inner">
            {rSymbol.substring(0, 1)}
          </div>
          <div>
            <div className="font-bold flex items-center gap-2">
              {rSymbol}
              <div className="hidden sm:block">{renderBadge()}</div>
            </div>
            <div className="text-xs text-muted-foreground">NSE Equity</div>
            <div className="sm:hidden mt-1">{renderBadge()}</div>
          </div>
       </div>
       
       <div className="col-span-4 md:col-span-3 text-right">
          <div className="font-mono font-semibold">₹{Number(price || 0).toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })}</div>
          <div className={`text-xs font-medium ${(Number(change) || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {(Number(change) || 0) >= 0 ? '+' : ''}{(Number(change) || 0).toFixed(2)}%
          </div>
       </div>

       <div className="hidden md:flex md:col-span-4 justify-center items-center h-10 px-2">
          {/* REPLACE SVG WITH REAL MINI CANDLESTICK */}
          <MiniCandlestick symbol={rSymbol} timeframe="1d" />
       </div>

       <div className="col-span-3 md:col-span-1 flex justify-end">
         <button onClick={(e) => onToggleWatchlist(e, symbol)} className="p-2 -mr-2 rounded-full hover:bg-muted text-muted-foreground hover:text-red-500 transition-colors">
           <Heart className="h-5 w-5" fill={isWatchlisted ? "#ef4444" : "none"} color={isWatchlisted ? "#ef4444" : "currentColor"} />
         </button>
       </div>
    </Link>
  );
}
