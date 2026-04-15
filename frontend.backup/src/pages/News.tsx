import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { Newspaper, RefreshCw } from "lucide-react";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface NewsItem {
  symbol?: string;
  title?: string;
  headline?: string;
  source?: string;
  published_at?: string;
  timestamp?: string;
  sentiment_score?: number;
  sentiment?: number;
  url?: string;
}

interface TradeRef {
  symbol?: string;
}

const sentimentLabel = (score: number): "Positive" | "Negative" | "Neutral" => {
  if (score > 0.2) return "Positive";
  if (score < -0.2) return "Negative";
  return "Neutral";
};

const sentimentClass = (score: number): string => {
  if (score > 0.2) return "bg-green-500/15 text-green-300 border border-green-500/30";
  if (score < -0.2) return "bg-red-500/15 text-red-300 border border-red-500/30";
  return "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30";
};

const News = () => {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [trackedSymbols, setTrackedSymbols] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchNews = async (manual = false) => {
    try {
      if (manual) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const [newsRes, tradesRes, signalsRes] = await Promise.all([
        axios.get(`${API_URL}/news`),
        axios.get(`${API_URL}/paper-trades`),
        axios.get(`${API_URL}/signals`),
      ]);

      const newsRows = Array.isArray(newsRes.data) ? newsRes.data : [];
      const tradeRows: TradeRef[] = Array.isArray(tradesRes.data) ? tradesRes.data : [];
      const signalRows: TradeRef[] = Array.isArray(signalsRes.data) ? signalsRes.data : signalsRes.data?.signals || [];

      const symbols = Array.from(new Set([...tradeRows, ...signalRows].map((row) => row.symbol).filter(Boolean) as string[]));

      setTrackedSymbols(symbols);
      setNewsItems(newsRows);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error fetching news:", error);
      setNewsItems([]);
      setTrackedSymbols([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews(false);
  }, []);

  const relevantNews = useMemo(() => {
    if (!trackedSymbols.length) return [];
    return newsItems.filter((item) => {
      const symbol = String(item.symbol ?? "").toUpperCase();
      return trackedSymbols.some((s) => s.toUpperCase() === symbol);
    });
  }, [newsItems, trackedSymbols]);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="flex items-center gap-2">
              <Newspaper className="h-5 w-5" />
              Trade-Relevant News
            </h1>
            <p className="text-sm text-muted-foreground mt-1">Only news for stocks you are trading</p>
            {lastUpdated && <p className="text-xs text-muted-foreground mt-1">Last updated: {lastUpdated}</p>}
          </div>
          <button
            onClick={() => fetchNews(true)}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium bg-accent/60 border border-border rounded-md hover:bg-accent disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        <div className="stat-card">
          <h3 className="text-sm font-semibold">Tracked Symbols</h3>
          <p className="text-xs text-muted-foreground mt-1">Used to filter relevant headlines for trade confirmation.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {trackedSymbols.map((symbol) => (
              <span key={symbol} className="badge-neutral">{symbol}</span>
            ))}
            {!trackedSymbols.length && <span className="text-sm text-muted-foreground">No tracked stocks yet.</span>}
          </div>
        </div>

        <div className="stat-card !p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-border/50">
            <h3 className="text-sm font-semibold">Relevant Headlines</h3>
          </div>
          {loading ? (
            <div className="px-4 py-8 text-center text-muted-foreground">Loading...</div>
          ) : relevantNews.length === 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground">No relevant stock news available right now.</div>
          ) : (
            <div className="divide-y divide-border/50">
              {relevantNews.map((item, idx) => {
                const score = item.sentiment_score ?? item.sentiment ?? 0;
                const label = sentimentLabel(score);
                return (
                  <div key={`${item.symbol}-${idx}`} className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="badge-neutral">{item.symbol}</span>
                      <span className={`text-xs px-2 py-1 rounded ${sentimentClass(score)}`}>{label}</span>
                      <span className="text-xs text-muted-foreground">{new Date(item.published_at ?? item.timestamp ?? Date.now()).toLocaleString()}</span>
                    </div>

                    {item.url ? (
                      <a href={item.url} target="_blank" rel="noreferrer" className="text-sm text-foreground hover:text-primary transition-colors">
                        {item.title ?? item.headline ?? "Untitled"}
                      </a>
                    ) : (
                      <p className="text-sm text-foreground">{item.title ?? item.headline ?? "Untitled"}</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">{item.source ?? "Unknown source"}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default News;
