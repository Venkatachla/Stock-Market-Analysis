'use client';

import { Signal } from '@/types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SignalTableProps {
  signals: Signal[];
  loading?: boolean;
}

export function SignalTable({ signals, loading = false }: SignalTableProps) {
  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return <TrendingUp className="w-4 h-4 text-accent-green" />;
      case 'SELL':
        return <TrendingDown className="w-4 h-4 text-accent-red" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'BULL':
        return 'bg-green-500/10 text-accent-green';
      case 'BEAR':
        return 'bg-red-500/10 text-accent-red';
      default:
        return 'bg-gray-500/10 text-gray-400';
    }
  };

  return (
    <div className="w-full bg-trading-card border border-gray-700/50 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700/50 bg-gray-800/30">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Symbol</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Probability UP</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Sector</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Regime</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Signal</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  Loading signals...
                </td>
              </tr>
            ) : signals.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  No signals available
                </td>
              </tr>
            ) : (
              signals.map((signal, idx) => (
                <tr
                  key={idx}
                  className="border-b border-gray-700/30 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-semibold text-white">{signal.symbol}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-12 bg-gray-700 rounded-full h-1.5">
                        <div
                          className="bg-accent-green h-full rounded-full"
                          style={{ width: `${signal.prob_up * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-white">
                        {(signal.prob_up * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-300">{signal.sector}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getRegimeColor(signal.regime)}`}>
                      {signal.regime}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getSignalIcon(signal.signal_type)}
                      <span className="text-sm font-medium text-white">{signal.signal_type}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-accent-blue">
                      {(signal.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default SignalTable;
