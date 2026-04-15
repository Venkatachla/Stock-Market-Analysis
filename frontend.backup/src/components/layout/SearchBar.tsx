import { useState, useEffect, useRef } from "react";
import { Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface SearchResult {
  symbol: string;
  ticker: string;
}

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        document.getElementById("global-search")?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!query) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await axios.get(`${API_URL}/symbols/search`, { params: { q: query, limit: 8 } });
        if (Array.isArray(res.data)) {
          setResults(res.data);
          setIsOpen(true);
        }
      } catch (err) {
        console.error("Search failed", err);
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (symbol: string) => {
    setQuery("");
    setIsOpen(false);
    navigate(`/stock/${symbol}`);
  };

  return (
    <div className="relative w-full max-w-md mx-auto" ref={wrapperRef}>
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
        </div>
        <input
          id="global-search"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query && setIsOpen(true)}
          placeholder="Search markets (Ctrl+K)"
          className="block w-full pl-10 pr-3 py-2 border border-border/60 rounded-md leading-5 bg-card/50 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:bg-card sm:text-sm transition-all"
        />
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground font-mono">⌘K</span>
        </div>
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute z-50 mt-1 w-full bg-card/95 backdrop-blur shadow-lg rounded-md border border-border overflow-hidden">
          <ul className="max-h-60 overflow-auto py-1">
            {results.map((r) => (
              <li
                key={r.symbol}
                onClick={() => handleSelect(r.symbol)}
                className="px-4 py-2 hover:bg-muted/50 cursor-pointer flex justify-between items-center transition-colors"
              >
                <span className="font-semibold text-sm">{r.symbol}</span>
                <span className="text-xs text-muted-foreground">{r.ticker}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
