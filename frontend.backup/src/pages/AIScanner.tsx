import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";
import { Rocket, RefreshCw, ChevronRight, Activity, TrendingUp, TrendingDown } from "lucide-react";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

const ScannerSection = ({ title, data, icon: Icon, typeClass }: any) => (
  <div className="bg-card border border-border/50 rounded-xl overflow-hidden shadow-sm">
    <div className="bg-muted/30 px-6 py-4 border-b border-border/50 flex items-center justify-between">
      <div className="flex items-center gap-2 font-bold text-lg">
        <Icon className={`h-5 w-5 ${typeClass}`} /> {title}
      </div>
      <span className="text-xs font-semibold bg-primary/10 text-primary px-2 py-1 rounded">Top 50</span>
    </div>
    <div className="p-0 overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-muted-foreground bg-muted/20 border-b border-border/50">
          <tr>
            <th className="px-6 py-3 font-medium">Symbol</th>
            <th className="px-6 py-3 font-medium">Underlying</th>
            <th className="px-6 py-3 font-medium">Model Prob %</th>
            <th className="px-6 py-3 font-medium text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/30">
          {data.map((item: any, i: number) => (
            <tr key={i} className="hover:bg-muted/20 transition-colors">
              <td className="px-6 py-3 font-bold flex flex-col">
                {item.symbol}
                {item.expiry && <span className="text-[10px] text-muted-foreground font-normal">Exp: {item.expiry}</span>}
              </td>
              <td className="px-6 py-3 text-muted-foreground">{item.underlying_symbol || item.name || "-"}</td>
              <td className="px-6 py-3 font-mono">
                <div className="flex items-center gap-2">
                   <div className="w-full bg-muted rounded-full h-1.5 max-w-[60px]">
                     <div className={`h-1.5 rounded-full ${item.prob > 65 ? 'bg-green-500' : 'bg-red-500'}`} style={{ width: `${item.prob}%` }}></div>
                   </div>
                   {item.prob}%
                </div>
              </td>
              <td className="px-6 py-3 text-right">
                <Link to={`/stock/${item.symbol}`} className="inline-flex items-center gap-1 text-xs font-semibold bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1.5 rounded transition-colors">
                  View Chart <ChevronRight className="h-3 w-3" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && <div className="p-6 text-center text-muted-foreground">No opportunities found matching criteria.</div>}
    </div>
  </div>
);

export default function AIScanner() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchResults = async () => {
    try {
      setRefreshing(true);
      const res = await axios.get(`${API_URL}/scanner_results`);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  return (
    <AppLayout>
      <div className="space-y-8 max-w-7xl mx-auto pb-24">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-primary/10 via-background to-background p-6 rounded-xl border border-primary/20">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Rocket className="h-8 w-8 text-primary" /> AI Universe Scanner 
              <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded font-black tracking-widest ml-2 animate-pulse">24/7 LIVE</span>
            </h1>
            <p className="text-muted-foreground text-sm mt-2 max-w-xl">
              Our ensemble model scans 294,000+ NSE equities, options (CE/PE), and futures continuously to surface extreme probability imbalances.
            </p>
          </div>
          <button 
            onClick={fetchResults}
            disabled={refreshing}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} /> 
            {refreshing ? "Scanning Universe..." : "Re-run Model on All"}
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center p-24 text-muted-foreground gap-4">
            <Activity className="h-8 w-8 animate-pulse text-primary" />
            <p>Processing 294k+ rows with prediction ensemble...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
             <ScannerSection title="Stocks to Buy (Strong)" data={data?.stocks_to_buy || []} icon={TrendingUp} typeClass="text-green-500" />
             <ScannerSection title="Stocks to Sell (Weak)" data={data?.stocks_to_sell || []} icon={TrendingDown} typeClass="text-red-500" />
             <ScannerSection title="Options Calls to Buy (CE)" data={data?.calls_to_buy || []} icon={Rocket} typeClass="text-green-400" />
             <ScannerSection title="Options Puts to Buy (PE)" data={data?.puts_to_buy || []} icon={TrendingDown} typeClass="text-red-400" />
          </div>
        )}
      </div>
    </AppLayout>
  );
}