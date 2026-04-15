import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";
import { Zap, ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface IntradayIdea {
  symbol: string;
  close: number;
  momentumScore: number;
  timeframe: string;
}

export default function Intraday() {
  const [ideas, setIdeas] = useState<IntradayIdea[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        // Mock payload structure that matches typical alpha engines
        const res = await axios.get(`${API_URL}/trade-now/bull-stocks?limit=15`);
        if (res.data?.opportunities) {
          setIdeas(res.data.opportunities.map((o: any) => ({
            symbol: o.symbol,
            close: o.current_price || o.close,
            momentumScore: Math.round(o.predicted_prob * 100),
            timeframe: '15m'
          })));
        }
      } catch (err) {
        console.error("Intraday failed to load", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Zap className="h-8 w-8 text-primary" fill="currentColor"/> Intraday Alpha
          </h1>
          <p className="text-muted-foreground mt-2">Short-term velocity anomalies detected on 5m, 15m, and 1h compressions.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {loading ? (
             Array.from({ length: 8 }).map((_, i) => (
               <div key={i} className="h-32 bg-card/40 border border-border/40 animate-pulse rounded-xl" />
             ))
          ) : (
            ideas.map((idea) => (
              <Link
                key={`${idea.symbol}-${idea.timeframe}`}
                to={`/stock/${idea.symbol}?tf=${idea.timeframe}`}
                className="bg-card border border-border/60 hover:border-primary/50 transition-all rounded-xl p-5 flex flex-col group cursor-pointer relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-3 opacity-10 pointer-events-none">
                  <Zap className="h-16 w-16" fill="currentColor" />
                </div>
                <div className="flex justify-between items-start mb-4">
                  <h3 className="font-bold text-xl">{idea.symbol}</h3>
                  <span className="text-xs font-semibold px-2 py-1 bg-muted rounded-md flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {idea.timeframe}
                  </span>
                </div>
                <div className="mt-auto flex justify-between items-end">
                  <div>
                    <p className="text-sm text-muted-foreground">LTP</p>
                    <p className="font-mono text-lg font-semibold">₹{Number(idea.close || 0).toFixed(2)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Momentum</p>
                    <p className="font-mono text-lg font-bold text-green-500">{idea.momentumScore} / 100</p>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}
