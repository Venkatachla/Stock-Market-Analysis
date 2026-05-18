import React, { useCallback, useMemo, useState } from 'react';
import { usePolling } from '@/hooks/usePolling';
import { useQuery } from '@tanstack/react-query';
import { getPortfolio, getTransactions, getWallet, Transaction } from '@/services/api';
import { SignalBadge, MetricCard } from '@/components/common/StatusComponents';
import { PieChart, TrendingUp, TrendingDown, Wallet, Plus, Send } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import TradingModal from '@/components/TradingModal';
import WalletModal from '@/components/WalletModal';
import type { PortfolioHolding } from '@/services/api';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

const Portfolio: React.FC = () => {
  const { token } = useAuth();
  const [walletOpen, setWalletOpen] = useState(false);
  const [tradingOpen, setTradingOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState<{ symbol: string; price: number; quantity?: number } | null>(null);
  const [tradingMode, setTradingMode] = useState<'BUY' | 'SELL'>('BUY');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const pollPortfolio = useCallback(
    () => (token ? getPortfolio(token) : Promise.reject('No token')),
    [token]
  );
  const pollTransactions = useCallback(
    () => (token ? getTransactions(token, 10) : Promise.resolve([])),
    [token]
  );

  // 1. Fetch Portfolio (Includes holdings)
  const { data: portfolioData, retry: retryPortfolio } = usePolling(
    pollPortfolio,
    10000
  );

  // 2. Fetch Wallet Separately (Case A - Reliable Source of Truth)
  const { data: walletData } = useQuery({
    queryKey: ["wallet", token],
    queryFn: () => getWallet(token!),
    enabled: !!token,
    refetchInterval: 10000, // Sync with portfolio polling
  });

  const { data: transactionsData, retry: retryTransactions } = usePolling(
    pollTransactions,
    15000
  );

  // Use real portfolio data from backend
  const portfolio = portfolioData?.holdings ?? [];
  const transactions = transactionsData ?? [];

  // PART 3 - FINAL SOURCE OF TRUTH
  // Combine sources and handle string numbers (Case C)
  const rawWallet = walletData ?? portfolioData?.wallet ?? null;
  
  const wallet = useMemo(() => {
    if (!rawWallet) return null;
    return {
      total_balance: typeof rawWallet.total_balance === 'string' ? parseFloat(rawWallet.total_balance) : rawWallet.total_balance,
      available_balance: typeof rawWallet.available_balance === 'string' ? parseFloat(rawWallet.available_balance) : rawWallet.available_balance,
      used_balance: typeof rawWallet.used_balance === 'string' ? parseFloat(rawWallet.used_balance) : rawWallet.used_balance,
    };
  }, [rawWallet]);

  if (wallet && wallet.total_balance === 0 && (portfolio.length > 0)) {
    console.warn("Wallet values are zero - check backend");
  }

  const holdings = portfolioData?.holdings ?? [];
  const totalInvested = holdings.reduce((sum, h) => {
    const qty = Number(h.quantity ?? 0);
    const avg = Number(h.avgPrice ?? 0);
    return sum + qty * avg;
  }, 0);

  const totalValue = holdings.reduce((sum, h) => {
    const qty = Number(h.quantity ?? 0);
    const current = Number(h.currentPrice ?? 0);
    return sum + qty * current;
  }, 0);

  const totalPnl = totalValue - totalInvested;
  const totalPnlPercent = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;

  const allocationTotalValue = holdings.reduce((sum, h) => {
    const qty = Number(h.quantity ?? 0);
    const current = Number(h.currentPrice ?? h.current_price ?? 0) || Number(h.avgPrice ?? h.avg_price ?? 0);
    return sum + (qty * current);
  }, 0);

  const metrics = {
    totalValue,
    totalInvested,
    totalPnl,
    totalPnlPercent,
    total: wallet?.total_balance,
    available: wallet?.available_balance,
    used: wallet?.used_balance,
  };

  const handleBuy = (holding: PortfolioHolding | { symbol: string; price: number }) => {
    const price = 'price' in holding ? holding.price : (holding as PortfolioHolding).currentPrice;
    setSelectedStock({
      ...holding,
      symbol: holding.symbol,
      price: Number(price),
    });
    setTradingMode('BUY');
    setTradingOpen(true);
  };

  const handleSell = (holding: PortfolioHolding) => {
    setSelectedStock({
      ...holding,
      symbol: holding.symbol,
      price: Number(holding.currentPrice),
      quantity: Number(holding.quantity),
    });
    setTradingMode('SELL');
    setTradingOpen(true);
  };

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  // Handle trade completion by refreshing portfolio immediately
  const handleTradeComplete = (type: 'success' | 'error', message: string) => {
    showNotification(type, message);
    if (type === 'success') {
      // Immediately refresh portfolio data after successful trade
      setTimeout(() => {
        retryPortfolio();
        retryTransactions();
      }, 500);  // Small delay to ensure backend has persisted the transaction
    }
  };

  if (!token) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Please log in to view your portfolio</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notification */}
      {notification && (
        <div className={`p-4 rounded-lg border ${notification.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-300' : 'bg-red-500/10 border-red-500/20 text-red-300'}`}>
          {notification.message}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Portfolio</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your holdings and wallet</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setWalletOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
          >
            <Wallet className="h-4 w-4" />
            Wallet
          </button>
        </div>
      </div>

      {/* Wallet Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-lg border border-blue-500/20 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-300 text-sm">Total Balance</span>
            <Wallet className="h-4 w-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-blue-300">
            ₹{typeof metrics.total === "number" ? metrics.total.toFixed(2) : "--"}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Available: ₹{typeof metrics.available === "number" ? metrics.available.toFixed(2) : "--"}
          </p>
        </div>

        <MetricCard label="Portfolio Value" value={`₹${metrics.totalValue.toFixed(2)}`} icon={<PieChart className="h-4 w-4 text-primary" />} />
        <MetricCard
          label="Total P&L"
          value={`₹${metrics.totalPnl.toFixed(2)}`}
          change={`${metrics.totalPnlPercent.toFixed(2)}%`}
          positive={metrics.totalPnl >= 0}
          icon={metrics.totalPnl >= 0 ? <TrendingUp className="h-4 w-4 text-signal-buy" /> : <TrendingDown className="h-4 w-4 text-signal-sell" />}
        />
      </div>

      {/* Main Stats */}
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <MetricCard label="Invested" value={`₹${metrics.totalInvested.toFixed(2)}`} />
    <MetricCard label="Holdings" value={portfolio.length.toString()} />
    <MetricCard label="Used Balance" value={typeof metrics.used === "number" ? `₹${metrics.used.toFixed(2)}` : "--"} />
    <MetricCard label="Available" value={typeof metrics.available === "number" ? `₹${metrics.available.toFixed(2)}` : "--"} />
  </div>

      {/* Allocation visual */}
      {portfolio.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="font-semibold text-card-foreground mb-4">Allocation</h2>
          <div className="flex h-6 rounded-full overflow-hidden">
            {portfolio.map((h, i) => {
              const qty = Number(h.quantity ?? 0);
              const current = Number(h.currentPrice ?? h.current_price ?? 0) || Number(h.avgPrice ?? h.avg_price ?? 0);
              const stockValue = qty * current;
              const allocation = allocationTotalValue > 0 ? (stockValue / allocationTotalValue) * 100 : 0;
              const displayPercent = allocation > 0 ? `${allocation.toFixed(2)}%` : "0%";

              return (
                <div
                  key={h.symbol}
                  className="relative group"
                  style={{ width: `${allocation}%`, backgroundColor: COLORS[i % COLORS.length] }}
                  title={`${h.symbol}: ${displayPercent}`}
                >
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded text-xs font-medium bg-popover text-popover-foreground border border-border opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                    {h.symbol}: {displayPercent}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex flex-wrap gap-3 mt-3">
            {portfolio.map((h, i) => {
              const qty = Number(h.quantity ?? 0);
              const current = Number(h.currentPrice ?? h.current_price ?? 0) || Number(h.avgPrice ?? h.avg_price ?? 0);
              const stockValue = qty * current;
              const allocation = allocationTotalValue > 0 ? (stockValue / allocationTotalValue) * 100 : 0;
              const displayPercent = allocation > 0 ? `${allocation.toFixed(2)}%` : "0%";

              return (
                <div key={h.symbol} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  {h.symbol} ({displayPercent})
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Holdings Table */}
      {portfolio.length > 0 ? (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="font-semibold text-card-foreground">Holdings</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" role="table">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Stock</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">Qty</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">Avg Price</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">Current</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">P&L</th>
                  <th className="text-center px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">Signal</th>
                  <th className="text-center px-4 py-3 font-medium text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.map((h) => {
                  // Use fields from transformer
                  const avgPrice = h.avgPrice;
                  const currentPrice = h.currentPrice;
                  const pnl = h.pnl;
                  const pnlPercent = h.pnlPercent;
                  const quantity = h.quantity;
                  
                  return (
                    <tr key={h.symbol} className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors">
                      <td className="px-4 py-3">
                        <Link to={`/stock/${h.symbol}`} className="font-medium text-foreground hover:text-primary">
                          {h.symbol}
                        </Link>
                        <div className="text-xs text-muted-foreground">{h.name || 'N/A'}</div>
                      </td>
                      <td className="text-right px-4 py-3 font-mono hidden sm:table-cell">{quantity ?? 0}</td>
                      <td className="text-right px-4 py-3 font-mono hidden md:table-cell">
                        {typeof avgPrice === "number" ? `₹${avgPrice.toFixed(2)}` : "--"}
                      </td>
                      <td className="text-right px-4 py-3 font-mono">
                        {typeof currentPrice === "number" ? `₹${currentPrice.toFixed(2)}` : "--"}
                      </td>
                      <td className={`text-right px-4 py-3 font-mono ${(pnl ?? 0) >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
                        {typeof pnl === "number" ? `₹${pnl.toFixed(2)}` : "--"}
                        <div className="text-xs">{typeof pnlPercent === "number" ? `${pnlPercent.toFixed(2)}%` : "--"}</div>
                      </td>
                      <td className="text-center px-4 py-3 hidden lg:table-cell">
                        <SignalBadge signal={h.signal || 'NEUTRAL'} />
                      </td>
                      <td className="text-center px-4 py-3">
                        <div className="flex gap-2 justify-center">
                          <button
                            onClick={() => handleBuy(h)}
                            className="p-2 rounded bg-green-600/20 hover:bg-green-600/30 text-green-400 transition"
                            title="Buy"
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleSell(h)}
                            className="p-2 rounded bg-red-600/20 hover:bg-red-600/30 text-red-400 transition"
                            title="Sell"
                          >
                            <Send className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <PieChart className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
          <p className="text-muted-foreground">No holdings yet. Start trading to build your portfolio.</p>
          <button
            onClick={() => setWalletOpen(true)}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
          >
            Add Funds
          </button>
        </div>
      )}

      {/* Recent Transactions */}
      {transactions.length > 0 && (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="font-semibold text-card-foreground">Recent Transactions</h2>
          </div>
          <div className="divide-y divide-border">
            {transactions.map((t: Transaction) => (
              <div key={t.id} className="px-4 py-3 hover:bg-accent/30 transition flex items-center justify-between text-sm">
                <div className="flex-1">
                  <p className="font-medium text-foreground">{t.type} {t.symbol && `- ${t.symbol}`}</p>
                  <p className="text-xs text-muted-foreground">{new Date(t.created_at).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className={`font-medium ${t.type === 'BUY' || t.type === 'DEPOSIT' ? 'text-red-400' : 'text-green-400'}`}>
                    {t.type === 'BUY' || t.type === 'DEPOSIT' ? '-' : '+'} ₹{typeof t.total_amount === "number" ? t.total_amount.toFixed(2) : "0.00"}
                  </p>
                  <p className={`text-xs ${t.status === 'SUCCESS' ? 'text-green-500' : t.status === 'FAILED' ? 'text-red-500' : 'text-yellow-500'}`}>
                    {t.status}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modals */}
      <WalletModal
        isOpen={walletOpen}
        onClose={() => setWalletOpen(false)}
        token={token}
        onSuccess={(msg) => showNotification('success', msg)}
        onError={(msg) => showNotification('error', msg)}
        onWalletUpdate={() => {
          retryPortfolio();
        }}
      />

      {selectedStock && (
        <TradingModal
          key={`${selectedStock.symbol}-${selectedStock.price}-${tradingOpen}`}
          isOpen={tradingOpen}
          onClose={() => setTradingOpen(false)}
          symbol={selectedStock.symbol}
          currentPrice={Number(selectedStock.price)}
          mode={tradingMode}
          maxQuantity={selectedStock.quantity}
          token={token}
          onSuccess={(msg) => handleTradeComplete('success', msg)}
          onError={(msg) => handleTradeComplete('error', msg)}
        />
      )}
    </div>
  );
};

export default Portfolio;
