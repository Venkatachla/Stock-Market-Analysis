import { useEffect, useRef, useCallback, useState } from 'react';

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs = 30000
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const fetchData = useCallback(async () => {
    try {
      const result = await fetcher();
      setData(result);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  const retry = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
    timerRef.current = setInterval(fetchData, intervalMs);
    return () => clearInterval(timerRef.current);
  }, [fetchData, intervalMs]);

  return { data, loading, error, retry };
}
