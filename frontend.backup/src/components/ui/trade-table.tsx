'use client';

import { PaperTrade } from '@/types';

interface TradeTableProps {
  trades: PaperTrade[];
  loading?: boolean;
}

export function TradeTable({ trades, loading = false }: TradeTableProps) {
  const getStatusColor = (status: string) => {
    return status === 'OPEN' ? 'text-yellow-400' : 'text-gray-400';
  };

  const getPnLColor = (pnl: number) => {
    return pnl > 0 ? 'text-accent-green' : pnl < 0 ? 'text-accent-red' : 'text-gray-400';
  };

  return (
    <div className="w-full bg-trading-card border border-gray-700/50 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700/50 bg-gray-800/30">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Symbol</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Entry Price</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Exit Price</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Qty</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">PnL</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Return %</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Entry Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                  Loading trades...
                </td>
              </tr>
            ) : trades.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                  No trades available
                </td>
              </tr>
            ) : (
              trades.map((trade, idx) => (
                <tr
                  key={idx}
                  className="border-b border-gray-700/30 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-semibold text-white">{trade.symbol}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">
                    ₹{trade.entry_price.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">
                    {trade.exit_price ? `₹${trade.exit_price.toFixed(2)}` : '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">{trade.quantity}</td>
                  <td className={`px-4 py-3 text-sm font-semibold ${getPnLColor(trade.pnl)}`}>
                    ₹{trade.pnl.toFixed(2)}
                  </td>
                  <td className={`px-4 py-3 text-sm font-semibold ${getPnLColor(trade.return_pct)}`}>
                    {trade.return_pct > 0 ? '+' : ''}{trade.return_pct.toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">{trade.entry_date}</td>
                  <td className={`px-4 py-3 text-sm font-semibold ${getStatusColor(trade.status)}`}>
                    {trade.status}
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

export default TradeTable;
