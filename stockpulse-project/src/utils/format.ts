export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 }).format(value);
}

export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

export function formatLargeNumber(value: number): string {
  if (value >= 1e7) return `${(value / 1e7).toFixed(2)} Cr`;
  if (value >= 1e5) return `${(value / 1e5).toFixed(2)} L`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)} K`;
  return value.toString();
}

export function getSignalColor(signal: 'BUY' | 'SELL' | 'NEUTRAL'): string {
  switch (signal) {
    case 'BUY': return 'text-signal-buy';
    case 'SELL': return 'text-signal-sell';
    default: return 'text-signal-neutral';
  }
}

export function getSignalBg(signal: 'BUY' | 'SELL' | 'NEUTRAL'): string {
  switch (signal) {
    case 'BUY': return 'bg-signal-buy/10 text-signal-buy border-signal-buy/20';
    case 'SELL': return 'bg-signal-sell/10 text-signal-sell border-signal-sell/20';
    default: return 'bg-signal-neutral/10 text-signal-neutral border-signal-neutral/20';
  }
}
