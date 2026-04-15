import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppLayout } from "@/components/AppLayout";
import { Bookmark, X } from "lucide-react";

export default function Watchlist() {
  const [symbols, setSymbols] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem("risk_os_watchlist");
    if (saved) {
      try {
        setSymbols(JSON.parse(saved));
      } catch (e) {}
    } else {
      setSymbols(["RELIANCE", "HDFCBANK", "INFY"]); // Defaults
    }
  }, []);

  const removeSymbol = (s: string) => {
    const next = symbols.filter(x => x !== s);
    setSymbols(next);
    localStorage.setItem("risk_os_watchlist", JSON.stringify(next));
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Bookmark className="h-8 w-8 text-primary" fill="currentColor"/> Watchlist
          </h1>
          <p className="text-muted-foreground mt-2">Your saved symbols stored locally.</p>
        </div>

        {symbols.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 border border-dashed border-border/50 rounded-xl bg-card/30">
            <Bookmark className="h-10 w-10 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No symbols saved.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {symbols.map(s => (
              <div key={s} className="bg-card border border-border/60 rounded-xl p-4 flex flex-col group relative">
                <button 
                  onClick={() => removeSymbol(s)} 
                  className="absolute top-3 right-3 text-muted-foreground hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="h-4 w-4" />
                </button>
                <h3 className="font-bold text-lg mb-2">{s}</h3>
                <Link to={`/stock/${s}`} className="mt-auto px-4 py-2 bg-muted text-sm font-medium rounded-lg text-center hover:bg-primary hover:text-primary-foreground transition-colors">
                  Analyze
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}