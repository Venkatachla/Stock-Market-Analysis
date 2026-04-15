import React from 'react';
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react';

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading...' }) => (
  <div className="flex flex-col items-center justify-center py-12 gap-3" role="status">
    <Loader2 className="h-8 w-8 animate-spin text-primary" />
    <p className="text-sm text-muted-foreground">{message}</p>
  </div>
);

export const ErrorState: React.FC<{ message: string; onRetry?: () => void }> = ({ message, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-12 gap-3 text-center" role="alert">
    <AlertCircle className="h-8 w-8 text-destructive" />
    <p className="text-sm text-muted-foreground">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <RefreshCw className="h-4 w-4" /> Retry
      </button>
    )}
  </div>
);

export const MetricCard: React.FC<{
  label: string;
  value: string;
  change?: string;
  positive?: boolean;
  icon?: React.ReactNode;
}> = React.memo(({ label, value, change, positive, icon }) => (
  <div className="rounded-lg border border-border bg-card p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</span>
      {icon}
    </div>
    <div className="text-2xl font-bold text-card-foreground">{value}</div>
    {change && (
      <span className={`text-xs font-medium ${positive ? 'text-signal-buy' : positive === false ? 'text-signal-sell' : 'text-muted-foreground'}`}>
        {change}
      </span>
    )}
  </div>
));

export const SignalBadge: React.FC<{ signal: 'BUY' | 'SELL' | 'NEUTRAL' }> = React.memo(({ signal }) => {
  const styles = {
    BUY: 'bg-signal-buy/15 text-signal-buy',
    SELL: 'bg-signal-sell/15 text-signal-sell',
    NEUTRAL: 'bg-muted text-muted-foreground',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${styles[signal]}`}>
      {signal}
    </span>
  );
});
