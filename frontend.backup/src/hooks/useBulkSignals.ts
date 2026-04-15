import { useState, useCallback, useRef } from 'react';
import axios from 'axios';

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

export interface BulkSignal {
  signal: string;
  prob: number;
  action: string;
}

// Minimal global cache outside react state to avoid prop drilling in case components mount randomly
const globalSignalCache: Record<string, BulkSignal> = {};
let pendingSymbols = new Set<string>();
let currentTimeout: any = null;
let subscribers: (() => void)[] = [];

function notifySubscribers() {
  subscribers.forEach(fn => fn());
}

export function useBulkSignals() {
  // Using a forceRender trick with subscriber to update UI on global cache updates
  const [, forceRender] = useState({});
  const [, forceRegister] = useState(false);

  // Expose the getter
  const getSignal = (symbol: string) => globalSignalCache[symbol];

  const fetchSignals = useCallback(async (symbols: string[], timeframe: string = "1d") => {
    const toFetch = symbols.filter(s => !globalSignalCache[s] && !pendingSymbols.has(s));
    if (toFetch.length === 0) return;

    toFetch.forEach(s => pendingSymbols.add(s));

    if (currentTimeout) clearTimeout(currentTimeout);

    currentTimeout = setTimeout(async () => {
      const batch = Array.from(pendingSymbols);
      pendingSymbols.clear();
      if (batch.length === 0) return;

      try {
        const res = await axios.post(`${API_URL}/bulk_predict`, { symbols: batch, timeframe });
        Object.assign(globalSignalCache, res.data);
        notifySubscribers();
      } catch (err) {
        console.error('Failed to fetch bulk signals', err);
      }
    }, 50); // batch rapidly firing requests within 50ms (windowing)
  }, []);

  return { signals: globalSignalCache, fetchSignals, getSignal };
}
