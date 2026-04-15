import { Search, Bell, Monitor } from "lucide-react";
import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const ADVANCED_MODE_KEY = "advanced_mode";
const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface SymbolSuggestion {
  symbol: string;
}

export function AppHeader() {
  const [searchValue, setSearchValue] = useState("");
  const [suggestions, setSuggestions] = useState<SymbolSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [advancedMode, setAdvancedMode] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const saved = localStorage.getItem(ADVANCED_MODE_KEY);
    setAdvancedMode(saved === "true");
  }, []);

  const toggleAdvancedMode = () => {
    const next = !advancedMode;
    setAdvancedMode(next);
    localStorage.setItem(ADVANCED_MODE_KEY, String(next));
    window.dispatchEvent(new Event("advanced-mode-changed"));
  };

  useEffect(() => {
    const q = searchValue.trim();
    if (!q) {
      setSuggestions([]);
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        const res = await axios.get(`${API_URL}/symbols/search`, { params: { q, limit: 8 } });
        const rows = Array.isArray(res.data) ? res.data : [];
        setSuggestions(rows.map((r: any) => ({ symbol: String(r.symbol || "").toUpperCase() })).filter((r: SymbolSuggestion) => !!r.symbol));
      } catch {
        setSuggestions([]);
      }
    }, 180);

    return () => window.clearTimeout(timer);
  }, [searchValue]);

  const goToSymbol = (raw: string) => {
    const symbol = String(raw || "").trim().toUpperCase();
    if (!symbol) return;
    navigate(`/chart/${encodeURIComponent(symbol)}`);
    setSearchValue("");
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const onEnter = () => {
    if (suggestions.length > 0) {
      goToSymbol(suggestions[0].symbol);
      return;
    }
    goToSymbol(searchValue);
  };

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-full max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search symbol..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => window.setTimeout(() => setShowSuggestions(false), 120)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onEnter();
            }}
            className="w-full h-8 pl-9 pr-3 text-sm bg-black border border-border rounded-md text-white placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-ring transition-colors"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-9 left-0 right-0 z-30 rounded-md border border-border/70 bg-card shadow-lg overflow-hidden">
              {suggestions.map((s) => (
                <button
                  key={s.symbol}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    goToSymbol(s.symbol);
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-accent/60"
                >
                  {s.symbol}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleAdvancedMode}
          className={`h-8 px-3 rounded-md text-xs font-semibold border transition-colors ${advancedMode ? "border-yellow-500/40 bg-yellow-500/15 text-yellow-300" : "border-border bg-accent/30 text-muted-foreground"}`}
        >
          Advanced: {advancedMode ? "ON" : "OFF"}
        </button>
        <div className="demo-banner">
          <Monitor className="h-3.5 w-3.5" />
          <span>Demo Mode</span>
        </div>
        <button className="h-8 w-8 rounded-md flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
          <Bell className="h-4 w-4" />
        </button>
        <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-semibold text-primary">
          ST
        </div>
      </div>
    </header>
  );
}