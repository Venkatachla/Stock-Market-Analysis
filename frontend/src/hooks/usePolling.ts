import { useEffect, useRef, useCallback, useState } from 'react';

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs = 30000
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetcherRef = useRef(fetcher);
  const isMountedRef = useRef(true);
  const inFlightRef = useRef(false);

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchData = useCallback(async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    try {
      const result = await fetcherRef.current();
      if (!isMountedRef.current) return;
      setData(result);
      setError(null);
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      inFlightRef.current = false;
      if (!isMountedRef.current) return;
      setLoading(false);
    }
  }, []);

  const retry = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    void fetchData();
    const intervalId = setInterval(() => {
      void fetchData();
    }, intervalMs);

    return () => clearInterval(intervalId);
  }, [fetchData, intervalMs]);

  return { data, loading, error, retry };
}
